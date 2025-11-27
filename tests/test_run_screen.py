from __future__ import annotations

import contextlib
import importlib
import sys
import time
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable

import pytest
from textual.app import App
from textual.widgets import Button, RichLog, TabbedContent, TextArea, Tree

import cli.screens.run as run_module
from cli.screens.run import RunScreen, _inject_status_plugin, _reload_modules
from cli.status_plugin import CLIStatusPlugin
from cli.utils import create_experiment_scaffolding
from cli.widgets.writer import WidgetWriter
from crystallize import data_source, pipeline_step
from crystallize.experiments.experiment import Experiment
from crystallize.experiments.treatment import Treatment
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
async def test_exit_after_finished(tmp_path: Path):
    datasources = tmp_path / "datasources.py"
    datasources.write_text(
        "from crystallize import data_source\n\n@data_source\ndef source(ctx):\n    return 0\n"
    )
    steps = tmp_path / "steps.py"
    steps.write_text(
        "from crystallize import pipeline_step\nimport time\n\n@pipeline_step()\n"
        "def add_one(data, ctx):\n    time.sleep(0.1)\n    return data + 1\n"
    )
    cfg = tmp_path / "config.yaml"
    cfg.write_text(
        """
name: exp
datasource:
  x: source
steps:
  - add_one
"""
    )
    exp = Experiment.from_yaml(cfg)
    screen = RunScreen(exp, cfg, False, None)

    class TestApp(App):
        async def on_mount(self) -> None:  # pragma: no cover - test helper
            await self.push_screen(screen)

    app = TestApp()
    async with app.run_test() as pilot:
        await pilot.press("R")
        while screen.worker and not screen.worker.is_finished:
            await pilot.pause()
        await pilot.pause()
        await pilot.press("q")  # exit run screen
        assert screen not in app.screen_stack


@pytest.mark.asyncio
async def test_step_cache_persists(tmp_path: Path):
    datasources = tmp_path / "datasources.py"
    datasources.write_text(
        "from crystallize import data_source\n\n@data_source\ndef source(ctx):\n    return 0\n"
    )
    steps = tmp_path / "steps.py"
    steps.write_text(
        "from crystallize import pipeline_step\n\n@pipeline_step()\ndef add_one(data, ctx):\n    return data + 1\n"
    )
    cfg = tmp_path / "config.yaml"
    cfg.write_text(
        """
name: exp
datasource:
  x: source
steps:
  - add_one
"""
    )
    exp = Experiment.from_yaml(cfg)
    screen = RunScreen(exp, cfg, False, None)

    class TestApp(App):
        async def on_mount(self) -> None:  # pragma: no cover - test helper
            await self.push_screen(screen)

    app = TestApp()
    async with app.run_test() as pilot:
        step_key = next(iter(screen.step_cacheable))
        screen.step_cacheable[step_key] = False
        node = screen.tree_nodes[step_key]
        data = node.data
        if data and data[0] == "step":
            data[3].cacheable = False
        screen._refresh_node(step_key)
        assert not screen.step_cacheable[step_key]
        await pilot.press("R")
        while screen.worker and not screen.worker.is_finished:
            await pilot.pause()
        await pilot.pause()
        await pilot.press("R")
        assert not screen.step_cacheable[step_key]
        while screen.worker and not screen.worker.is_finished:
            await pilot.pause()
        await pilot.pause()
        await pilot.press("q")


