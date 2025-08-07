import yaml
from pathlib import Path
import pytest

from crystallize.experiments.experiment import Experiment
from crystallize.experiments.experiment_graph import ExperimentGraph
from crystallize.plugins.plugins import ArtifactPlugin

from crystallize import data_source, pipeline_step, verifier, Artifact


@data_source
def constant(ctx, value=1):
    return value


@pipeline_step()
def add_one(data, ctx):
    ctx.metrics.add("val", data + 1)
    ctx.artifacts.add("artifact.txt", b"data")
    return {"val": data + 1}


@pipeline_step()
def add_one_out(data, ctx, dest: Artifact):
    dest.write(b"data")
    ctx.metrics.add("val", data + 1)
    return {"val": data + 1}


@pipeline_step()
def write_out(data, ctx, dest: Artifact):
    dest.write(str(data).encode())
    ctx.metrics.add("val", data)
    return data


@verifier
def always_sig(baseline, treatment):
    return {"p_value": 0.01, "significant": True}


def create_exp(tmp, name="exp"):
    d = tmp / name
    d.mkdir()
    (d / "datasources.py").write_text("from test_from_yaml import constant\n")
    (d / "steps.py").write_text("from test_from_yaml import add_one_out\n")
    (d / "verifiers.py").write_text("from test_from_yaml import always_sig\n")
    cfg = {
        "name": name,
        "datasource": {"x": "constant"},
        "steps": [{"add_one_out": {"dest": "artifact"}}],
        "hypotheses": [{"name": "h", "verifier": "always_sig", "metrics": "val"}],
        "treatments": {"control": {}},
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
    graph = ExperimentGraph.from_yaml(exp_dir / "config.yaml")
    res = graph.run()
    assert res[exp_dir.name].metrics.baseline.metrics["val"] == [2]


def test_graph_from_yaml_directory(tmp_path: Path):
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
        "treatments": {},
        "hypotheses": [],
    }
    (cons / "config.yaml").write_text(yaml.safe_dump(cfg))

    graph = ExperimentGraph.from_yaml(tmp_path)
    res = graph.run()
    assert "consumer" in res


def test_from_yaml_output_alias_mapping(tmp_path: Path):
    exp_dir = tmp_path / "exp_alias"
    exp_dir.mkdir()
    (exp_dir / "datasources.py").write_text("from test_from_yaml import constant\n")
    (exp_dir / "steps.py").write_text("from test_from_yaml import write_out\n")

    cfg = {
        "name": "exp_alias",
        "datasource": {"x": "constant"},
        "steps": [{"write_out": {"dest": "result"}}],
        "treatments": {"control": {}},
        "hypotheses": [],
        "outputs": {"result": {"file_name": "out.txt"}},
    }
    (exp_dir / "config.yaml").write_text(yaml.safe_dump(cfg))

    plugin = ArtifactPlugin(root_dir=str(tmp_path / "arts"))
    exp = Experiment.from_yaml(exp_dir / "config.yaml")
    exp.plugins = [plugin]
    exp.validate()
    exp.run()

    step_dir = "Write_OutStep"
    out_path = (
        tmp_path
        / "arts"
        / "exp_alias"
        / "v0"
        / "replicate_0"
        / "baseline"
        / step_dir
        / "out.txt"
    )
    assert out_path.read_text() == "1"


def test_from_yaml_output_default_mapping(tmp_path: Path):
    exp_dir = tmp_path / "exp_default"
    exp_dir.mkdir()
    (exp_dir / "datasources.py").write_text("from test_from_yaml import constant\n")
    (exp_dir / "steps.py").write_text("from test_from_yaml import write_out\n")

    cfg = {
        "name": "exp_default",
        "datasource": {"x": "constant"},
        "steps": ["write_out"],
        "treatments": {"control": {}},
        "hypotheses": [],
        "outputs": {"dest": {"file_name": "out.txt"}},
    }
    (exp_dir / "config.yaml").write_text(yaml.safe_dump(cfg))

    plugin = ArtifactPlugin(root_dir=str(tmp_path / "arts"))
    exp = Experiment.from_yaml(exp_dir / "config.yaml")
    exp.plugins = [plugin]
    exp.validate()
    exp.run()

    step_dir = "Write_OutStep"
    out_path = (
        tmp_path
        / "arts"
        / "exp_default"
        / "v0"
        / "replicate_0"
        / "baseline"
        / step_dir
        / "out.txt"
    )
    assert out_path.read_text() == "1"


