import asyncio
from pathlib import Path
from typing import Any

import pytest

from cli.discovery import _import_module, _run_object, discover_objects
from cli.utils import (
    _build_experiment_table,
    _build_hypothesis_tables,
    _write_experiment_summary,
    _write_summary,
    filter_mapping,
)
from crystallize import data_source, pipeline_step
from crystallize.experiments.experiment import Experiment
from crystallize.experiments.experiment_graph import ExperimentGraph
from crystallize.experiments.result import Result
from crystallize.experiments.result_structs import (
    ExperimentMetrics,
    TreatmentMetrics,
    HypothesisResult,
)
from crystallize.pipelines.pipeline import Pipeline


class FakeLog:
    def __init__(self) -> None:
        self.written: list[Any] = []

    def write(self, message: Any) -> None:
        self.written.append(message)


@data_source
def dummy_source(ctx):
    return ctx.get("replicate", 0)


@pipeline_step()
def add_one(data, ctx):
    ctx.metrics.add("val", data + 1)
    return {"val": data + 1}


def create_module(tmp: Path) -> Path:
    content = (
        "from crystallize import Experiment, ExperimentGraph, Pipeline, data_source, pipeline_step\n"
        "@data_source\n"
        "def ds(ctx):\n    return 0\n"
        "@pipeline_step()\n"
        "def step(data, ctx):\n    return data\n"
        "\nexp = Experiment(datasource=ds(), pipeline=Pipeline([step()]), name='e')\n"
        "exp.validate()\n"
        "graph = ExperimentGraph.from_experiments([exp])\n"
    )
    mod = tmp / "m.py"
    mod.write_text(content)
    return mod


def make_result() -> Result:
    metrics = ExperimentMetrics(
        baseline=TreatmentMetrics({"m": [0]}),
        treatments={"t": TreatmentMetrics({"m": [1]})},
        hypotheses=[],
    )
    return Result(metrics=metrics, errors={})


def make_hyp_result() -> Result:
    metrics = ExperimentMetrics(
        baseline=TreatmentMetrics({"m": [0]}),
        treatments={"t": TreatmentMetrics({"m": [1]})},
        hypotheses=[
            HypothesisResult(
                name="h",
                results={"t": {"p_value": 0.1, "significant": False}},
                ranking={"best": "t"},
            )
        ],
    )
    return Result(metrics=metrics, errors={})


def test_import_module_relative(tmp_path: Path):
    mod = tmp_path / "mod.py"
    mod.write_text("X = 1")
    m, err = _import_module(mod, tmp_path)
    assert m is not None and getattr(m, "X") == 1 and err is None


def test_import_module_invalid(tmp_path: Path):
    bad = tmp_path / "bad.py"
    bad.write_text("def broken(")
    mod, err = _import_module(bad, tmp_path)
    assert mod is None


def test_import_module_absolute(tmp_path: Path):
    mod = tmp_path / "abs.py"
    mod.write_text("X = 2")
    m, err = _import_module(mod, Path.cwd())
    assert m is not None and getattr(m, "X") == 2 and err is None


def test_import_module_runtime_error(tmp_path: Path):
    bad = tmp_path / "bad.py"
    bad.write_text("raise ValueError('boom')")
    mod, err = _import_module(bad, Path.cwd())
    assert mod is None


def test_discover_objects_skips_invalid(tmp_path: Path):
    create_module(tmp_path)
    bad = tmp_path / "bad.py"
    bad.write_text("def broken(")
    exps, errors = discover_objects(tmp_path, Experiment)
    assert len(exps) == 1


def test_discover_objects_nested(tmp_path: Path):
    pkg = tmp_path / "pkg"
    sub = pkg / "sub"
    sub.mkdir(parents=True)

    mod1 = create_module(pkg)
    mod2 = create_module(sub)

    objs, _ = discover_objects(pkg, ExperimentGraph)
    keys = {Path(k.split(":")[0]) for k in objs}
    assert mod1 in keys and mod2 in keys


def test_run_object_graph_override_replicates():
    exp = Experiment(
        datasource=dummy_source(), pipeline=Pipeline([add_one()]), name="e"
    )
    exp.validate()
    graph = ExperimentGraph.from_experiments([exp])
    results = asyncio.run(_run_object(graph, "rerun", replicates=2))
    assert results["e"].metrics.baseline.metrics["val"] == [1, 2]


def test_run_object_experiment_single():
    exp = Experiment(datasource=dummy_source(), pipeline=Pipeline([add_one()]))
    exp.validate()
    result = asyncio.run(_run_object(exp, "rerun", replicates=2))
    assert result.metrics.baseline.metrics["val"] == [1]


def test_run_object_error_bubbles():
    class BoomExperiment(Experiment):
        async def arun(self, *args: Any, **kwargs: Any) -> Any:  # type: ignore[override]
            raise RuntimeError("boom")

    exp = BoomExperiment(datasource=dummy_source(), pipeline=Pipeline([add_one()]))
    exp.validate()
    with pytest.raises(RuntimeError):
        asyncio.run(_run_object(exp, "rerun", replicates=1))


