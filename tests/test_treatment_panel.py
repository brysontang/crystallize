import json
from pathlib import Path

import pytest
from textual.app import App
from textual.widgets import Tree

from cli.screens.run import RunScreen
from crystallize import data_source, pipeline_step
from crystallize.experiments.experiment import Experiment
from crystallize.plugins.plugins import ArtifactPlugin


@data_source
def source(ctx):
    return 0


@pipeline_step()
def metric_step(data, ctx):
    ctx.metrics.add("score", data)
    return data


def _write_config(tmp_path: Path) -> Path:
    cfg = tmp_path / "config.yaml"
    cfg.write_text(
        """
name: exp
datasource:
  x: source
steps:
  - metric_step
treatments:
  treatment_a:
    val: 1
  treatment_b:
    val: 2
"""
    )
    datasources = tmp_path / "datasources.py"
    datasources.write_text(
        "from crystallize import data_source\n@data_source\ndef source(ctx):\n    return 0\n"
    )
    steps = tmp_path / "steps.py"
    steps.write_text(
        "from crystallize import pipeline_step\n@pipeline_step()\ndef metric_step(data, ctx):\n    ctx.metrics.add('score', data)\n    return data\n"
    )
    return cfg


@pytest.mark.asyncio
async def test_toggle_state_persistence(tmp_path: Path) -> None:
    cfg = _write_config(tmp_path)
    exp = Experiment.from_yaml(cfg)
    plugin = exp.get_plugin(ArtifactPlugin)
    plugin.root_dir = str(tmp_path)
    screen = RunScreen(exp, cfg, False, None)

    class TestApp(App):
        async def on_mount(self) -> None:  # pragma: no cover - helper
            await self.push_screen(screen)

    app = TestApp()
    async with app.run_test():
        screen._reload_object()
        plugin = screen._obj.get_plugin(ArtifactPlugin)
        plugin.root_dir = str(tmp_path)
        screen._build_trees()
        tree = screen.query_one("#treatment-tree", Tree)
        node_b = next(
            n for n in tree.root.children if n.data and n.data[1] == "treatment_b"
        )
        tree.focus()
        tree._cursor_node = node_b
        screen.action_toggle_treatment()
    state_path = cfg.with_suffix(".state.json")
    data = json.loads(state_path.read_text())
    assert data["inactive_treatments"] == ["treatment_b"]

    exp2 = Experiment.from_yaml(cfg)
    plugin2 = exp2.get_plugin(ArtifactPlugin)
    plugin2.root_dir = str(tmp_path)
    screen2 = RunScreen(exp2, cfg, False, None)

    class TestApp2(App):
        async def on_mount(self) -> None:  # pragma: no cover - helper
            await self.push_screen(screen2)

    app2 = TestApp2()
    async with app2.run_test():
        screen2._reload_object()
        plugin = screen2._obj.get_plugin(ArtifactPlugin)
        plugin.root_dir = str(tmp_path)
        screen2._build_trees()
        assert "treatment_b" in screen2._inactive_treatments
        assert [t.name for t in screen2._obj.treatments] == ["treatment_a"]

        state_path.unlink()
        tree = screen2.query_one("#treatment-tree", Tree)
        node_b = next(
            n for n in tree.root.children if n.data and n.data[1] == "treatment_b"
        )
        tree.focus()
        tree._cursor_node = node_b
        screen2.action_toggle_treatment()
        data = json.loads(state_path.read_text())
        assert data["inactive_treatments"] == []


@pytest.mark.asyncio
async def test_summary_shortcut_shows_inactive_metrics(tmp_path: Path) -> None:
    cfg = _write_config(tmp_path)
    exp_first = Experiment.from_yaml(cfg)
    plugin = exp_first.get_plugin(ArtifactPlugin)
    plugin.root_dir = str(tmp_path)
    await exp_first.arun()

    exp = Experiment.from_yaml(cfg)
    plugin = exp.get_plugin(ArtifactPlugin)
    plugin.root_dir = str(tmp_path)
    screen = RunScreen(exp, cfg, False, None)

    class AppTest(App):
        async def on_mount(self) -> None:  # pragma: no cover - helper
            await self.push_screen(screen)

    app = AppTest()
    async with app.run_test():
        screen._reload_object()
        plugin = screen._obj.get_plugin(ArtifactPlugin)
        plugin.root_dir = str(tmp_path)
        screen._build_trees()
        tree = screen.query_one("#treatment-tree", Tree)
        node_b = next(
            n for n in tree.root.children if n.data and n.data[1] == "treatment_b"
        )
        tree.focus()
        tree._cursor_node = node_b
        screen.action_toggle_treatment()
        screen._reload_object()
        plugin = screen._obj.get_plugin(ArtifactPlugin)
        plugin.root_dir = str(tmp_path)
        result = await screen._obj.arun(strategy="rerun")
        screen._experiments = [screen._obj]
        screen._result = result
        screen.render_summary(result)
        text = screen.summary_plain_text
        assert "treatment_a" in text and "treatment_b" not in text
        tree._cursor_node = node_b
        tree.focus()
        screen.action_summary()
        text_all = screen.summary_plain_text
        assert "treatment_a" in text_all and "treatment_b" in text_all
        assert text_all.index("treatment_b") < text_all.index("treatment_a")
        assert screen.query_one("#summary_log").visible


