from pathlib import Path

import pytest
import yaml

from crystallize import Artifact, data_source, pipeline_step, verifier
from crystallize.experiments.experiment import Experiment
from crystallize.experiments.experiment_graph import ExperimentGraph


@data_source
def constant(ctx):
    return 1


@pipeline_step()
def write_metric(data, ctx, dest: Artifact):
    ctx.metrics.add("val", data)
    dest.write(str(data).encode())
    return {"val": data}


@verifier
def ok_verifier(baseline, treatment):
    return {"p_value": 1.0}


def create_experiment_dir(base: Path, name: str, datasource_spec: dict[str, str]) -> Path:
    exp_dir = base / name
    exp_dir.mkdir()
    (exp_dir / "datasources.py").write_text("from test_validation_errors import constant\n")
    (exp_dir / "steps.py").write_text("from test_validation_errors import write_metric\n")

    cfg = {
        "name": name,
        "datasource": datasource_spec,
        "steps": [{"write_metric": {"dest": "artifact"}}],
        "treatments": {},
        "outputs": {"artifact": {}},
    }
    (exp_dir / "config.yaml").write_text(yaml.safe_dump(cfg))
    return exp_dir


def test_missing_datasource_section(tmp_path: Path) -> None:
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text(yaml.safe_dump({"name": "missing"}))

    with pytest.raises(ValueError, match="datasource"):
        Experiment.from_yaml(cfg_path)


def test_experiment_graph_cycle_detection(tmp_path: Path) -> None:
    root = tmp_path / "experiments"
    root.mkdir()
    create_experiment_dir(root, "a", {"input": "b#artifact"})
    create_experiment_dir(root, "b", {"input": "a#artifact"})

    with pytest.raises(ValueError, match="cycles"):
        ExperimentGraph.from_yaml(root / "a" / "config.yaml")


def test_unknown_verifier_reference(tmp_path: Path) -> None:
    exp_dir = tmp_path / "exp_verifier"
    exp_dir.mkdir()
    (exp_dir / "datasources.py").write_text("from test_validation_errors import constant\n")
    (exp_dir / "steps.py").write_text("from test_validation_errors import write_metric\n")
    (exp_dir / "verifiers.py").write_text(
        "from test_validation_errors import ok_verifier\n"
    )

    cfg = {
        "name": "exp_verifier",
        "datasource": {"x": "constant"},
        "steps": [{"write_metric": {"dest": "artifact"}}],
        "treatments": {},
        "outputs": {"artifact": {}},
        "hypotheses": [{"name": "h1", "verifier": "missing_verifier", "metrics": "val"}],
    }
    (exp_dir / "config.yaml").write_text(yaml.safe_dump(cfg))

    with pytest.raises(ValueError, match="missing_verifier"):
        Experiment.from_yaml(exp_dir / "config.yaml")
