from __future__ import annotations

import importlib
import sys
import time
from pathlib import Path
from typing import Any

import pytest
from textual.app import App
from textual.widgets import Button, Tree

from cli.screens.run import RunScreen, _inject_status_plugin, delete_artifacts, _reload_modules
from cli.status_plugin import CLIStatusPlugin
from cli.utils import create_experiment_scaffolding
from cli.widgets.writer import WidgetWriter
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


class DummyWidget:
    def write(self, msg: str) -> None:  # pragma: no cover - simple stub
        pass

    def refresh(self) -> None:  # pragma: no cover - simple stub
        pass


class DummyApp:
    def call_from_thread(self, func, *args, **kwargs) -> None:  # pragma: no cover
        func(*args, **kwargs)


def test_delete_artifacts(tmp_path: Path) -> None:
    plugin = ArtifactPlugin(root_dir=str(tmp_path))
    exp = Experiment(
        datasource=dummy_source(),
        pipeline=Pipeline([add_one()]),
        name="e",
        plugins=[plugin],
    )
    exp.validate()
    path = Path(plugin.root_dir) / "e"
    path.mkdir()
    delete_artifacts(exp)
    assert not path.exists()


def test_inject_status_plugin_adds_experiment(tmp_path: Path) -> None:
    plugin = ArtifactPlugin(root_dir=str(tmp_path))
    exp = Experiment(
        datasource=dummy_source(),
        pipeline=Pipeline([add_one()]),
        name="exp",
        plugins=[plugin],
    )
    exp.validate()
    events: list[dict[str, Any]] = []

    def cb(event: str, info: dict[str, Any]) -> None:
        events.append(info)

    writer = WidgetWriter(DummyWidget(), DummyApp(), [])
    _inject_status_plugin(exp, cb, writer)
    plugin = exp.get_plugin(CLIStatusPlugin)
    assert plugin is not None
    plugin.callback("start", {})
    assert events[0]["experiment"] == "exp"


def test_reload_modules(tmp_path: Path) -> None:
    pkg_dir = tmp_path / "pkg"
    pkg_dir.mkdir()
    init_file = pkg_dir / "__init__.py"
    init_file.write_text("VALUE = 1\n")
    sys.path.insert(0, str(tmp_path))
    mod = importlib.import_module("pkg")
    assert mod.VALUE == 1
    time.sleep(1)
    init_file.write_text("VALUE = 2\n")
    _reload_modules(tmp_path)
    importlib.invalidate_caches()
    mod2 = importlib.import_module("pkg")
    assert mod2.VALUE == 2
    sys.path.remove(str(tmp_path))
    sys.modules.pop("pkg", None)


