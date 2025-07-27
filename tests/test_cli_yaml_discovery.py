from pathlib import Path

import yaml

from cli.discovery import discover_configs


def test_yaml_discovery(tmp_path: Path) -> None:
    exp_dir = tmp_path / "exp"
    exp_dir.mkdir()
    cfg1 = {"name": "exp", "datasource": {"n": "numbers"}}
    (exp_dir / "config.yaml").write_text(yaml.safe_dump(cfg1))

    graph_dir = tmp_path / "graph"
    graph_dir.mkdir()
    cfg2 = {"name": "graph", "datasource": {"data": "exp#out"}}
    (graph_dir / "config.yaml").write_text(yaml.safe_dump(cfg2))

    graphs, experiments, errors = discover_configs(tmp_path)

    graph_paths = {info["path"] for info in graphs.values()}
    exp_paths = {info["path"] for info in experiments.values()}

    assert (graph_dir / "config.yaml") in graph_paths
    assert (exp_dir / "config.yaml") in exp_paths
    assert not errors