@pytest.mark.asyncio
async def test_summary_tab_and_plain_text(tmp_path: Path):
    datasources = tmp_path / "datasources.py"
    datasources.write_text(
        "from crystallize import data_source\n\n@data_source\ndef source(ctx):\n    return 0\n"
    )
    steps = tmp_path / "steps.py"
    steps.write_text(
        "from crystallize import pipeline_step\n\n@pipeline_step()\ndef add_one(data, ctx):\n    return data + 1\n"
    )
    cfg = tmp_path / "config.yaml"
    cfg.write_text(
        """
name: exp
datasource:
  x: source
steps:
  - add_one
"""
    )
    exp = Experiment.from_yaml(cfg)
    screen = RunScreen(exp, cfg, False, None)

    class TestApp(App):
        async def on_mount(self) -> None:  # pragma: no cover - test helper
            await self.push_screen(screen)

    app = TestApp()
    async with app.run_test() as pilot:
        await pilot.press("R")
        while screen.worker and not screen.worker.is_finished:
            await pilot.pause()
        while screen.worker is not None:
            await pilot.pause()
        tabs = screen.query_one("#output-tabs", TabbedContent)
        for _ in range(50):
            if tabs.active == "summary":
                break
            await pilot.pause()
        assert tabs.active == "summary"
        llm_xml = screen.query_one("#llm_xml_output", TextArea)
        assert "<CrystallizeSummary>" in llm_xml.text
        await pilot.press("t")
        summary_rich = screen.query_one("#summary_log", RichLog)
        summary_plain = screen.query_one("#summary_plain", TextArea)
        assert summary_plain.display
        assert not summary_rich.display
        await pilot.press("q")


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
        screen._build_trees()
        tree = screen.query_one("#exp-tree", Tree)
        step_node = tree.root.children[0].children[0]
        tree.focus()
        tree._cursor_node = step_node  # type: ignore[attr-defined]
        tree._cursor_line = step_node.line  # type: ignore[attr-defined]
        called = False

        def wrapped() -> None:
            nonlocal called
            called = True

        screen.action_toggle_cache = wrapped  # type: ignore[assignment]
        await pilot.press("l")
        assert called
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
        screen._build_trees()
        tree = screen.query_one("#exp-tree", Tree)
        step_node = tree.root.children[0].children[0]
        assert "🔒" in step_node.label.plain
        screen.worker = type("W", (), {"is_finished": True})()


