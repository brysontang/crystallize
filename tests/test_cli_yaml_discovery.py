from pathlib import Path

import yaml

from cli.discovery import discover_configs


def test_yaml_discovery(tmp_path: Path) -> None:
    exp_dir = tmp_path / "exp"
    exp_dir.mkdir()
    cfg1 = {
        "name": "exp",
        "datasource": {"n": "numbers"},
        "cli": {"group": "Data", "priority": 1, "icon": "X", "color": "#111111"},
    }
    (exp_dir / "config.yaml").write_text(yaml.safe_dump(cfg1))

    graph_dir = tmp_path / "graph"
    graph_dir.mkdir()
    cfg2 = {
        "name": "graph",
        "datasource": {"data": "exp#out"},
        "cli": {"disabled": True},
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
    default_key = next(
        k for k, v in experiments.items() if v["path"] == other / "config.yaml"
    )
    default_info = experiments[default_key]
    assert default_info["cli"]["group"] == "Experiments"
    assert default_info["cli"]["icon"] == "🧪"
    assert not errors
