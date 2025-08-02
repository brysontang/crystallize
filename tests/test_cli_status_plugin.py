import json
import math
import types
from pathlib import Path

from crystallize import data_source, pipeline_step
from crystallize.experiments.experiment import Experiment
from crystallize.experiments.experiment_graph import ExperimentGraph
from crystallize.experiments.treatment import Treatment
from crystallize.pipelines.pipeline import Pipeline

from cli.screens.run import _inject_status_plugin
from cli.status_plugin import CLIStatusPlugin
from cli.utils import estimate_experiment_time, estimate_experiment_time_from_yaml
from crystallize.utils import cache as cache_utils


events: list[tuple[str, dict[str, object]]] = []


def record(event: str, info: dict[str, object]) -> None:
    events.append((event, info))


@data_source
def ds(ctx):
    return 0


@pipeline_step()
def step_a(data, ctx):
    return data


@pipeline_step()
def step_b(data, ctx):
    return data


def test_cli_status_plugin_progress():
    events.clear()
    plugin = CLIStatusPlugin(record)
    treatment = Treatment("t", {})
    exp = Experiment(
        datasource=ds(),
        pipeline=Pipeline([step_a(), step_b()]),
        plugins=[plugin],
        treatments=[treatment],
        replicates=2,
    )
    exp.validate()
    exp.run(treatments=[treatment], replicates=2)

    assert events[0][0] == "start"
    assert any(evt == "replicate" for evt, _ in events)
    step_events = [info for evt, info in events if evt == "step_finished"]
    assert (
        len(step_events)
        == len(exp.pipeline.steps) * (len(exp.treatments) + 1) * exp.replicates
    )
    rep_events = [info for evt, info in events if evt == "replicate"]
    assert len(rep_events) == 4


def test_step_progress_eta(monkeypatch):
    events.clear()
    plugin = CLIStatusPlugin(record)

    @pipeline_step()
    def prog_step(data, ctx):
        emit = ctx.get("textual__emit")
        emit(ctx, 0.25)
        emit(ctx, 0.5)
        emit(ctx, 0.75)
        return data

    exp = Experiment(datasource=ds(), pipeline=Pipeline([prog_step()]), plugins=[plugin])
    exp.validate()

    import cli.status_plugin as status_plugin

    times = iter([0, 1, 2, 3, 4])
    monkeypatch.setattr(
        status_plugin, "time", types.SimpleNamespace(perf_counter=lambda: next(times))
    )

    exp.run()

    step_events = [info for evt, info in events if evt == "step"]
    assert math.isclose(step_events[1]["eta"], 2.0)
    assert math.isclose(step_events[2]["eta"], 1.0)


def test_inject_status_plugin_deduplicates_experiment():
    plugin = CLIStatusPlugin(lambda e, i: None)
    exp = Experiment(datasource=ds(), pipeline=Pipeline([step_a()]), plugins=[plugin])
    exp.validate()
    _inject_status_plugin(exp, lambda e, i: None)
    count = sum(isinstance(p, CLIStatusPlugin) for p in exp.plugins)
    assert count == 1


def test_inject_status_plugin_deduplicates_graph():
    plugin = CLIStatusPlugin(lambda e, i: None)
    exp = Experiment(
        datasource=ds(), pipeline=Pipeline([step_a()]), plugins=[plugin], name="e"
    )
    exp.validate()
    graph = ExperimentGraph.from_experiments([exp])
    _inject_status_plugin(graph, lambda e, i: None)
    exp2 = graph._graph.nodes["e"]["experiment"]
    count = sum(isinstance(p, CLIStatusPlugin) for p in exp2.plugins)
    assert count == 1


def test_status_plugin_records_times(tmp_path, monkeypatch):
    plugin = CLIStatusPlugin(lambda e, i: None)

    @pipeline_step(cacheable=True)
    def cached_step(data, ctx):
        return data

    exp = Experiment(
        datasource=ds(),
        pipeline=Pipeline([cached_step()]),
        plugins=[plugin],
        name="timed",
    )
    exp.validate()

    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.setattr(cache_utils, "CACHE_DIR", tmp_path / "cache")

    exp.run()
    step_name = cached_step().__class__.__name__
    path = tmp_path / ".cache" / "crystallize" / "steps" / "timed.json"
    data = json.loads(path.read_text())
    assert step_name in data and len(data[step_name]) == 1

    exp.run()  # second run uses cache
    data2 = json.loads(path.read_text())
    assert len(data2[step_name]) == 1

    eta = estimate_experiment_time(exp)
    assert eta >= data2[step_name][0]

    cfg = tmp_path / "config.yaml"
    cfg.write_text("name: timed\nsteps:\n  - cached_step\n")
    eta_yaml = estimate_experiment_time_from_yaml(cfg)
    assert eta_yaml >= data2[step_name][0]