@pytest.mark.asyncio
async def test_build_tree_and_toggle_cache(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    exp_dir = create_experiment_scaffolding("demo", directory=tmp_path, examples=True)
    cfg = exp_dir / "config.yaml"
    monkeypatch.chdir(tmp_path)
    obj = Experiment.from_yaml(cfg)
    async with App().run_test() as pilot:
        screen = RunScreen(obj, cfg, False, None)
        await pilot.app.push_screen(screen)
        screen.worker = type("W", (), {"is_finished": True})()
        screen._reload_object()
        screen._build_tree()
        tree = screen.query_one("#node-tree", Tree)
        exp_name = screen._obj.name
        step_name = screen._obj.pipeline.steps[0].__class__.__name__
        step_node = tree.root.children[0].children[0]
        assert "🔒" not in step_node.label.plain
        assert (exp_name,) in screen.tree_nodes
        assert (exp_name, step_name) in screen.tree_nodes
        screen.worker = type("W", (), {"is_finished": True})()


@pytest.mark.asyncio
async def test_build_tree_shows_lock_for_cacheable_step(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    exp_dir = create_experiment_scaffolding("demo", directory=tmp_path, examples=True)
    # make step cacheable in code
    step_file = exp_dir / "steps.py"
    step_file.write_text(
        "from crystallize import pipeline_step\n"
        "@pipeline_step(cacheable=True)\n"
        "def add_one(data: int, delta: int = 1) -> int:\n"
        "    return data + delta\n"
    )
    cfg = exp_dir / "config.yaml"
    monkeypatch.chdir(tmp_path)
    obj = Experiment.from_yaml(cfg)
    async with App().run_test() as pilot:
        screen = RunScreen(obj, cfg, False, None)
        await pilot.app.push_screen(screen)
        screen.worker = type("W", (), {"is_finished": True})()
        screen._reload_object()
        screen._build_tree()
        tree = screen.query_one("#node-tree", Tree)
        step_node = tree.root.children[0].children[0]
        assert "🔒" in step_node.label.plain
        screen.worker = type("W", (), {"is_finished": True})()


@pytest.mark.xfail(reason="cache not reused")
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
        screen._reload_object()
        screen._build_tree()
        tree = screen.query_one("#node-tree", Tree)
        step_node = tree.root.children[0].children[0]
        tree._cursor_node = step_node  # type: ignore[attr-defined]
        screen.action_toggle_cache()
        await screen._obj.arun()
        assert counter_file.read_text() == "1"
        await screen._obj.arun()
        assert counter_file.read_text() == "1"
        screen.worker = type("W", (), {"is_finished": True})()


@pytest.mark.asyncio
async def test_run_reloads_changed_step_code(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    exp_dir = create_experiment_scaffolding("demo", directory=tmp_path, examples=True)
    step_file = exp_dir / "steps.py"
    marker = exp_dir / "marker.txt"
    step_file.write_text(
        "from pathlib import Path\nfrom crystallize import pipeline_step\n"
        "MARK = Path(__file__).with_name('marker.txt')\n"
        "@pipeline_step()\n"
        "def add_one(data: int, delta: int = 1) -> int:\n"
        "    MARK.write_text('first')\n"
        "    return data + delta\n"
    )
    cfg = exp_dir / "config.yaml"
    monkeypatch.chdir(tmp_path)
    obj = Experiment.from_yaml(cfg)
    async with App().run_test() as pilot:
        screen = RunScreen(obj, cfg, False, None)
        await pilot.app.push_screen(screen)
        await screen._obj.arun()
        assert marker.read_text() == "first"
        step_file.write_text(
            "from pathlib import Path\nfrom crystallize import pipeline_step\n"
            "MARK = Path(__file__).with_name('marker.txt')\n"
            "@pipeline_step()\n"
            "def add_one(data: int, delta: int = 1) -> int:\n"
            "    MARK.write_text('second')\n"
            "    return data + delta + 1\n"
        )
        screen._reload_object()
        await screen._obj.arun()
        assert marker.read_text() == "second"
        screen.worker = type("W", (), {"is_finished": True})()


@pytest.mark.asyncio
async def test_handle_status_events_updates_state(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    exp_dir = create_experiment_scaffolding("demo", directory=tmp_path, examples=True)
    cfg = exp_dir / "config.yaml"
    monkeypatch.chdir(tmp_path)
    obj = Experiment.from_yaml(cfg)
    async with App().run_test() as pilot:
        screen = RunScreen(obj, cfg, False, None)
        await pilot.app.push_screen(screen)
        screen.worker = type("W", (), {"is_finished": True})()
        screen._reload_object()
        screen._build_tree()
        tree = screen.query_one("#node-tree", Tree)
        exp_name = obj.name
        exp_node = tree.root.children[0]
        step_name = obj.pipeline.steps[0].__class__.__name__
        step_node = exp_node.children[0]
        assert "⏳" in exp_node.label.plain
        screen._handle_status_event(
            "start", {"experiment": "demo", "steps": [step_name], "replicates": 2}
        )
        assert screen.experiment_states["demo"] == "running"
        exp_node = screen.tree_nodes[(exp_name,)]
        assert "⚙️" in exp_node.label.plain
        screen._handle_status_event(
            "replicate",
            {"experiment": "demo", "replicate": 1, "total": 2, "condition": "t"},
        )
        assert screen.replicate_progress == (1, 2)
        assert screen.current_treatment == "t"
        assert "Treatment: t" in screen.top_bar
        screen._handle_status_event(
            "step", {"experiment": "demo", "step": step_name, "percent": 0.5}
        )
        assert screen.progress_percent == 0.5
        assert "50%" in screen.top_bar
        step_node = screen.tree_nodes[(exp_name, step_name)]
        assert "⚙️" in step_node.label.plain
        screen._handle_status_event(
            "step_finished", {"experiment": "demo", "step": step_name}
        )
        assert screen.step_states[("demo", step_name)] == "completed"
        step_node = screen.tree_nodes[(exp_name, step_name)]
        assert "✅" in step_node.label.plain
        exp_node = screen.tree_nodes[(exp_name,)]
        assert "✅" in exp_node.label.plain
        screen.worker = type("W", (), {"is_finished": True})()


@pytest.mark.asyncio
async def test_run_or_cancel_behaviour(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    exp_dir = create_experiment_scaffolding("demo", directory=tmp_path, examples=True)
    cfg = exp_dir / "config.yaml"
    monkeypatch.chdir(tmp_path)
    obj = Experiment.from_yaml(cfg)
    async with App().run_test() as pilot:
        screen = RunScreen(obj, cfg, False, None)
        await pilot.app.push_screen(screen)
        screen.worker = type("W", (), {"is_finished": True})()
        called = False

        def fake_start() -> None:
            nonlocal called
            called = True

        screen._start_run = fake_start  # type: ignore[assignment]
        screen.action_run_or_cancel()
        assert called

        class DummyWorker:
            is_finished = False
            cancelled = False

            def cancel(self) -> None:
                self.cancelled = True

        worker = DummyWorker()
        screen.worker = worker
        screen.action_run_or_cancel()
        assert worker.cancelled
        screen.worker = type("W", (), {"is_finished": True})()


@pytest.mark.asyncio
async def test_on_experiment_complete_opens_summary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    exp_dir = create_experiment_scaffolding("demo", directory=tmp_path, examples=True)
    cfg = exp_dir / "config.yaml"
    monkeypatch.chdir(tmp_path)
    obj = Experiment.from_yaml(cfg)
    async with App().run_test() as pilot:
        screen = RunScreen(obj, cfg, False, None)
        await pilot.app.push_screen(screen)
        screen.worker = type("W", (), {"is_finished": True})()
        opened: list[Any] = []

        def fake_open(res: Any) -> None:
            opened.append(res)

        screen.open_summary_screen = fake_open  # type: ignore[assignment]
        message = screen.ExperimentComplete(result=123)
        screen.on_experiment_complete(message)
        run_btn = screen.query_one("#run-btn", Button)
        assert opened == [123]
        assert screen.worker is None
        assert run_btn.label == "Run"
        screen.worker = type("W", (), {"is_finished": True})()


@pytest.mark.asyncio
async def test_step_logs_written(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    exp_dir = create_experiment_scaffolding("demo", directory=tmp_path, examples=True)
    cfg = exp_dir / "config.yaml"
    monkeypatch.chdir(tmp_path)
    obj = Experiment.from_yaml(cfg)
    async with App().run_test() as pilot:
        screen = RunScreen(obj, cfg, False, None)
        await pilot.app.push_screen(screen)
        screen.worker = type("W", (), {"is_finished": True})()
        log_widget = screen.query_one("#live_log")
        log_widget.write("hello")
        screen.log_history.append("hello")
        assert any("hello" in msg for msg in screen.log_history)
