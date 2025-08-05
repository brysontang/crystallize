from pathlib import Path

from crystallize import data_source, pipeline_step
from crystallize.experiments.experiment import Experiment
from crystallize.experiments.experiment_graph import ExperimentGraph
from crystallize.pipelines.pipeline import Pipeline
from crystallize.experiments.treatment import Treatment
from cli.status_plugin import CLIStatusPlugin
from cli.screens.run import _inject_status_plugin
from crystallize.utils.context import FrozenContext


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


def test_inject_status_plugin_deduplicates_experiment():
    plugin = CLIStatusPlugin(lambda e, i: None)
    exp = Experiment(datasource=ds(), pipeline=Pipeline([step_a()]), plugins=[plugin])
    exp.validate()
    _inject_status_plugin(exp, lambda e, i: None, writer=None)
    count = sum(isinstance(p, CLIStatusPlugin) for p in exp.plugins)
    assert count == 1


def test_inject_status_plugin_deduplicates_graph():
    plugin = CLIStatusPlugin(lambda e, i: None)
    exp = Experiment(
        datasource=ds(), pipeline=Pipeline([step_a()]), plugins=[plugin], name="e"
    )
    exp.validate()
    graph = ExperimentGraph.from_experiments([exp])
    _inject_status_plugin(graph, lambda e, i: None, writer=None)
    exp2 = graph._graph.nodes["e"]["experiment"]
    count = sum(isinstance(p, CLIStatusPlugin) for p in exp2.plugins)
    assert count == 1


def test_before_step_emits_initial_progress() -> None:
    events.clear()
    plugin = CLIStatusPlugin(record)
    exp = Experiment(datasource=ds(), pipeline=Pipeline([step_a()]), plugins=[plugin])
    exp.validate()
    ctx = FrozenContext({})
    plugin.before_replicate(exp, ctx)
    plugin.before_step(exp, exp.pipeline.steps[0])
    assert (
        "step",
        {"step": exp.pipeline.steps[0].__class__.__name__, "percent": 0.0},
    ) in events


def test_after_run_creates_nested_history(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    plugin = CLIStatusPlugin(lambda e, i: None)
    exp = Experiment(
        datasource=ds(),
        pipeline=Pipeline([step_a()]),
        plugins=[plugin],
        name="exp/test",
    )
    exp.validate()
    exp.run()
    hist = tmp_path / ".cache" / "crystallize" / "steps" / "exp" / "test.json"
    assert hist.exists()
