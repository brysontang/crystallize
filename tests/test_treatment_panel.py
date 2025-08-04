import json
from pathlib import Path

import pytest
from rich.style import Style
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
        screen._build_tree()
        tree = screen.query_one("#node-tree", Tree)
        node_b = next(
            n for n in tree.root.children if n.data and n.data[1] == "treatment_b"
        )
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
        screen2._build_tree()
        assert "treatment_b" in screen2._inactive_treatments
        assert [t.name for t in screen2._obj.treatments] == ["treatment_a"]

        state_path.unlink()
        tree = screen2.query_one("#node-tree", Tree)
        node_b = next(
            n for n in tree.root.children if n.data and n.data[1] == "treatment_b"
        )
        tree._cursor_node = node_b
        screen2.action_toggle_treatment()
        data = json.loads(state_path.read_text())
        assert data["inactive_treatments"] == []


@pytest.mark.asyncio
async def test_summary_shows_inactive_metrics(tmp_path: Path) -> None:
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
        screen._build_tree()
        tree = screen.query_one("#node-tree", Tree)
        node_b = next(
            n for n in tree.root.children if n.data and n.data[1] == "treatment_b"
        )
        tree._cursor_node = node_b
        screen.action_toggle_treatment()
        screen._reload_object()
        plugin = screen._obj.get_plugin(ArtifactPlugin)
        plugin.root_dir = str(tmp_path)
        result = await screen._obj.arun(strategy="resume")
        screen._experiments = [screen._obj]
        screen.render_summary(result, highlight="treatment_b")
        text = screen.summary_plain_text
        assert "treatment_a" in text and "treatment_b" in text
        assert text.index("treatment_b") < text.index("treatment_a")
        screen.action_summary()
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
        screen._build_tree()
        tree = screen.query_one("#node-tree", Tree)
        node_add = next(
            n for n in tree.root.children if n.data and n.data[0] == "add_treatment"
        )
        tree._cursor_node = node_add
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
        screen._build_tree()
        tree = screen.query_one("#node-tree", Tree)
        node_a = next(
            n for n in tree.root.children if n.data and n.data[1] == "treatment_a"
        )
        node_b = next(
            n for n in tree.root.children if n.data and n.data[1] == "treatment_b"
        )
        tree._cursor_node = node_b
        label_b = screen.action_toggle_treatment()
        assert Style.parse(node_a.label.style) == Style.parse("green")
        assert label_b is not None and Style.parse(label_b.style) == Style.parse("red")
