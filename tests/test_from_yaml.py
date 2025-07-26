import yaml
from pathlib import Path

from crystallize.experiments.experiment import Experiment
from crystallize.experiments.experiment_graph import ExperimentGraph

from crystallize import data_source, pipeline_step, verifier


@data_source
def constant(ctx, value=1):
    return value


@pipeline_step()
def add_one(data, ctx):
    ctx.metrics.add("val", data + 1)
    ctx.artifacts.add("artifact.txt", b"data")
    return {"val": data + 1}


@verifier
def always_sig(baseline, treatment):
    return {"p_value": 0.01, "significant": True}


def create_exp(tmp, name="exp"):
    d = tmp / name
    d.mkdir()
    (d / "datasources.py").write_text("from test_from_yaml import constant\n")
    (d / "steps.py").write_text("from test_from_yaml import add_one\n")
    (d / "hypotheses.py").write_text("from test_from_yaml import always_sig\n")
    cfg = {
        "name": name,
        "datasource": {"x": "constant"},
        "steps": ["add_one"],
        "hypotheses": [{"name": "h", "verifier": "always_sig", "metrics": "val"}],
        "treatments": [{"name": "control"}],
        "outputs": {"artifact": {}},
    }
    (d / "config.yaml").write_text(yaml.safe_dump(cfg))
    return d


def test_experiment_from_yaml(tmp_path: Path):
    exp_dir = create_exp(tmp_path)
    exp = Experiment.from_yaml(exp_dir / "config.yaml")
    exp.validate()
    res = exp.run()
    assert res.metrics.baseline.metrics["val"] == [2]


def test_graph_from_yaml(tmp_path: Path):
    exp_dir = create_exp(tmp_path)
    graph = ExperimentGraph.from_yaml(tmp_path)
    res = graph.run()
    assert res[exp_dir.name].metrics.baseline.metrics["val"] == [2]


def test_from_yaml_relative(monkeypatch, tmp_path: Path):
    exp_dir = create_exp(tmp_path, name="rel")
    monkeypatch.chdir(tmp_path)
    exp = Experiment.from_yaml(exp_dir / "config.yaml")
    exp.validate()
    res = exp.run()
    assert res.metrics.baseline.metrics["val"] == [2]


def test_from_yaml_with_artifact(tmp_path: Path):
    prod_dir = create_exp(tmp_path, name="producer")
    prod = Experiment.from_yaml(prod_dir / "config.yaml")
    prod.validate()
    prod.run()

    cons = tmp_path / "consumer"
    cons.mkdir()
    (cons / "datasources.py").write_text(
        "from crystallize import data_source\n"
        "@data_source\n"
        "def dummy(ctx):\n    return 0\n"
    )
    (cons / "steps.py").write_text(
        "from crystallize import pipeline_step\n"
        "@pipeline_step()\n"
        "def passthrough(data, ctx):\n    ctx.metrics.add('val', 0)\n    return {'val': 0}\n"
    )
    cfg = {
        "name": "consumer",
        "datasource": {"prev": "producer#artifact"},
        "steps": ["passthrough"],
        "treatments": [],
        "hypotheses": [],
    }
    (cons / "config.yaml").write_text(yaml.safe_dump(cfg))

    graph = ExperimentGraph.from_yaml(tmp_path)
    res = graph.run()
    assert "consumer" in res