def test_build_experiment_table():
    table = _build_experiment_table(make_result())
    assert table is not None
    assert list(table.columns[0].cells) == ["m"]
    assert list(table.columns[1].cells) == ["[0]"]
    assert list(table.columns[2].cells) == ["[1]"]


def test_build_experiment_table_multiple_metrics():
    metrics = ExperimentMetrics(
        baseline=TreatmentMetrics({"a": [1], "b": [2]}),
        treatments={
            "t1": TreatmentMetrics({"a": [3], "c": [4]}),
            "t2": TreatmentMetrics({"b": [5]}),
        },
        hypotheses=[],
    )
    table = _build_experiment_table(Result(metrics=metrics, errors={}))
    assert table is not None
    assert [c.header for c in table.columns] == ["Metric", "Baseline", "t1", "t2"]
    rows = [[cell for cell in col.cells] for col in table.columns]
    assert rows[0] == ["a", "b", "c"]
    assert rows[1] == ["[1]", "[2]", "None"]
    assert rows[2] == ["[3]", "None", "[4]"]
    assert rows[3] == ["None", "[5]", "None"]


def test_build_experiment_table_no_metrics():
    metrics = ExperimentMetrics(
        baseline=TreatmentMetrics({}), treatments={}, hypotheses=[]
    )
    result = Result(metrics=metrics, errors={})
    assert _build_experiment_table(result) is None


def test_build_hypothesis_tables():
    res = make_hyp_result()
    tables = _build_hypothesis_tables(res)
    assert len(tables) == 1
    assert tables[0].title.startswith("Hypothesis: h")


def test_write_experiment_summary_with_errors():
    res = make_result()
    res.errors = {"base": RuntimeError("fail")}
    log = FakeLog()
    _write_experiment_summary(log, res)
    assert any(isinstance(m, type(_build_experiment_table(res))) for m in log.written)
    assert any("Errors occurred" in str(m) for m in log.written)
    assert any("base:" in str(m) for m in log.written)


def test_write_experiment_summary_errors_only():
    metrics = ExperimentMetrics(
        baseline=TreatmentMetrics({}), treatments={}, hypotheses=[]
    )
    res = Result(metrics=metrics, errors={"boom": RuntimeError("fail")})
    log = FakeLog()
    _write_experiment_summary(log, res)
    assert not any(hasattr(m, "columns") for m in log.written)
    assert any("Errors occurred" in str(m) for m in log.written)


def test_write_experiment_summary_with_hypotheses():
    res = make_hyp_result()
    log = FakeLog()
    _write_experiment_summary(log, res)
    titles = [getattr(m, "title", "") for m in log.written if hasattr(m, "title")]
    assert "Metrics" in titles
    assert any(isinstance(t, str) and t.startswith("Hypothesis: h") for t in titles)


def test_write_experiment_summary_with_artifacts(tmp_path: Path):
    res = make_result()
    base = tmp_path / "baseline" / "out.txt"
    base.parent.mkdir(parents=True, exist_ok=True)
    base.write_text("a")
    treat = tmp_path / "t" / "out.txt"
    treat.parent.mkdir(parents=True, exist_ok=True)
    treat.write_text("b")
    res.artifacts = {"out.txt": {"baseline": base, "t": treat}}
    log = FakeLog()
    _write_experiment_summary(log, res)
    tables = [m for m in log.written if hasattr(m, "title")]
    art = next((t for t in tables if getattr(t, "title", "") == "Artifacts"), None)
    assert art is not None
    from rich.console import Console

    console = Console(record=True)
    console.print(art)
    out = console.export_text()
    assert "Artifacts" in out and "out.txt" in out


def test_write_summary_single_result():
    res = make_result()
    log = FakeLog()
    _write_summary(log, res)
    assert any(hasattr(m, "columns") for m in log.written)
    assert not any(str(m) == "exp" for m in log.written)


def test_write_summary_nested_dicts():
    res1 = make_result()
    res2 = make_result()
    log = FakeLog()
    _write_summary(log, {"e1": res1, "e2": res2})
    heads = [str(m) for m in log.written if "Errors" not in str(m)]
    assert any("e1" in h for h in heads)
    assert any("e2" in h for h in heads)


def test_write_summary_dict():
    res = make_result()
    log = FakeLog()
    _write_summary(log, {"exp": res})
    assert any(str(m) == "exp" for m in log.written if not hasattr(m, "columns"))
    assert any(hasattr(m, "columns") for m in log.written)


def test_filter_mapping():
    data = {"ExpOne": 1, "Another": 2, "expTwo": 3}
    assert filter_mapping(data, "exp") == {"ExpOne": 1, "expTwo": 3}
