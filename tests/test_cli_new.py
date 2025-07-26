import asyncio
from pathlib import Path

from cli.discovery import _run_object, discover_objects
from crystallize import data_source, pipeline_step
from crystallize.experiments.experiment import Experiment
from crystallize.experiments.experiment_graph import ExperimentGraph
from crystallize.pipelines.pipeline import Pipeline


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


def test_discover_objects(tmp_path: Path):
    create_module(tmp_path)
    exps, _ = discover_objects(tmp_path, Experiment)
    graphs, _ = discover_objects(tmp_path, ExperimentGraph)
    assert any(isinstance(o, Experiment) for o in exps.values())
    assert any(isinstance(o, ExperimentGraph) for o in graphs.values())


def test_run_object_override_replicates():
    exp = Experiment(datasource=dummy_source(), pipeline=Pipeline([add_one()]))
    exp.validate()
    result = asyncio.run(_run_object(exp, "rerun", replicates=2))
    assert result.metrics.baseline.metrics["val"] == [1]
