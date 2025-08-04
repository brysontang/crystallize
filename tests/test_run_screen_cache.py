from __future__ import annotations

from pathlib import Path

import pytest
from textual.app import App
from textual.widgets import Tree

from cli.screens.run import RunScreen
from cli.utils import create_experiment_scaffolding
from crystallize import data_source, pipeline_step
from crystallize.experiments.experiment import Experiment
from crystallize.pipelines.pipeline import Pipeline
from crystallize.plugins.plugins import ArtifactPlugin


@data_source
def dummy_source(ctx):
    return 0


@pipeline_step()
def add_one(data, ctx):
    return data + 1

@pytest.mark.asyncio
async def test_toggle_cache_persists_between_runs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    exp_dir = create_experiment_scaffolding("demo", directory=tmp_path, examples=True)
    step_file = exp_dir / "steps.py"
    counter_file = exp_dir / "count.txt"
    step_file.write_text(
        "from pathlib import Path\nfrom crystallize import pipeline_step\n"
        "CNT = Path(__file__).with_name('count.txt')\n"
        "@pipeline_step()\n"
        "def add_one(data: int, delta: int = 1) -> int:\n"
        "    n = int(CNT.read_text()) if CNT.exists() else 0\n"
        "    CNT.write_text(str(n + 1))\n"
        "    return data + delta\n"
    )
    cfg = exp_dir / "config.yaml"
    monkeypatch.setenv("CRYSTALLIZE_CACHE_DIR", str(tmp_path / ".cache"))
    monkeypatch.chdir(tmp_path)
    obj = Experiment.from_yaml(cfg)
    async with App().run_test() as pilot:  # noqa: SIM117
        screen = RunScreen(obj, cfg, False, None)
        await pilot.app.push_screen(screen)
        screen.worker = type("W", (), {"is_finished": True})()
        tree = screen.query_one("#exp-tree", Tree)
        tree.root.remove_children()
        screen._reload_object()
        screen._build_trees()
        tree = screen.query_one("#exp-tree", Tree)
        step_node = tree.root.children[0].children[0]
        tree.focus()
        tree._cursor_node = step_node  # type: ignore[attr-defined]
        screen.action_toggle_cache()
        await screen._obj.arun()
        assert counter_file.read_text() == "1"
        await screen._obj.arun()
        assert counter_file.read_text() == "1"
        screen.worker = type("W", (), {"is_finished": True})()


@pytest.mark.asyncio
async def test_all_steps_cache_when_toggled(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cnt1 = tmp_path / "count1.txt"
    cnt2 = tmp_path / "count2.txt"

    @data_source
    def src(ctx):  # type: ignore[unused-ignore]
        return 0

    @pipeline_step()
    def step_one(data, ctx):
        n = int(cnt1.read_text()) if cnt1.exists() else 0
        cnt1.write_text(str(n + 1))
        return data + 1

    @pipeline_step()
    def step_two(data, ctx):
        n = int(cnt2.read_text()) if cnt2.exists() else 0
        cnt2.write_text(str(n + 1))
        return data + 1

    exp = Experiment(
        datasource=src(),
        pipeline=Pipeline([step_one(), step_two()]),
        name="demo",
    )
    cfg = tmp_path / "dummy.yaml"
    cfg.write_text("")
    monkeypatch.setenv("CRYSTALLIZE_CACHE_DIR", str(tmp_path / ".cache"))
    monkeypatch.chdir(tmp_path)
    async with App().run_test() as pilot:
        screen = RunScreen(exp, cfg, False, None)
        screen._reload_object = lambda: None  # type: ignore[assignment]
        await pilot.app.push_screen(screen)
        screen.worker = type("W", (), {"is_finished": True})()
        screen._build_trees()
        tree = screen.query_one("#exp-tree", Tree)
        exp_node = tree.root.children[0]
        tree.focus()
        for step_node in exp_node.children:
            tree._cursor_node = step_node  # type: ignore[attr-defined]
            screen.action_toggle_cache()
        await screen._obj.arun()
        await screen._obj.arun()
        assert cnt1.read_text() == "1"
        assert cnt2.read_text() == "1"
        screen.worker = type("W", (), {"is_finished": True})()


@pytest.mark.asyncio
async def test_build_artifacts_respects_experiment_lock(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    exp_dir = create_experiment_scaffolding("demo", directory=tmp_path, examples=True)
    cfg = exp_dir / "config.yaml"
    monkeypatch.chdir(tmp_path)
    obj = Experiment.from_yaml(cfg)
    plugin = obj.get_plugin(ArtifactPlugin)
    assert plugin is not None
    plugin.root_dir = str(tmp_path / "artifacts")
    obj.validate()
    async with App().run_test() as pilot:
        screen = RunScreen(obj, cfg, False, None)
        screen._reload_object = lambda: None  # type: ignore[assignment]
        await pilot.app.push_screen(screen)
        screen.worker = type("W", (), {"is_finished": True})()
        screen._build_trees()
        exp_path = Path(plugin.root_dir) / "demo"
        exp_path.mkdir(parents=True)
        screen._build_artifacts()
        assert exp_path.exists()
        exp_path.mkdir(parents=True, exist_ok=True)
        screen.experiment_cacheable["demo"] = False
        screen._build_artifacts()
        assert exp_path.exists()
        assert obj.strategy == "rerun"
        screen.worker = type("W", (), {"is_finished": True})()


@pytest.mark.asyncio
async def test_resume_marks_completed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    exp_dir = create_experiment_scaffolding("demo", directory=tmp_path, examples=True)
    cfg = exp_dir / "config.yaml"
    monkeypatch.chdir(tmp_path)
    obj = Experiment.from_yaml(cfg)
    plugin = obj.get_plugin(ArtifactPlugin)
    assert plugin is not None
    plugin.root_dir = str(tmp_path / "artifacts")
    obj.validate()
    await obj.arun()
    obj2 = Experiment.from_yaml(cfg)
    plugin2 = obj2.get_plugin(ArtifactPlugin)
    assert plugin2 is not None
    plugin2.root_dir = str(tmp_path / "artifacts")
    obj2.validate()
    async with App().run_test() as pilot:
        screen = RunScreen(obj2, cfg, False, None)
        screen._reload_object = lambda: None  # type: ignore[assignment]
        await pilot.app.push_screen(screen)
        screen.worker = type("W", (), {"is_finished": True})()
        tree = screen.query_one("#exp-tree", Tree)
        exp_node = tree.root.children[0]
        step_node = exp_node.children[0]
        assert "✅" in exp_node.label.plain
        assert "✅" in step_node.label.plain