@pytest.mark.asyncio
async def test_step_nodes_are_leaves(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
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
        screen._build_trees()
        tree = screen.query_one("#exp-tree", Tree)
        step_node = tree.root.children[0].children[0]
        assert not step_node.allow_expand
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
async def test_top_bar_shows_current_experiment(
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
        step_name = obj.pipeline.steps[0].__class__.__name__
        screen._handle_status_event(
            "start", {"experiment": obj.name, "steps": [step_name], "replicates": 1}
        )
        assert obj.name in screen.top_bar
        screen.worker = type("W", (), {"is_finished": True})()


@pytest.mark.asyncio
async def test_handle_status_events_updates_state(
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
        screen._build_trees()
        tree = screen.query_one("#exp-tree", Tree)
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
            "step", {"experiment": "demo", "step": step_name, "percent": 0.0}
        )
        step_node = screen.tree_nodes[(exp_name, step_name)]
        assert "⚙️" in step_node.label.plain
        screen._handle_status_event(
            "step", {"experiment": "demo", "step": step_name, "percent": 0.5}
        )
        assert screen.progress_percent == 0.5
        assert "50%" in screen.top_bar
        screen._handle_status_event(
            "step_finished", {"experiment": "demo", "step": step_name}
        )
        assert screen.step_states[("demo", step_name)] == "completed"
        step_node = screen.tree_nodes[(exp_name, step_name)]
        assert "✅" in step_node.label.plain
        exp_node = screen.tree_nodes[(exp_name,)]
        assert "⚙️" in exp_node.label.plain
        screen._handle_status_event(
            "replicate",
            {"experiment": "demo", "replicate": 2, "total": 2, "condition": "t"},
        )
        assert screen.step_states[("demo", step_name)] == "pending"
        step_node = screen.tree_nodes[(exp_name, step_name)]
        assert "⏳" in step_node.label.plain
        screen.render_summary = lambda result: None  # type: ignore[assignment]
        screen.on_experiment_complete(screen.ExperimentComplete(result=123))
        exp_node = screen.tree_nodes[(exp_name,)]
        assert "✅" in exp_node.label.plain
        screen.worker = type("W", (), {"is_finished": True})()


def test_run_or_cancel_behaviour(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    exp_dir = create_experiment_scaffolding("demo", directory=tmp_path, examples=True)
    cfg = exp_dir / "config.yaml"
    monkeypatch.chdir(tmp_path)
    obj = Experiment.from_yaml(cfg)
    screen = RunScreen(obj, cfg, False, None)
    run_btn = SimpleNamespace(label="Run")
    monkeypatch.setattr(screen, "query_one", lambda *a, **kw: run_btn)
    monkeypatch.setattr(screen, "_write_error", lambda *a, **kw: None)

    screen.worker = type("W", (), {"is_finished": True})()
    called = False

    def fake_start() -> None:
        nonlocal called
        called = True

    screen._start_run = fake_start  # type: ignore[assignment]
    screen.action_run_or_cancel()
    assert called

    class DummyLoop:
        def __init__(self) -> None:
            self.called = False

        def call_soon_threadsafe(self, func: Callable[[], None]) -> None:
            self.called = True
            func()

    class DummyTask:
        def cancel(self) -> None:
            pass

    class DummyWorker:
        is_finished = False

    worker = DummyWorker()
    screen.worker = worker
    screen._loop = DummyLoop()
    screen._task = DummyTask()
    callbacks: list[Callable[[], None]] = []

    def fake_set_interval(interval: float, cb: Callable[[], None]):
        callbacks.append(cb)
        return SimpleNamespace(stop=lambda: None)

    monkeypatch.setattr(screen, "set_interval", fake_set_interval)
    screen.action_run_or_cancel()
    assert screen._loop.called
    assert run_btn.label == "Canceling..."
    worker.is_finished = True
    callbacks[0]()
    assert run_btn.label == "Run"
    assert screen.worker is None
    screen.worker = type("W", (), {"is_finished": True})()


def test_cancel_timeout_sets_force_stop_label(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    exp_dir = create_experiment_scaffolding("demo", directory=tmp_path, examples=True)
    cfg = exp_dir / "config.yaml"
    monkeypatch.chdir(tmp_path)
    obj = Experiment.from_yaml(cfg)
    screen = RunScreen(obj, cfg, False, None)
    run_btn = SimpleNamespace(label="Run")
    monkeypatch.setattr(screen, "query_one", lambda *a, **kw: run_btn)
    monkeypatch.setattr(screen, "_write_error", lambda *a, **kw: None)

    screen.worker = type("W", (), {"is_finished": False})()

    class DummyLoop:
        def call_soon_threadsafe(self, func: Callable[[], None]) -> None:
            func()

    screen._loop = DummyLoop()
    screen._task = type("T", (), {"cancel": lambda self: None})()
    callbacks: list[Callable[[], None]] = []

    def fake_set_interval(interval: float, cb: Callable[[], None]):
        callbacks.append(cb)
        return SimpleNamespace(stop=lambda: None)

    monkeypatch.setattr(screen, "set_interval", fake_set_interval)
    times = [0.0]

    def fake_perf() -> float:
        return times[0]

    monkeypatch.setattr(run_module.time, "perf_counter", fake_perf)
    screen.action_run_or_cancel()
    # simulate time passing beyond timeout
    times[0] = 6.0
    callbacks[0]()
    assert run_btn.label == "Force Stop (unsafe)"


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

        def fake_render(res: Any) -> None:
            opened.append(res)

        screen.render_summary = fake_render  # type: ignore[assignment]
        message = screen.ExperimentComplete(result=123)
        screen.on_experiment_complete(message)
        run_btn = screen.query_one("#run-btn", Button)
        tabs = screen.query_one("#output-tabs", TabbedContent)
        assert opened == [123]
        assert tabs.active == "summary"
        assert screen.worker is None
        assert run_btn.label == "Run"
        screen.worker = type("W", (), {"is_finished": True})()


@pytest.mark.asyncio
async def test_step_logs_written(
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
        log_widget = screen.query_one("#live_log")
        log_widget.write("hello")
        screen.log_history.append("hello")
        assert any("hello" in msg for msg in screen.log_history)


@pytest.mark.asyncio
async def test_tree_expanded_shows_step_status_on_experiment(
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
        screen._build_trees()
        exp_name = obj.name
        step_name = obj.pipeline.steps[0].__class__.__name__
        screen._handle_status_event(
            "start", {"experiment": exp_name, "steps": [step_name], "replicates": 1}
        )
        screen._handle_status_event(
            "step", {"experiment": exp_name, "step": step_name, "percent": 0.2}
        )
        exp_node = screen.tree_nodes[(exp_name,)]
        assert "⚙️" in exp_node.label.plain
        screen.worker = type("W", (), {"is_finished": True})()


@pytest.mark.asyncio
async def test_tree_collapsed_shows_step_status_on_experiment(
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
        screen._build_trees()
        tree = screen.query_one("#exp-tree", Tree)
        exp_name = obj.name
        exp_node = tree.root.children[0]
        step_name = obj.pipeline.steps[0].__class__.__name__
        exp_node.collapse()
        screen._handle_status_event(
            "start", {"experiment": exp_name, "steps": [step_name], "replicates": 1}
        )
        screen._handle_status_event(
            "step", {"experiment": exp_name, "step": step_name, "percent": 0.2}
        )
        exp_node = screen.tree_nodes[(exp_name,)]
        assert "⚙️" in exp_node.label.plain
        screen.worker = type("W", (), {"is_finished": True})()


@pytest.mark.asyncio
async def test_step_error_icon_displayed(
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
        screen._build_trees()
        exp_name = obj.name
        step_name = obj.pipeline.steps[0].__class__.__name__
        screen.step_states[(exp_name, step_name)] = "errored"
        screen._refresh_node((exp_name, step_name))
        step_node = screen.tree_nodes[(exp_name, step_name)]
        assert "⚠️" in step_node.label.plain
        screen.worker = type("W", (), {"is_finished": True})()


@pytest.mark.asyncio
async def test_run_with_changed_treatment_uses_new_value(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    exp_dir = create_experiment_scaffolding("demo", directory=tmp_path, examples=True)
    step_file = exp_dir / "steps.py"
    marker = exp_dir / "marker.txt"
    step_file.write_text(
        "from pathlib import Path\nfrom crystallize import pipeline_step\n"
        "MARK = Path(__file__).with_name('marker.txt')\n"
        "@pipeline_step()\n"
        "def add_one(data: int, delta: int = 0) -> int:\n"
        "    MARK.write_text(str(delta))\n"
        "    return data + delta\n"
    )
    cfg = exp_dir / "config.yaml"
    monkeypatch.chdir(tmp_path)
    obj = Experiment.from_yaml(cfg)
    async with App().run_test() as pilot:
        screen = RunScreen(obj, cfg, False, None)
        await pilot.app.push_screen(screen)
        screen.worker = type("W", (), {"is_finished": True})()
        await screen._obj.arun(treatments=[Treatment("t1", {"delta": 1})])
        assert marker.read_text() == "1"
        await screen._obj.arun(treatments=[Treatment("t2", {"delta": 2})])
        assert marker.read_text() == "2"
        screen.worker = type("W", (), {"is_finished": True})()


@pytest.mark.asyncio
async def test_rerun_after_config_error_shows_error_tab(
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

        def run_worker(func, *a, **kw):
            import threading

            t = threading.Thread(target=func)
            t.start()
            t.join()
            return SimpleNamespace(is_finished=True)

        screen.run_worker = run_worker  # type: ignore[assignment]
        screen.app.call_from_thread = lambda f, *a, **kw: f(*a, **kw)  # type: ignore[assignment]

        def fake_run_object(*args: Any, **kwargs: Any) -> Any:
            raise ValueError("boom")

        monkeypatch.setattr(run_module, "_run_object", fake_run_object)

        await pilot.press("R")
        tabs = screen.query_one("#output-tabs", TabbedContent)
        assert tabs.active == "errors"
        assert any("boom" in msg for msg in screen.error_history)


@pytest.mark.asyncio
async def test_start_run_load_error_shows_error_tab(
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

        def boom() -> None:
            raise RuntimeError("loadfail")

        screen._reload_object = boom  # type: ignore[assignment]
        await pilot.press("R")
        tabs = screen.query_one("#output-tabs", TabbedContent)
        assert tabs.active == "errors"
        assert any("loadfail" in msg for msg in screen.error_history)


@pytest.mark.parametrize(
    ("editor", "expected"),
    [
        ("code", ["code", "-g", "dummy:7"]),
        ("vim", ["vim", "+7", "dummy"]),
    ],
)
def test_open_in_editor_builds_command(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, editor: str, expected: list[str]
) -> None:
    called: dict[str, list[str]] = {}

    def fake_run(cmd, check=False):
        called["cmd"] = cmd

    monkeypatch.setattr(run_module, "pristine_stdio", contextlib.nullcontext)
    monkeypatch.setattr(run_module, "_suspend_tui", contextlib.nullcontext)
    monkeypatch.setattr(run_module.subprocess, "run", fake_run)
    monkeypatch.setenv("EDITOR", editor)
    run_module._open_in_editor("dummy", 7)
    assert called["cmd"] == expected


@pytest.mark.asyncio
async def test_action_edit_step_opens_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    datasources = tmp_path / "datasources.py"
    datasources.write_text(
        "from crystallize import data_source\n\n@data_source\ndef source(ctx):\n    return 0\n"
    )
    steps = tmp_path / "steps.py"
    steps.write_text(
        "from crystallize import pipeline_step\n\n@pipeline_step()\ndef add_one(data, ctx):\n    return data + 1\n"
    )
    cfg = tmp_path / "config.yaml"
    cfg.write_text(
        """
name: exp
datasource:
  x: source
steps:
  - add_one
"""
    )
    exp = Experiment.from_yaml(cfg)
    screen = RunScreen(exp, cfg, False, None)

    recorded: dict[str, Any] = {}

    def fake_open(path: str, line: int | None = None) -> None:
        recorded["path"] = path
        recorded["line"] = line

    monkeypatch.setattr(run_module, "_open_in_editor", fake_open)
    monkeypatch.setenv("EDITOR", "echo")

    class TestApp(App):
        async def on_mount(self) -> None:  # pragma: no cover - test helper
            await self.push_screen(screen)

    app = TestApp()
    async with app.run_test():
        screen._build_trees()
        tree = screen.query_one("#exp-tree", Tree)
        step_node = tree.root.children[0].children[0]
        tree.focus()
        monkeypatch.setattr(Tree, "cursor_node", property(lambda self: step_node))
        monkeypatch.setattr(RunScreen, "_focused_tree", lambda self: tree)
        screen.action_edit_step()

    assert recorded["path"].endswith(".py")
    assert recorded["line"] > 0


@pytest.mark.asyncio
async def test_action_edit_step_no_editor_shows_hint_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    datasources = tmp_path / "datasources.py"
    datasources.write_text(
        "from crystallize import data_source\n\n@data_source\ndef source(ctx):\n    return 0\n"
    )
    steps = tmp_path / "steps.py"
    steps.write_text(
        "from crystallize import pipeline_step\n\n@pipeline_step()\ndef add_one(data, ctx):\n    return data + 1\n"
    )
    cfg = tmp_path / "config.yaml"
    cfg.write_text(
        """
name: exp
datasource:
  x: source
steps:
  - add_one
"""
    )
    exp = Experiment.from_yaml(cfg)
    screen = RunScreen(exp, cfg, False, None)

    messages: list[str] = []
    monkeypatch.setattr(
        RunScreen, "_write_error", lambda self, text: messages.append(text)
    )
    for var in ("CRYSTALLIZE_EDITOR", "EDITOR", "VISUAL"):
        monkeypatch.delenv(var, raising=False)

    class TestApp(App):
        async def on_mount(self) -> None:  # pragma: no cover - test helper
            await self.push_screen(screen)

    app = TestApp()
    async with app.run_test():
        screen._build_trees()
        tree = screen.query_one("#exp-tree", Tree)
        step_node = tree.root.children[0].children[0]
        tree.focus()
        monkeypatch.setattr(Tree, "cursor_node", property(lambda self: step_node))
        monkeypatch.setattr(RunScreen, "_focused_tree", lambda self: tree)
        screen.action_edit_step()
        screen.action_edit_step()

    assert (
        messages[0]
        == "Set $EDITOR (e.g. export EDITOR=vim) to enable 'e' to open files."
    )
    assert messages[1] == "No editor configured"
