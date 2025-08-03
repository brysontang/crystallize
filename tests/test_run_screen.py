from __future__ import annotations

from pathlib import Path
from typing import Any

import importlib
import sys
import time

import pytest

from cli.screens.run import RunScreen, _inject_status_plugin, delete_artifacts, _reload_modules
from cli.status_plugin import CLIStatusPlugin
from cli.utils import create_experiment_scaffolding
from crystallize import data_source, pipeline_step
from crystallize.experiments.experiment import Experiment
from crystallize.pipelines.pipeline import Pipeline
from crystallize.plugins.plugins import ArtifactPlugin
from cli.widgets.writer import WidgetWriter


@data_source
def dummy_source(ctx):
    return 0


@pipeline_step()
def add_one(data, ctx):
    return data + 1


class DummyWidget:
    def write(self, msg):
        pass

    def refresh(self):
        pass


class DummyApp:
    def call_from_thread(self, func, *args, **kwargs):
        func(*args, **kwargs)


def test_delete_artifacts(tmp_path: Path) -> None:
    plugin = ArtifactPlugin(root_dir=str(tmp_path))
    exp = Experiment(datasource=dummy_source(), pipeline=Pipeline([add_one()]), name="e", plugins=[plugin])
    exp.validate()
    path = Path(plugin.root_dir) / "e"
    path.mkdir()
    delete_artifacts(exp)
    assert not path.exists()


def test_inject_status_plugin_adds_experiment(tmp_path: Path) -> None:
    plugin = ArtifactPlugin(root_dir=str(tmp_path))
    exp = Experiment(datasource=dummy_source(), pipeline=Pipeline([add_one()]), name="exp", plugins=[plugin])
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


class StubNode:
    def __init__(self, label: str, data: Any | None = None) -> None:
        self.label = label
        self.data = data
        self.children: list[StubNode] = []

    def add(self, label: str, data: Any | None = None) -> StubNode:
        node = StubNode(label, data)
        self.children.append(node)
        return node

    def set_label(self, label: str) -> None:
        self.label = label

    def expand(self) -> None:  # pragma: no cover - stub
        pass


class StubTree:
    def __init__(self) -> None:
        self.root = StubNode("root")
        self.cursor_node: StubNode | None = None


@pytest.mark.asyncio
async def test_build_tree_and_toggle_cache(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    exp_dir = create_experiment_scaffolding("demo", directory=tmp_path, examples=True)
    cfg = exp_dir / "config.yaml"
    monkeypatch.chdir(tmp_path)
    obj = Experiment.from_yaml(cfg)
    screen = RunScreen(obj, cfg, False, None)
    tree = StubTree()
    screen.query_one = lambda *_args, **_kwargs: tree  # type: ignore[assignment]
    screen._reload_object()
    screen._build_tree()
    exp_name = obj.name
    step_name = obj.pipeline.steps[0].__class__.__name__
    assert (exp_name,) in screen.tree_nodes
    assert (exp_name, step_name) in screen.tree_nodes


@pytest.mark.asyncio
async def test_handle_status_events_updates_state(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    exp_dir = create_experiment_scaffolding("demo", directory=tmp_path, examples=True)
    cfg = exp_dir / "config.yaml"
    monkeypatch.chdir(tmp_path)
    obj = Experiment.from_yaml(cfg)
    screen = RunScreen(obj, cfg, False, None)
    step_name = obj.pipeline.steps[0].__class__.__name__
    screen._handle_status_event("start", {"experiment": "demo", "steps": [step_name], "replicates": 2})
    assert screen.experiment_states["demo"] == "running"
    screen._handle_status_event("replicate", {"experiment": "demo", "replicate": 1, "total": 2, "condition": "t"})
    assert screen.replicate_progress == (1, 2)
    screen._handle_status_event("step", {"experiment": "demo", "step": step_name, "percent": 0.5})
    assert screen.progress_percent == 0.5
    assert "50%" in screen.top_bar
    screen._handle_status_event("step_finished", {"experiment": "demo", "step": step_name})
    assert screen.step_states[("demo", step_name)] == "completed"


def test_run_or_cancel_behaviour(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    exp_dir = create_experiment_scaffolding("demo", directory=tmp_path, examples=True)
    cfg = exp_dir / "config.yaml"
    monkeypatch.chdir(tmp_path)
    obj = Experiment.from_yaml(cfg)
    screen = RunScreen(obj, cfg, False, None)
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


def test_on_experiment_complete_opens_summary(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    exp_dir = create_experiment_scaffolding("demo", directory=tmp_path, examples=True)
    cfg = exp_dir / "config.yaml"
    monkeypatch.chdir(tmp_path)
    obj = Experiment.from_yaml(cfg)
    screen = RunScreen(obj, cfg, False, None)
    opened: list[Any] = []

    def fake_open(res: Any) -> None:
        opened.append(res)

    btn = StubNode("Run")
    screen.query_one = lambda *_a, **_k: btn  # type: ignore[assignment]
    screen.open_summary_screen = fake_open  # type: ignore[assignment]
    message = screen.ExperimentComplete(result=123)
    screen.on_experiment_complete(message)
    assert opened == [123]
    assert screen.worker is None
    assert btn.label == "Run"
