from pathlib import Path

import pytest
import yaml

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


def test_create_with_input_artifacts(tmp_path: Path) -> None:
    mapping = {"prev": "other#out"}
    path = create_experiment_scaffolding(
        "consumer",
        directory=tmp_path,
        steps=False,
        datasources=False,
        input_artifacts=mapping,
    )
    cfg = yaml.safe_load((path / "config.yaml").read_text())
    assert cfg["datasource"] == mapping