def test_from_yaml_multiple_outputs(tmp_path: Path):
    exp_dir = tmp_path / "exp_multi"
    exp_dir.mkdir()
    (exp_dir / "datasources.py").write_text("from test_from_yaml import constant\n")
    (exp_dir / "steps.py").write_text("from test_from_yaml import write_out\n")

    cfg = {
        "name": "exp_multi",
        "datasource": {"x": "constant"},
        "steps": [
            {"write_out": {"dest": "results1"}},
            {"write_out": {"dest": "results2"}},
        ],
        "treatments": {"control": {}},
        "hypotheses": [],
        "outputs": {
            "results1": {"file_name": "out1.txt"},
            "results2": {"file_name": "out2.txt"},
        },
    }
    (exp_dir / "config.yaml").write_text(yaml.safe_dump(cfg))

    plugin = ArtifactPlugin(root_dir=str(tmp_path / "arts"))
    exp = Experiment.from_yaml(exp_dir / "config.yaml")
    exp.plugins = [plugin]
    exp.validate()
    exp.run()

    step_dir = "Write_OutStep"
    out1 = (
        tmp_path
        / "arts"
        / "exp_multi"
        / "v0"
        / "replicate_0"
        / "baseline"
        / step_dir
        / "out1.txt"
    )
    out2 = (
        tmp_path
        / "arts"
        / "exp_multi"
        / "v0"
        / "replicate_0"
        / "baseline"
        / step_dir
        / "out2.txt"
    )
    assert out1.read_text() == "1"
    assert out2.read_text() == "1"


def test_from_yaml_unknown_output(tmp_path: Path):
    exp_dir = tmp_path / "exp_bad_alias"
    exp_dir.mkdir()
    (exp_dir / "datasources.py").write_text("from test_from_yaml import constant\n")
    (exp_dir / "steps.py").write_text("from test_from_yaml import write_out\n")

    cfg = {
        "name": "exp_bad_alias",
        "datasource": {"x": "constant"},
        "steps": [{"write_out": {"dest": "missing"}}],
        "treatments": {"control": {}},
        "hypotheses": [],
        "outputs": {"result": {"file_name": "out.txt"}},
    }
    (exp_dir / "config.yaml").write_text(yaml.safe_dump(cfg))

    with pytest.raises(ValueError, match="missing"):
        Experiment.from_yaml(exp_dir / "config.yaml")


def test_from_yaml_unused_output(tmp_path: Path):
    exp_dir = tmp_path / "exp_unused"
    exp_dir.mkdir()
    (exp_dir / "datasources.py").write_text("from test_from_yaml import constant\n")
    (exp_dir / "steps.py").write_text("from test_from_yaml import write_out\n")

    cfg = {
        "name": "exp_unused",
        "datasource": {"x": "constant"},
        "steps": [{"write_out": {"dest": "result"}}],
        "treatments": {"control": {}},
        "hypotheses": [],
        "outputs": {
            "result": {"file_name": "out.txt"},
            "unused": {"file_name": "unused.txt"},
        },
    }
    (exp_dir / "config.yaml").write_text(yaml.safe_dump(cfg))

    with pytest.raises(ValueError, match="unused"):
        Experiment.from_yaml(exp_dir / "config.yaml")


def test_graph_from_yaml_recursive(tmp_path: Path):
    root = tmp_path / "experiments"
    root.mkdir()

    prod_dir = create_exp(root, name="producer")
    prod = Experiment.from_yaml(prod_dir / "config.yaml")
    prod.validate()
    prod.run()

    cons = root / "consumer"
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
        "treatments": {},
        "hypotheses": [],
    }
    (cons / "config.yaml").write_text(yaml.safe_dump(cfg))

    graph = ExperimentGraph.from_yaml(cons / "config.yaml")
    res = graph.run()
    assert "consumer" in res


def test_graph_from_yaml_missing(tmp_path: Path):
    d = tmp_path / "final"
    d.mkdir()
    (d / "datasources.py").write_text(
        "from crystallize import data_source\n"
        "@data_source\n"
        "def dummy(ctx):\n    return 0\n"
    )
    (d / "steps.py").write_text(
        "from crystallize import pipeline_step\n"
        "@pipeline_step()\n"
        "def passthrough(data, ctx):\n    ctx.metrics.add('val', 0)\n    return {'val': 0}\n"
    )
    cfg = {
        "name": "final",
        "datasource": {"prev": "missing#artifact"},
        "steps": ["passthrough"],
        "treatments": {},
        "hypotheses": [],
    }
    (d / "config.yaml").write_text(yaml.safe_dump(cfg))

    with pytest.raises(FileNotFoundError):
        ExperimentGraph.from_yaml(d / "config.yaml")
