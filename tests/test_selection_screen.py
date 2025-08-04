import os
import json
from pathlib import Path

import yaml
import pytest
from textual.app import App
from textual.widgets import Static, Tree

from cli.utils import create_experiment_scaffolding

from cli.screens.selection import SelectionScreen
from cli.widgets.config_editor import ConfigEditorWidget


@pytest.mark.asyncio
async def test_update_details_mounts_widget(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    exp_dir = tmp_path / "exp"
    exp_dir.mkdir()
    cfg = exp_dir / "config.yaml"
    cfg.write_text(
        yaml.safe_dump(
            {
                "name": "e",
                "cli": {"icon": "🔬", "group": "test", "priority": 1},
                "steps": ["simple"],
                "datasource": {},
                "treatments": {},
            }
        )
    )
    hist_dir = tmp_path / ".cache" / "crystallize" / "steps"
    hist_dir.mkdir(parents=True)
    (hist_dir / "e.json").write_text(json.dumps({"SimpleStep": [1.0]}))

    cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        async with App().run_test() as pilot:
            screen = SelectionScreen()
            await pilot.app.push_screen(screen)
            await pilot.pause(1)

            data = {
                "path": str(cfg),
                "label": "test",
                "type": "Experiment",
                "doc": "test doc",
            }
            await screen._update_details(data)

            container = screen.query_one("#config-container")
            assert any(
                isinstance(child, ConfigEditorWidget) for child in container.children
            )
            details = screen.query_one("#details", Static)
            assert "Estimated runtime" in str(details.renderable)
    finally:
        os.chdir(cwd)


@pytest.mark.asyncio
async def test_loads_with_no_experiments(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    async with App().run_test() as pilot:
        screen = SelectionScreen()
        await pilot.app.push_screen(screen)
        await pilot.pause(1)
        tree = screen.query_one("#object-tree", Tree)
        assert not list(tree.root.children)


@pytest.mark.asyncio
async def test_loads_with_experiments(tmp_path: Path, monkeypatch) -> None:
    exp1 = tmp_path / "exp1"
    exp1.mkdir()
    (exp1 / "config.yaml").write_text(
        yaml.safe_dump(
            {
                "name": "e1",
                "cli": {"icon": "🧪", "group": "Experiments", "priority": 1},
                "datasource": {},
                "steps": ["s"],
                "treatments": {},
            }
        )
    )
    exp2 = tmp_path / "exp2"
    exp2.mkdir()
    (exp2 / "config.yaml").write_text(
        yaml.safe_dump(
            {
                "name": "e2",
                "cli": {"icon": "🧪", "group": "Experiments", "priority": 1},
                "datasource": {},
                "steps": ["s"],
                "treatments": {},
            }
        )
    )
    monkeypatch.chdir(tmp_path)
    async with App().run_test() as pilot:
        screen = SelectionScreen()
        await pilot.app.push_screen(screen)
        await pilot.pause(1)
        tree = screen.query_one("#object-tree", Tree)
        group = next(g for g in tree.root.children if g.label.plain == "Experiments")
        for _ in range(10):
            if len(group.children) >= 2:
                break
            await pilot.pause(0.1)
        labels = [child.label.plain for child in group.children]
        assert any("exp1 - e1" in label for label in labels)
        assert any("exp2 - e2" in label for label in labels)


@pytest.mark.asyncio
async def test_estimated_time_multiple_runs(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    exp_dir = tmp_path / "exp"
    exp_dir.mkdir()
    cfg = exp_dir / "config.yaml"
    cfg.write_text(
        yaml.safe_dump(
            {
                "name": "exp",
                "cli": {"icon": "🧪", "group": "Experiments", "priority": 1},
                "datasource": {},
                "steps": ["simple"],
                "treatments": {},
            }
        )
    )
    hist_dir = tmp_path / ".cache" / "crystallize" / "steps"
    hist_dir.mkdir(parents=True)
    (hist_dir / "exp.json").write_text(json.dumps({"SimpleStep": [1.0, 3.0]}))

    monkeypatch.chdir(tmp_path)
    async with App().run_test() as pilot:
        screen = SelectionScreen()
        await pilot.app.push_screen(screen)
        await pilot.pause(1)
        tree = screen.query_one("#object-tree", Tree)
        node = tree.root.children[0].children[0]
        data = node.data
        await screen._update_details(data)
        details = screen.query_one("#details", Static)
        assert "2s" in str(details.renderable)


@pytest.mark.asyncio
async def test_graph_estimated_time(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    e1 = tmp_path / "e1"
    e1.mkdir()
    (e1 / "config.yaml").write_text(
        yaml.safe_dump(
            {
                "name": "e1",
                "cli": {"icon": "🧪", "group": "Experiments", "priority": 1},
                "datasource": {},
                "steps": ["a"],
                "treatments": {},
            }
        )
    )
    graph_cfg = tmp_path / "config.yaml"
    graph_cfg.write_text(
        yaml.safe_dump(
            {
                "name": "graph",
                "cli": {"icon": "📈", "group": "Graphs", "priority": 1},
                "datasource": {"x": "e1#out"},
                "steps": ["b"],
                "treatments": {},
            }
        )
    )
    hist_dir = tmp_path / ".cache" / "crystallize" / "steps"
    hist_dir.mkdir(parents=True)
    (hist_dir / "e1.json").write_text(json.dumps({"AStep": [1.0]}))
    (hist_dir / "graph.json").write_text(json.dumps({"BStep": [2.0]}))

    monkeypatch.chdir(tmp_path)
    async with App().run_test() as pilot:
        screen = SelectionScreen()
        await pilot.app.push_screen(screen)
        await pilot.pause(1)
        tree = screen.query_one("#object-tree", Tree)
        # Second group should be graphs
        graph_group = next(g for g in tree.root.children if g.label.plain == "Graphs")
        node = graph_group.children[0]
        await screen._update_details(node.data)
        details = screen.query_one("#details", Static)
        assert "3s" in str(details.renderable)


@pytest.mark.asyncio
async def test_refresh_updates_list(tmp_path: Path, monkeypatch) -> None:
    exp = tmp_path / "exp"
    exp.mkdir()
    cfg = exp / "config.yaml"
    cfg.write_text(
        yaml.safe_dump(
            {
                "name": "old",
                "cli": {"icon": "🧪", "group": "Experiments", "priority": 1},
                "datasource": {},
                "steps": ["s"],
                "treatments": {},
            }
        )
    )
    monkeypatch.chdir(tmp_path)
    async with App().run_test() as pilot:
        screen = SelectionScreen()
        await pilot.app.push_screen(screen)
        await pilot.pause(1)
        tree = screen.query_one("#object-tree", Tree)
        group = tree.root.children[0]
        assert "old" in group.children[0].label.plain

        data = yaml.safe_load(cfg.read_text())
        data["name"] = "new"
        cfg.write_text(yaml.safe_dump(data))
        await pilot.press("r")
        await pilot.pause(1)
        tree = screen.query_one("#object-tree", Tree)
        group = tree.root.children[0]
        assert "new" in group.children[0].label.plain


@pytest.mark.asyncio
async def test_create_experiment_refreshes(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    async with App().run_test() as pilot:
        screen = SelectionScreen()
        await pilot.app.push_screen(screen)
        await pilot.pause(1)

        def fake_push(screen_obj, cb):
            create_experiment_scaffolding("newexp", directory=Path("experiments"))
            cb(None)

        screen.app.push_screen = fake_push  # type: ignore[assignment]
        await pilot.press("n")
        await pilot.pause(1)
        tree = screen.query_one("#object-tree", Tree)
        group = tree.root.children[0]
        labels = [child.label.plain for child in group.children]
        assert any("newexp" in label for label in labels)


@pytest.mark.asyncio
async def test_details_edit_updates_config(tmp_path: Path, monkeypatch) -> None:
    cfg = tmp_path / "config.yaml"
    cfg.write_text(
        yaml.safe_dump(
            {
                "name": "e",
                "cli": {"icon": "🧪", "group": "Experiments", "priority": 1},
                "datasource": {},
                "steps": ["s"],
                "treatments": {},
            }
        )
    )
    monkeypatch.chdir(tmp_path)
    async with App().run_test() as pilot:
        screen = SelectionScreen()
        await pilot.app.push_screen(screen)
        await pilot.pause(1)
        tree = screen.query_one("#object-tree", Tree)
        node = tree.root.children[0].children[0]
        await screen._update_details(node.data)
        container = screen.query_one("#config-container")
        widget = container.query_one(ConfigEditorWidget)
        await pilot.pause(0.1)
        steps_node = next(
            c for c in widget.cfg_tree.root.children if str(c.label) == "steps"
        )
        leaf = steps_node.children[0]
        widget.cfg_tree._cursor_node = leaf  # type: ignore[attr-defined]

        async def fake_push(screen_obj, cb):
            cb("t")

        widget.app.push_screen = fake_push  # type: ignore[assignment]
        await widget.action_edit()
        data = yaml.safe_load(cfg.read_text())
        assert data["steps"] == ["t"]


@pytest.mark.asyncio
async def test_update_details_missing_cli(tmp_path: Path, monkeypatch) -> None:
    cfg = tmp_path / "config.yaml"
    cfg.write_text(
        yaml.safe_dump({"name": "e", "steps": ["s"], "treatments": {}, "datasource": {}})
    )
    monkeypatch.chdir(tmp_path)
    async with App().run_test() as pilot:
        screen = SelectionScreen()
        await pilot.app.push_screen(screen)
        await pilot.pause(1)
        data = {
            "path": str(cfg),
            "label": "test",
            "type": "Experiment",
            "doc": "",
        }
        await screen._update_details(data)


@pytest.mark.asyncio
async def test_run_missing_step_shows_error(tmp_path: Path, monkeypatch) -> None:
    exp = tmp_path / "exp"
    exp.mkdir()
    (exp / "config.yaml").write_text(
        yaml.safe_dump(
            {
                "name": "e",
                "cli": {"icon": "🧪", "group": "Experiments", "priority": 1},
                "datasource": {"x": "ds"},
                "steps": ["missing"],
                "treatments": {},
            }
        )
    )
    (exp / "steps.py").write_text("")
    (exp / "datasources.py").write_text(
        """
def ds():
    return 1
"""
    )
    monkeypatch.chdir(tmp_path)
    async with App().run_test() as pilot:
        screen = SelectionScreen()
        await pilot.app.push_screen(screen)
        await pilot.pause(1)
        tree = screen.query_one("#object-tree", Tree)
        node = tree.root.children[0].children[0]
        await screen._run_interactive_and_exit(node.data)
        await pilot.pause(0.1)
        err_screen = pilot.app.screen_stack[-1]
        msg = err_screen.query_one("#error-msg", Static).renderable
        assert "Verify your configuration" in str(msg)


@pytest.mark.asyncio
async def test_invalid_yaml_shows_error(tmp_path: Path, monkeypatch) -> None:
    bad = tmp_path / "bad"
    bad.mkdir()
    (bad / "config.yaml").write_text("name: x:\n - bad")
    monkeypatch.chdir(tmp_path)
    async with App().run_test() as pilot:
        screen = SelectionScreen()
        await pilot.app.push_screen(screen)
        await pilot.pause(1)
        assert screen._load_errors
        screen.action_show_errors()
        await pilot.pause(0.1)
        err_screen = pilot.app.screen_stack[-1]
        msg = err_screen.query_one("#error-msg", Static).renderable
        assert "Invalid YAML" in str(msg)
