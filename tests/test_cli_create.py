from pathlib import Path
import yaml
import pytest

from cli.utils import create_experiment_scaffolding


def test_create_basic(tmp_path: Path) -> None:
    path = create_experiment_scaffolding("exp", directory=tmp_path)
    assert (path / "steps.py").exists()
    assert (path / "datasources.py").exists()
    cfg = yaml.safe_load((path / "config.yaml").read_text())
    assert cfg["name"] == "exp"
    assert cfg["steps"] == []
    assert cfg["datasource"] == {}


def test_create_with_examples(tmp_path: Path) -> None:
    path = create_experiment_scaffolding("demo", directory=tmp_path, examples=True)
    cfg = yaml.safe_load((path / "config.yaml").read_text())
    assert cfg["steps"] == ["add_one"]
    assert cfg["datasource"] == {"numbers": "numbers"}


def test_create_invalid_name(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        create_experiment_scaffolding("Bad Name", directory=tmp_path)


def test_create_with_artifact_inputs(tmp_path: Path) -> None:
    # upstream experiment providing an output
    up_path = create_experiment_scaffolding("up", directory=tmp_path, outputs=True)
    cfg = yaml.safe_load((up_path / "config.yaml").read_text())
    assert "outputs" in cfg

    # downstream experiment referencing the upstream output
    down = create_experiment_scaffolding(
        "down",
        directory=tmp_path,
        artifact_inputs={"up_out": "up#out"},
    )
    down_cfg = yaml.safe_load((down / "config.yaml").read_text())
    assert down_cfg["datasource"] == {"up_out": "up#out"}