@pytest.mark.asyncio
async def test_add_treatment_placeholder(tmp_path: Path, monkeypatch) -> None:
    cfg = _write_config(tmp_path)
    exp = Experiment.from_yaml(cfg)
    plugin = exp.get_plugin(ArtifactPlugin)
    plugin.root_dir = str(tmp_path)
    screen = RunScreen(exp, cfg, False, None)

    class TestApp(App):
        async def on_mount(self) -> None:  # pragma: no cover - helper
            await self.push_screen(screen)

    app = TestApp()
    async with app.run_test():
        screen._reload_object()
        plugin = screen._obj.get_plugin(ArtifactPlugin)
        plugin.root_dir = str(tmp_path)
        screen._build_trees()
        tree = screen.query_one("#treatment-tree", Tree)
        assert tree.root.children[-1].data[0] == "add_treatment"
        node_add = tree.root.children[-1]
        tree.focus()
        tree._cursor_node = node_add
        monkeypatch.setattr(RunScreen, "_focused_tree", lambda self: tree)
        monkeypatch.setattr("cli.screens.run._open_in_editor", lambda *a, **k: None)
        screen.action_edit_selected_node()
    lines = cfg.read_text().splitlines()
    idx = lines.index("  treatment_b:") + 2
    assert lines[idx] == "  # new treatment"


@pytest.mark.asyncio
async def test_color_rendering(tmp_path: Path) -> None:
    cfg = _write_config(tmp_path)
    exp = Experiment.from_yaml(cfg)
    plugin = exp.get_plugin(ArtifactPlugin)
    plugin.root_dir = str(tmp_path)
    screen = RunScreen(exp, cfg, False, None)

    class AppTest(App):
        async def on_mount(self) -> None:  # pragma: no cover - helper
            await self.push_screen(screen)

    app = AppTest()
    async with app.run_test():
        screen._reload_object()
        plugin = screen._obj.get_plugin(ArtifactPlugin)
        plugin.root_dir = str(tmp_path)
        screen._build_trees()
        tree = screen.query_one("#treatment-tree", Tree)
        node_a = next(
            n for n in tree.root.children if n.data and n.data[1] == "treatment_a"
        )
        node_b = next(
            n for n in tree.root.children if n.data and n.data[1] == "treatment_b"
        )
        tree.focus()
        screen._on_treatment_highlighted(Tree.NodeHighlighted(node_a))
        assert (
            tree.highlight_style
            and tree.highlight_style.color
            and tree.highlight_style.color.name == "green3"
        )
        tree._cursor_node = node_b
        screen._on_treatment_highlighted(Tree.NodeHighlighted(node_b))
        assert (
            tree.highlight_style
            and tree.highlight_style.color
            and tree.highlight_style.color.name == "green3"
        )
        label_b = screen.action_toggle_treatment()
        assert str(node_a.label.style) == "green"
        assert label_b is not None and str(label_b.style) == "red"
        assert (
            tree.highlight_style
            and tree.highlight_style.color
            and tree.highlight_style.color.name == "red3"
        )


@pytest.mark.asyncio
async def test_edit_apply_variable(tmp_path: Path, monkeypatch) -> None:
    cfg = _write_config(tmp_path)
    exp = Experiment.from_yaml(cfg)
    plugin = exp.get_plugin(ArtifactPlugin)
    plugin.root_dir = str(tmp_path)
    screen = RunScreen(exp, cfg, False, None)

    class AppTest(App):
        async def on_mount(self) -> None:  # pragma: no cover - helper
            await self.push_screen(screen)

    app = AppTest()
    async with app.run_test():
        screen._reload_object()
        plugin = screen._obj.get_plugin(ArtifactPlugin)
        plugin.root_dir = str(tmp_path)
        screen._build_trees()
        tree = screen.query_one("#treatment-tree", Tree)
        t_node = next(
            n for n in tree.root.children if n.data and n.data[1] == "treatment_b"
        )
        ctx_node = next(
            n for n in t_node.children if n.data and n.data[2] == "val"
        )
        tree.focus()
        tree._cursor_node = ctx_node
        captured: dict[str, int] = {}

        def fake_open(path: str, line: int | None = None) -> None:
            captured["line"] = line or 0

        monkeypatch.setattr(RunScreen, "_focused_tree", lambda self: tree)
        monkeypatch.setattr("cli.screens.run._open_in_editor", fake_open)
        screen.action_edit_selected_node()
    lines = cfg.read_text().splitlines()
    expected = lines.index("    val: 2") + 1
    assert captured["line"] == expected
