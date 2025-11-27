from pathlib import Path

import yaml

from cli.discovery import discover_configs
from cli.utils import update_replicates


def test_yaml_discovery(tmp_path: Path) -> None:
    exp_dir = tmp_path / "exp"
    exp_dir.mkdir()
    cfg1 = {
        "name": "exp",
        "datasource": {"n": "numbers"},
        "cli": {"group": "Data", "priority": 1, "icon": "X", "color": "#111111"},
        "replicates": 5,
    }
    (exp_dir / "config.yaml").write_text(yaml.safe_dump(cfg1))

    graph_dir = tmp_path / "graph"
    graph_dir.mkdir()
    cfg2 = {
        "name": "graph",
        "datasource": {"data": "exp#out"},
        "cli": {"hidden": True},
    }
    (graph_dir / "config.yaml").write_text(yaml.safe_dump(cfg2))

    other = tmp_path / "other"
    other.mkdir()
    cfg3 = {"name": "other", "datasource": {"n": "numbers"}}
    (other / "config.yaml").write_text(yaml.safe_dump(cfg3))

    graphs, experiments, errors = discover_configs(tmp_path)

    graph_paths = {info["path"] for info in graphs.values()}
    exp_paths = {info["path"] for info in experiments.values()}

    assert (graph_dir / "config.yaml") not in graph_paths
    assert (exp_dir / "config.yaml") in exp_paths
    assert (other / "config.yaml") in exp_paths
    info_key = next(
        k for k, v in experiments.items() if v["path"] == exp_dir / "config.yaml"
    )
    info = experiments[info_key]
    assert info["cli"]["group"] == "Data"
    assert info["cli"]["priority"] == 1
    assert info["cli"]["icon"] == "X"
    assert info["cli"]["color"] == "#111111"
    assert info["replicates"] == 5
    default_key = next(
        k for k, v in experiments.items() if v["path"] == other / "config.yaml"
    )
    default_info = experiments[default_key]
    assert default_info["cli"]["group"] == "Experiments"
    assert default_info["cli"]["icon"] == "🧪"
    assert default_info["replicates"] == 1
    assert not errors


def test_update_replicates(tmp_path: Path) -> None:
    cfg = tmp_path / "config.yaml"
    with cfg.open("w") as f:
        yaml.safe_dump({"name": "e", "datasource": {"n": "numbers"}}, f)

    update_replicates(cfg, 7)

    with cfg.open() as f:
        data = yaml.safe_load(f)

    assert data["replicates"] == 7


def test_yaml_discovery_requires_extras(monkeypatch, tmp_path: Path) -> None:
    exp_dir = tmp_path / "exp"
    exp_dir.mkdir()
    cfg = {
        "name": "exp",
        "datasource": {"n": "numbers"},
        "steps": ["crystallize_extras.fake_step"],
    }
    (exp_dir / "config.yaml").write_text(yaml.safe_dump(cfg))

    import cli.discovery as discovery

    def fake_import(name):
        if name.startswith("crystallize_extras"):
            raise ModuleNotFoundError("No module named 'crystallize_extras'")
        return None

    monkeypatch.setattr(discovery.importlib, "import_module", fake_import)

    graphs, experiments, errors = discover_configs(tmp_path)

    assert not graphs and not experiments
    err = errors[str(exp_dir / "config.yaml")]
    assert "crystallize-extras" in str(err)
