"""Screen for running experiments and graphs."""

from __future__ import annotations

import asyncio
import contextlib
import importlib
import inspect
import os
import queue  # Import queue
import subprocess
import sys
import traceback
import time
from collections import deque
from pathlib import Path
from typing import Any, Callable, Dict, List, Iterable
import json

import networkx as nx
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.css.query import NoMatches
from textual.message import Message
from textual.reactive import reactive
from textual.screen import Screen
from textual import on
from textual.widgets import (
    Button,
    Footer,
    Header,
    RichLog,
    Static,
    TabPane,
    TabbedContent,
    TextArea,
    Tree,
)
from rich.console import Console
from rich.text import Text
from rich.style import Style

from crystallize.experiments.experiment import Experiment
from crystallize.experiments.experiment_graph import ExperimentGraph
from crystallize.experiments.result import Result
from crystallize.experiments.result_structs import ExperimentMetrics, TreatmentMetrics
from crystallize.experiments.treatment import Treatment
from crystallize.plugins.plugins import ArtifactPlugin, LoggingPlugin
from crystallize.plugins import load_all_metrics
from crystallize.utils.constants import METADATA_FILENAME
from ..status_plugin import CLIStatusPlugin, TextualLoggingPlugin
from ..discovery import _run_object
from ..widgets.writer import WidgetWriter
from ..utils import _write_summary, format_seconds, generate_xml_summary
from ..yaml_edit import (
    ensure_new_treatment_placeholder,
    find_treatment_line,
    find_treatment_apply_line,
)
from .style.run import CSS


def _inject_status_plugin(
    obj: Any, callback: Callable[[str, dict[str, Any]], None], writer: WidgetWriter
) -> None:
    """Inject CLIStatusPlugin into experiments if not already present."""

    def ensure(exp: Experiment) -> None:
        def wrapped(event: str, info: Dict[str, Any], *, _exp=exp) -> None:
            callback(event, {"experiment": _exp.name, **info})

        if exp.get_plugin(CLIStatusPlugin) is None:
            exp.plugins.append(CLIStatusPlugin(wrapped))
        artifact = exp.get_plugin(ArtifactPlugin)
        if artifact is None:
            exp.plugins.append(ArtifactPlugin(versioned=True))
        else:
            artifact.versioned = True

        exp.plugins = [p for p in exp.plugins if not isinstance(p, LoggingPlugin)]
        exp.plugins.append(TextualLoggingPlugin(writer=writer, verbose=True))

    if isinstance(obj, ExperimentGraph):
        for node in obj._graph.nodes:
            ensure(obj._graph.nodes[node]["experiment"])
    else:
        ensure(obj)


@contextlib.contextmanager
def pristine_stdio():
    """
    Temporarily restore the real stdout / stderr so fork‑/spawn‑based
    child processes don’t inherit custom writers that break fileno().
    """
    saved_out, saved_err = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = sys.__stdout__, sys.__stderr__
    try:
        yield
    finally:
        sys.stdout, sys.stderr = saved_out, saved_err


_ACTIVE_APP: App | None = None


@contextlib.contextmanager
def _suspend_tui(app: App | None = None) -> Iterable[None]:
    """Suspend the Textual application if provided."""
    active = app or _ACTIVE_APP
    if active is not None:
        with active.suspend():
            yield
    else:  # pragma: no cover - fallback when no app available
        yield


def _open_in_editor(path: str, line: int | None = None) -> None:
    """Open ``path`` in the user's configured editor."""
    editor = (
        os.getenv("CRYSTALLIZE_EDITOR")
        or os.getenv("EDITOR")
        or os.getenv("VISUAL")
    )
    if not editor:
        raise RuntimeError("No editor configured")
    import shlex

    line = 1 if line is None else line
    parts = shlex.split(editor)
    prog = parts[0]
    extra_args = parts[1:]
    editor_name = os.path.basename(prog).lower()
    if editor_name.endswith(".exe"):
        editor_name = editor_name[:-4]

    cmd: list[str]
    if editor_name in {"code", "code-insiders", "cursor", "cursor-insiders"}:
        cmd = [prog, "-g", f"{path}:{line}"]
    elif editor_name == "subl":
        cmd = [prog, f"{path}:{line}"]
    elif editor_name.startswith(("pycharm", "charm", "idea", "intellij")):
        cmd = [prog, "--line", str(line), path]
    elif editor_name == "emacsclient":
        cmd = [prog, f"+{line}", path]
    elif editor_name in {"vim", "nvim", "nano", "helix"}:
        cmd = [prog, f"+{line}", path]
    else:
        cmd = [prog, path]
    cmd[1:1] = extra_args

    with pristine_stdio(), _suspend_tui():
        subprocess.run(cmd, check=False)


def _reload_modules(base_path: Path) -> None:
    """Reload modules located under ``base_path``.

    This removes any modules whose ``__file__`` resides inside ``base_path`` and
    invalidates import caches so that subsequent imports load fresh code.
    """
    importlib.invalidate_caches()
    resolved = base_path.resolve()
    for name, module in list(sys.modules.items()):
        file = getattr(module, "__file__", None)
        if not file:
            continue
        try:
            path = Path(file).resolve()
        except OSError:  # pragma: no cover - defensive
            continue
        try:
            is_rel = path.is_relative_to(resolved)
        except ValueError:  # pragma: no cover - py<3.9 safeguard
            is_rel = resolved in path.parents or path == resolved
        if is_rel:
            del sys.modules[name]


class RunScreen(Screen):
    """Display live output of a running experiment."""

    CSS = CSS

    class NodeStatusChanged(Message):
        def __init__(self, node_name: str, status: str) -> None:
            self.node_name = node_name
            self.status = status
            super().__init__()

    class ExperimentComplete(Message):
        def __init__(self, result: Any, error: str | None = None) -> None:
            self.result = result
            self.error = error
            super().__init__()

    BINDINGS = [
        Binding("q", "cancel_and_exit", "Close", show=False),
        Binding("ctrl+c", "cancel_and_exit", "Close", show=False),
        Binding("S", "summary", "Summary"),
        Binding("t", "toggle_plain_text", "Toggle Plain Text"),
        Binding("l", "toggle_cache", "Toggle Cache"),
        Binding("R", "run_or_cancel", "Run"),
        Binding("escape", "cancel_and_exit", "Close"),
        Binding("e", "edit_selected_node", "Edit"),
        Binding("x", "toggle_treatment", "Toggle Treatment"),
    ]

    plain_text: bool = reactive(False)
    progress_percent: float = reactive(0.0)
    eta_remaining: str = reactive("--")
    top_bar: str = reactive("")

    def __init__(
        self, obj: Any, cfg_path: Path, is_graph: bool, replicates: int | None
    ) -> None:
        super().__init__()
        self._obj = obj
        self._cfg_path = Path(cfg_path)
        self._is_graph = is_graph
        self._replicates = replicates
        self._result: Any = None
        self.event_queue: queue.Queue[tuple[str, dict[str, Any]]] = queue.Queue()
        self.log_history: list[str] = []
        self.error_history: list[str] = []
        self._progress_history: deque[tuple[float, float]] = deque(maxlen=5)
        self._current_step: str | None = None
        self._step_start: float | None = None
        self.worker: Any | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._task: asyncio.Task[Any] | None = None
        self.cancel_timer: Any | None = None
        self._inactive_treatments: set[str] = set()
        self._reset_state()
        self._editor_hint_shown = False

    def _reset_state(self) -> None:
        self.experiment_states: Dict[str, str] = {}
        self.experiment_cacheable: Dict[str, bool] = {}
        self.step_states: Dict[tuple[str, str], str] = {}
        self.step_cacheable: Dict[tuple[str, str], bool] = {}
        self.tree_nodes: Dict[tuple[str, ...], Any] = {}
        self._experiments: list[Experiment] = []
        self._exp_map: Dict[str, Experiment] = {}
        self._all_treatments: list[Treatment] = []
        self._all_treatments_map: Dict[str, list[Treatment]] = {}
        self.replicate_progress: tuple[int, int] = (0, 0)
        self.current_treatment: str = ""
        self.current_experiment: str = ""
        self.progress_percent = 0.0
        self.eta_remaining = "--"
        self.top_bar = ""
        self.summary_plain_text = ""
        self._update_top_bar()

    async def on_mount(self) -> None:  # pragma: no cover - UI loop
        self._setup_ui()

    def _format_label(self, name: str, state: str, cacheable: bool) -> str:
        state_icon = {
            "pending": "⏳",
            "running": "⚙️",
            "completed": "✅",
            "errored": "⚠️",
        }.get(state, "⏳")
        cache_icon = "🔒" if cacheable else " "
        return f"{state_icon} {cache_icon} {name}"

    def _refresh_node(self, path: tuple[str, ...]) -> None:
        node = self.tree_nodes.get(path)
        if not node:
            return
        if path[0] == "treatment":
            name = path[1]
            color = "green" if name not in self._inactive_treatments else "red"
            node.set_label(Text(name, style=color))
            return
        if len(path) == 1:
            name = path[0]
            label = self._format_label(
                name,
                self.experiment_states.get(name, "pending"),
                self.experiment_cacheable.get(name, True),
            )
        else:
            exp, step = path
            label = self._format_label(
                step,
                self.step_states.get((exp, step), "pending"),
                self.step_cacheable.get((exp, step), True),
            )
        node.set_label(label)

    def _build_trees(self) -> None:
        exp_tree = self.query_one("#exp-tree", Tree)
        treat_tree = self.query_one("#treatment-tree", Tree)
        exp_tree.root.remove_children()
        treat_tree.root.remove_children()
        self.tree_nodes.clear()
        if isinstance(self._obj, ExperimentGraph):
            order = list(nx.topological_sort(self._obj._graph))
            exps = [self._obj._graph.nodes[n]["experiment"] for n in order]
        else:
            exps = [self._obj]
        self._experiments = exps
        self._exp_map = {exp.name: exp for exp in exps}
        for exp in exps:
            self.experiment_states[exp.name] = "pending"
            self.experiment_cacheable.setdefault(exp.name, True)
            exp_node = exp_tree.root.add(
                self._format_label(
                    exp.name, "pending", self.experiment_cacheable.get(exp.name, True)
                ),
                data=("exp", exp.name, exp),
            )
            self.tree_nodes[(exp.name,)] = exp_node
            for step in exp.pipeline.steps:
                name = step.__class__.__name__
                key = (exp.name, name)
                self.step_states[key] = "pending"
                cacheable = self.step_cacheable.get(key, step.cacheable)
                self.step_cacheable[key] = cacheable
                step.cacheable = cacheable
                node = exp_node.add(
                    self._format_label(name, "pending", cacheable),
                    data=("step", exp.name, name, step),
                    allow_expand=False,
                )
                self.tree_nodes[(exp.name, name)] = node
        for t in self._all_treatments:
            color = "green" if t.name not in self._inactive_treatments else "red"
            t_node = treat_tree.root.add(
                Text(t.name, style=color),
                data=("treatment", t.name, t),
            )
            self.tree_nodes[("treatment", t.name)] = t_node
            for k, v in t.apply_map.items():
                t_node.add(
                    Text(f"{k}: {v}"),
                    data=("ctx", t.name, k),
                    allow_expand=False,
                )
        treat_tree.root.add("[+ add treatment]", data=("add_treatment",))
        exp_tree.root.expand()
        treat_tree.root.expand()
        self._mark_cached_completion(exps)
        exp_tree.focus()

    @on(Tree.NodeHighlighted, "#treatment-tree")
    def _on_treatment_highlighted(self, event: Tree.NodeHighlighted) -> None:
        tree = event.control
        node = event.node
        if node.data and node.data[0] == "treatment":
            name = node.data[1]
            color = "red3" if name in self._inactive_treatments else "green3"
            tree.highlight_style = Style(color=color)
        else:
            tree.highlight_style = None

    def _mark_cached_completion(self, exps: List[Experiment]) -> None:
        for exp in exps:
            if not self.experiment_cacheable.get(exp.name, True):
                continue
            plugin = exp.get_plugin(ArtifactPlugin)
            if plugin is None:
                continue
            exp_dir = exp.name or exp.id
            version = getattr(plugin, "version", None)
            if version is None:
                base_dir = Path(plugin.root_dir) / exp_dir
                versions = [
                    int(p.name[1:])
                    for p in base_dir.glob("v*")
                    if p.name.startswith("v") and p.name[1:].isdigit()
                ]
                version = max(versions, default=0)
            meta_path = (
                Path(plugin.root_dir) / exp_dir / f"v{version}" / METADATA_FILENAME
            )
            if meta_path.exists():
                self.experiment_states[exp.name] = "completed"
                for step in exp.pipeline.steps:
                    name = step.__class__.__name__
                    self.step_states[(exp.name, name)] = "completed"
                    self._refresh_node((exp.name, name))
                self._refresh_node((exp.name,))

    def _focused_tree(self) -> Tree | None:
        treat_tree = self.query_one("#treatment-tree", Tree)
        exp_tree = self.query_one("#exp-tree", Tree)
        if treat_tree.has_focus:
            return treat_tree
        if exp_tree.has_focus:
            return exp_tree
        return None

    def _reload_object(self) -> None:
        _reload_modules(self._cfg_path.parent)
        state_path = self._cfg_path.with_suffix(".state.json")
        data = {}
        if state_path.exists():
            try:
                data = json.loads(state_path.read_text())
            except (OSError, ValueError) as exc:
                self._write_error(f"Failed to parse {state_path.name}: {exc}")
        self._inactive_treatments = set(data.get("inactive_treatments", []))
        if self._is_graph:
            self._obj = ExperimentGraph.from_yaml(self._cfg_path)
            exps = [self._obj._graph.nodes[n]["experiment"] for n in self._obj._graph]
        else:
            self._obj = Experiment.from_yaml(self._cfg_path)
            exps = [self._obj]
        self._all_treatments = []
        self._all_treatments_map = {}
        for exp in exps:
            self._all_treatments.extend(exp.treatments)
            self._all_treatments_map[exp.name] = list(exp.treatments)
            exp.treatments = [
                t for t in exp.treatments if t.name not in self._inactive_treatments
            ]
        self._experiments = exps

    def _write_error(self, text: str) -> None:
        error_log = self.query_one("#error_log", RichLog)
        error_log.write(f"[bold red]{text}[/bold red]")
        self.error_history.append(text)

    def _start_run(self) -> None:
        exp_tree = self.query_one("#exp-tree", Tree)
        treat_tree = self.query_one("#treatment-tree", Tree)
        exp_tree.root.remove_children()
        treat_tree.root.remove_children()
        prev_exp_cache = self.experiment_cacheable.copy()
        prev_step_cache = self.step_cacheable.copy()
        self._reset_state()
        self.experiment_cacheable.update(prev_exp_cache)
        self.step_cacheable.update(prev_step_cache)
        run_btn = self.query_one("#run-btn", Button)
        error_widget = self.query_one("#error_log", RichLog)
        error_widget.clear()
        self.error_history.clear()
        try:
            self._reload_object()
            self._build_trees()
            self._build_artifacts()
        except Exception:
            tb_str = traceback.format_exc()
            self._write_error(tb_str)
            tabs = self.query_one("#output-tabs", TabbedContent)
            tabs.active = "errors"
            run_btn.label = "Run"
            return
        tabs = self.query_one("#output-tabs", TabbedContent)
        log_widget = self.query_one("#live_log", RichLog)
        log_widget.clear()
        summary_log = self.query_one("#summary_log", RichLog)
        summary_log.clear()
        summary_plain = self.query_one("#summary_plain", TextArea)
        summary_plain.load_text("")
        self.summary_plain_text = ""
        writer = WidgetWriter(log_widget, self.app, self.log_history)

        def queue_callback(event: str, info: dict[str, Any]) -> None:
            self.event_queue.put((event, info))

        _inject_status_plugin(self._obj, queue_callback, writer=writer)

        async def progress_callback(status: str, name: str) -> None:
            self.app.call_from_thread(
                self.on_node_status_changed, self.NodeStatusChanged(name, status)
            )

        def run_experiment_sync() -> None:
            result = None
            error: str | None = None
            try:
                async def run_with_callback():
                    with pristine_stdio():
                        if isinstance(self._obj, ExperimentGraph):
                            return await self._obj.arun(
                                strategy=None,
                                replicates=self._replicates,
                                progress_callback=progress_callback,
                            )
                        else:
                            return await _run_object(self._obj, None, self._replicates)

                self._loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._loop)
                self._task = self._loop.create_task(run_with_callback())
                result = self._loop.run_until_complete(self._task)
            except asyncio.CancelledError:
                pass
            except Exception:
                error = traceback.format_exc()
                print(f"[bold red]An error occurred in the worker:\n{error}[/bold red]")
            finally:
                if self._loop is not None:
                    self._loop.run_until_complete(self._loop.shutdown_asyncgens())
                    asyncio.set_event_loop(None)
                    self._loop.close()
                    self._loop = None
                    self._task = None
                self.app.call_from_thread(
                    self.on_experiment_complete,
                    self.ExperimentComplete(result, error),
                )

        self.worker = self.run_worker(run_experiment_sync, thread=True)
        run_btn.label = "Cancel"

    def _handle_status_event(self, event: str, info: dict[str, Any]) -> None:
        exp_name = info.get("experiment", "")
        if event == "start":
            self.current_experiment = exp_name
            self.experiment_states[exp_name] = "running"
            for step in info.get("steps", []):
                self.step_states[(exp_name, step)] = "pending"
                self._refresh_node((exp_name, step))
            self._refresh_node((exp_name,))
            self.replicate_progress = (0, info.get("replicates", 0))
        elif event == "replicate":
            rep = info.get("replicate", 0)
            total = info.get("total", 0)
            cond = info.get("condition", "")
            self.replicate_progress = (rep, total)
            self.current_treatment = cond
            exp = self._exp_map.get(self.current_experiment)
            if exp:
                for step in exp.pipeline.steps:
                    name = step.__class__.__name__
                    self.step_states[(exp.name, name)] = "pending"
                    self._refresh_node((exp.name, name))
                self.experiment_states[exp.name] = "running"
                self._refresh_node((exp.name,))
            self.progress_percent = 0.0
            self._progress_history.clear()
            self._current_step = None
            self._step_start = None
            self.eta_remaining = "--"
        elif event == "step":
            step = info.get("step")
            percent = float(info.get("percent", 0.0))
            now = time.perf_counter()
            if step != self._current_step:
                self._current_step = step
                self._progress_history.clear()
                self._step_start = now
            self._progress_history.append((now, percent))
            eta_seconds = None
            if len(self._progress_history) >= 2 and percent > 0:
                first_t, first_p = self._progress_history[0]
                dt = now - first_t
                dp = percent - first_p
                if dt > 0 and dp > 0:
                    rate = dp / dt
                    eta_seconds = (1.0 - percent) / rate
            if eta_seconds is not None and eta_seconds >= 0:
                self.eta_remaining = format_seconds(eta_seconds)
            else:
                self.eta_remaining = "--"
            self.progress_percent = percent
            if step:
                self.step_states[(exp_name, step)] = "running"
                self._refresh_node((exp_name, step))
        elif event == "step_finished":
            step = info.get("step")
            if step:
                self.step_states[(exp_name, step)] = "completed"
                self._refresh_node((exp_name, step))
            self._current_step = None
            self._progress_history.clear()
            self._step_start = None
            self.eta_remaining = "--"
        elif event == "reset_progress":
            self.progress_percent = 0.0
            self._progress_history.clear()
            self._step_start = time.perf_counter()

        self._update_top_bar()

    def _update_top_bar(self) -> None:
        rep, total = self.replicate_progress
        filled = int(self.progress_percent * 20)
        bar = "[" + "#" * filled + "-" * (20 - filled) + "]"
        self.top_bar = (
            f"Experiment: {self.current_experiment or '--'} │ "
            f"Replicate: {rep}/{total} │ Treatment: {self.current_treatment or '--'} │ "
            f"Current Step Progress: {bar} {self.progress_percent*100:.0f}% (~{self.eta_remaining})"
        )

    def watch_top_bar(self) -> None:
        try:
            self.query_one("#top-bar", Static).update(self.top_bar)
        except NoMatches:
            return

    def watch_plain_text(self) -> None:  # pragma: no cover - UI behaviour
        try:
            log_widget = self.query_one("#live_log", RichLog)
            text_widget = self.query_one("#plain_log", TextArea)
            summary_widget = self.query_one("#summary_log", RichLog)
            summary_plain = self.query_one("#summary_plain", TextArea)
            error_widget = self.query_one("#error_log", RichLog)
            error_plain = self.query_one("#error_plain", TextArea)
            llm_widget = self.query_one("#llm_xml_output", TextArea)
            tabs = self.query_one("#output-tabs", TabbedContent)
        except NoMatches:
            return

        if self.plain_text:
            full_log = "".join(self.log_history)
            text_widget.load_text(full_log)
            summary_plain.load_text(self.summary_plain_text)
            error_plain.load_text("".join(self.error_history))
            log_widget.display = False
            text_widget.display = True
            summary_widget.display = False
            summary_plain.display = True
            error_widget.display = False
            error_plain.display = True
            if tabs.active == "summary":
                summary_plain.focus()
            elif tabs.active == "logs":
                text_widget.focus()
            elif tabs.active == "llm_data":
                llm_widget.focus()
            else:
                error_plain.focus()
        else:
            log_widget.display = True
            text_widget.display = False
            summary_widget.display = True
            summary_plain.display = False
            error_widget.display = True
            error_plain.display = False
            if tabs.active == "summary":
                summary_widget.focus()
            elif tabs.active == "logs":
                log_widget.focus()
            elif tabs.active == "llm_data":
                llm_widget.focus()
            else:
                error_widget.focus()

    def _build_artifacts(self) -> None:
        experiments = getattr(self, "_experiments", []) or (
            [self._obj]
            if not isinstance(self._obj, ExperimentGraph)
            else [
                self._obj._graph.nodes[n]["experiment"] for n in self._obj._graph.nodes
            ]
        )
        for exp in experiments:
            cacheable = self.experiment_cacheable.get(exp.name, True)
            exp.strategy = "resume" if cacheable else "rerun"
        self._mark_cached_completion(experiments)

    def compose(self) -> ComposeResult:  # pragma: no cover - UI layout
        yield Header(show_clock=True)
        yield Static(id="top-bar")
        with Horizontal(id="main-area"):
            with Vertical(id="sidebar"):
                yield Static("Experiments", id="exp-header")
                yield Tree("", id="exp-tree")
                yield Static("Treatments", id="treat-header")
                yield Tree("", id="treatment-tree")
                yield Button("Run", id="run-btn")
            with TabbedContent(initial="logs", id="output-tabs"):
                with TabPane("Logs", id="logs"):
                    yield RichLog(highlight=True, markup=True, id="live_log")
                    yield TextArea(
                        "",
                        read_only=True,
                        show_line_numbers=False,
                        id="plain_log",
                        classes="hidden",
                    )
                with TabPane("Summary", id="summary"):
                    yield RichLog(highlight=True, markup=True, id="summary_log")
                    yield TextArea(
                        "",
                        read_only=True,
                        show_line_numbers=False,
                        id="summary_plain",
                        classes="hidden",
                    )
                with TabPane("LLM Data", id="llm_data"):
                    yield TextArea(
                        "",
                        read_only=True,
                        show_line_numbers=False,
                        id="llm_xml_output",
                    )
                with TabPane("Errors", id="errors"):
                    yield RichLog(highlight=True, markup=True, id="error_log")
                    yield TextArea(
                        "",
                        read_only=True,
                        show_line_numbers=False,
                        id="error_plain",
                        classes="hidden",
                    )
        yield Footer()

    def render_summary(
        self,
        result: Any,
        highlight: str | None = None,
        *,
        all_treatments: bool = False,
    ) -> None:
        summary_log = self.query_one("#summary_log", RichLog)
        summary_log.clear()
        experiments = getattr(self, "_experiments", [])

        def enrich(exp: Experiment, res: Result) -> Result:
            plugin = exp.get_plugin(ArtifactPlugin)
            if plugin is None:
                return res
            exp_dir = Path(plugin.root_dir) / (exp.name or exp.id)
            if all_treatments:
                version, baseline, treatment_map = load_all_metrics(exp_dir)
                if version < 0:
                    return res
                metrics = ExperimentMetrics(
                    baseline=TreatmentMetrics(baseline),
                    treatments={
                        f"{n} (v{ver})": TreatmentMetrics(m)
                        for n, (ver, m) in treatment_map.items()
                    },
                    hypotheses=res.metrics.hypotheses,
                )
            else:
                version = getattr(plugin, "version", 0)
                metrics = ExperimentMetrics(
                    baseline=TreatmentMetrics(res.metrics.baseline.metrics),
                    treatments={
                        f"{n} (v{version})": TreatmentMetrics(m.metrics)
                        for n, m in res.metrics.treatments.items()
                    },
                    hypotheses=res.metrics.hypotheses,
                )
            return Result(
                metrics=metrics,
                artifacts=res.artifacts,
                errors=res.errors,
                provenance=res.provenance,
            )

        if isinstance(result, dict):
            enriched: dict[str, Result] = {}
            for name, res in result.items():
                exp = next((e for e in experiments if e.name == name), self._obj)
                enriched[name] = enrich(exp, res)
            out_obj: Any = enriched
        else:
            exp = experiments[0] if experiments else self._obj
            out_obj = enrich(exp, result)

        highlight_label: str | None = None
        if highlight:
            targets = out_obj.values() if isinstance(out_obj, dict) else [out_obj]
            for res in targets:
                match = next(
                    (k for k in res.metrics.treatments if k.startswith(highlight)),
                    None,
                )
                if match:
                    highlight_label = match
                    break

        _write_summary(
            summary_log,
            out_obj,
            highlight=highlight_label,
            inactive=self._inactive_treatments,
        )

        console = Console(record=True)

        class _Writer:
            def write(self, renderable: Any) -> None:
                console.print(renderable)

        writer = _Writer()
        _write_summary(
            writer,
            out_obj,
            highlight=highlight_label,
            inactive=self._inactive_treatments,
        )
        xml_output = generate_xml_summary(out_obj)
        self.query_one("#llm_xml_output", TextArea).load_text(xml_output)
        self.summary_plain_text = console.export_text()
        summary_plain = self.query_one("#summary_plain", TextArea)
        summary_plain.load_text(self.summary_plain_text)
        self.watch_plain_text()

    def process_queue(self) -> None:
        try:
            while not self.event_queue.empty():
                event, info = self.event_queue.get_nowait()
                self._handle_status_event(event, info)
        except queue.Empty:
            pass

    def action_run_or_cancel(self) -> None:
        run_btn = self.query_one("#run-btn", Button)
        if self.worker and not self.worker.is_finished:
            if run_btn.label == "Force Stop (unsafe)":
                self._write_error("Cancellation is taking too long; force stop is unsafe.")
                return
            if self._loop and self._task:
                self._loop.call_soon_threadsafe(self._task.cancel)
            run_btn.label = "Canceling..."
            start = time.perf_counter()

            def check_cancel() -> None:
                if not self.worker or self.worker.is_finished:
                    run_btn.label = "Run"
                    if self.cancel_timer:
                        self.cancel_timer.stop()
                    self.worker = None
                elif time.perf_counter() - start > 5:
                    run_btn.label = "Force Stop (unsafe)"
                    self._write_error(
                        "Cancellation did not complete; stopping forcefully is unsafe."
                    )
                    if self.cancel_timer:
                        self.cancel_timer.stop()

            self.cancel_timer = self.set_interval(0.1, check_cancel)
            return
        self._start_run()

    def _setup_ui(self) -> None:
        self._reload_object()
        exp_tree = self.query_one("#exp-tree", Tree)
        treat_tree = self.query_one("#treatment-tree", Tree)
        exp_tree.show_root = False
        treat_tree.show_root = False
        self._build_trees()
        self.queue_timer = self.set_interval(1 / 15, self.process_queue)

    def on_node_status_changed(self, message: NodeStatusChanged) -> None:
        self.experiment_states[message.node_name] = message.status
        self._refresh_node((message.node_name,))

    def on_experiment_complete(self, message: ExperimentComplete) -> None:
        self.process_queue()
        self._result = message.result
        run_btn = self.query_one("#run-btn", Button)
        run_btn.label = "Run"
        self.worker = None
        if message.error:
            try:
                self.error_history.append(message.error)
                self._write_error(message.error)
                tabs = self.query_one("#output-tabs", TabbedContent)
                tabs.active = "errors"
            except NoMatches:
                pass
            return
        try:
            if self._result is not None:
                self.render_summary(self._result)
                tabs = self.query_one("#output-tabs", TabbedContent)

                def activate_summary() -> None:
                    try:
                        from textual.widgets._tabbed_content import ContentTabs

                        tabs_widget = tabs.get_child_by_type(ContentTabs)
                        summary_tab = next(
                            t
                            for t in tabs_widget.query("Tab")
                            if "summary" in (t.id or "")
                        )
                        tabs_widget._activate_tab(summary_tab)  # type: ignore[attr-defined]
                        tabs.active = "summary"
                    except Exception:  # pragma: no cover - fallback for older Textual
                        tabs._active = "summary"  # type: ignore[attr-defined]
                        tabs.active = "summary"

                self.call_after_refresh(activate_summary)
                tabs.active = "summary"
                for exp in self._experiments:
                    self.experiment_states[exp.name] = "completed"
                    for step in exp.pipeline.steps:
                        name = step.__class__.__name__
                        self.step_states[(exp.name, name)] = "completed"
                        self._refresh_node((exp.name, name))
                    self._refresh_node((exp.name,))
        except NoMatches:
            pass

    def on_unmount(self) -> None:  # pragma: no cover - cleanup
        if hasattr(self, "queue_timer"):
            self.queue_timer.stop()
        if getattr(self, "worker", None) is not None and not self.worker.is_finished:
            if self._loop and self._task:
                self._loop.call_soon_threadsafe(self._task.cancel)
            self.worker.cancel()

    def action_cancel_and_exit(self) -> None:
        self.app.pop_screen()

    def action_toggle_plain_text(self) -> None:
        self.plain_text = not self.plain_text

    def action_toggle_cache(self) -> None:
        """Toggle caching for the selected experiment or step."""

        tree = self.query_one("#exp-tree", Tree)
        if not tree.has_focus:
            return
        node = tree.cursor_node
        if node is None or not node.data:
            return
        data = node.data
        if data[0] == "exp":
            exp_name = data[1]
            self.experiment_cacheable[exp_name] = not self.experiment_cacheable.get(
                exp_name, True
            )
            self._refresh_node((exp_name,))
        elif data[0] == "step":
            exp_name, step_name, step_obj = data[1], data[2], data[3]
            new_val = not self.step_cacheable.get((exp_name, step_name), True)
            self.step_cacheable[(exp_name, step_name)] = new_val
            step_obj.cacheable = new_val
            self._refresh_node((exp_name, step_name))

    def action_toggle_treatment(self) -> Text | None:
        """Toggle active state for the selected treatment and persist it."""

        tree = self.query_one("#treatment-tree", Tree)
        node = tree.cursor_node
        if not node or not node.data or node.data[0] != "treatment":
            return None
        name = node.data[1]
        if name in self._inactive_treatments:
            self._inactive_treatments.remove(name)
            active = True
        else:
            self._inactive_treatments.add(name)
            active = False
        color = "green" if active else "red"
        label = Text(name, style=color)
        node.set_label(label)
        tree.highlight_style = Style(color="green3" if active else "red3")
        state_path = self._cfg_path.with_suffix(".state.json")
        with state_path.open("w") as f:
            json.dump({"inactive_treatments": sorted(self._inactive_treatments)}, f)
        return label

    def action_edit_selected_node(self) -> None:
        global _ACTIVE_APP
        tree = self._focused_tree()
        if tree is None:
            return
        node = tree.cursor_node
        if not node or not node.data:
            return

        kind = node.data[0]

        if kind == "step":
            # Existing step edit logic
            step_obj = node.data[3]
            path = getattr(step_obj, "__orig_source__", None)
            line = getattr(step_obj, "__orig_lineno__", None)

            if path is None:
                cls = step_obj.__class__
                path = inspect.getsourcefile(cls)
                line = inspect.getsourcelines(cls)[1]

            try:
                _ACTIVE_APP = self.app
                _open_in_editor(path, line)
            except RuntimeError as exc:
                self._show_editor_hint(str(exc))
            finally:
                _ACTIVE_APP = None

        elif kind == "exp":
            exp_name = node.data[1]
            path = str(self._cfg_path)
            line = self._find_yaml_line(exp_name)

            try:
                _ACTIVE_APP = self.app
                _open_in_editor(path, line)
            except RuntimeError as exc:
                self._show_editor_hint(str(exc))
            finally:
                _ACTIVE_APP = None

        elif kind == "treatment":
            t_name = node.data[1]
            path = str(self._cfg_path)
            line = find_treatment_line(self._cfg_path, t_name)
            try:
                _ACTIVE_APP = self.app
                _open_in_editor(path, line)
            except RuntimeError as exc:
                self._show_editor_hint(str(exc))
            finally:
                _ACTIVE_APP = None
        elif kind == "ctx":
            t_name = node.data[1]
            key = node.data[2]
            path = str(self._cfg_path)
            line = find_treatment_apply_line(self._cfg_path, t_name, key)
            try:
                _ACTIVE_APP = self.app
                _open_in_editor(path, line)
            except RuntimeError as exc:
                self._show_editor_hint(str(exc))
            finally:
                _ACTIVE_APP = None

        elif kind == "add_treatment":
            path = str(self._cfg_path)
            line = ensure_new_treatment_placeholder(self._cfg_path)
            try:
                _ACTIVE_APP = self.app
                _open_in_editor(path, line)
            except RuntimeError as exc:
                self._show_editor_hint(str(exc))
            finally:
                _ACTIVE_APP = None

    def action_edit_step(self) -> None:
        """Backward compatible alias for editing the selected node."""
        self.action_edit_selected_node()

    def _show_editor_hint(self, message: str) -> None:
        """Display a helpful hint when no editor is configured."""
        if not self._editor_hint_shown:
            self._write_error(
                "Set $EDITOR (e.g. export EDITOR=vim) to enable 'e' to open files."
            )
            self._editor_hint_shown = True
        self._write_error(message)

    def _find_yaml_line(self, experiment_name: str) -> int:
        """Find the line number where the experiment is defined in the YAML."""
        try:
            with open(self._cfg_path, "r") as f:
                for i, line in enumerate(f, start=1):
                    if line.strip().startswith(f"{experiment_name}:"):
                        return i
        except Exception:
            pass
        return 1  # fallback to top of file

    def action_summary(self) -> None:
        tree = self.query_one("#treatment-tree", Tree)
        node = tree.cursor_node
        selected = (
            node.data[1] if node and node.data and node.data[0] == "treatment" else None
        )
        if self._result is not None:
            self.render_summary(self._result, selected, all_treatments=True)
        tabs = self.query_one("#output-tabs", TabbedContent)

        def activate_summary() -> None:
            try:
                from textual.widgets._tabbed_content import ContentTabs

                tabs_widget = tabs.get_child_by_type(ContentTabs)
                summary_tab = next(
                    t for t in tabs_widget.query("Tab") if "summary" in (t.id or "")
                )
                tabs_widget._activate_tab(summary_tab)  # type: ignore[attr-defined]
                tabs.active = "summary"
            except Exception:  # pragma: no cover - fallback for older Textual
                tabs._active = "summary"  # type: ignore[attr-defined]
                tabs.active = "summary"

        self.call_after_refresh(activate_summary)
        tabs.active = "summary"

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "run-btn":
            self.action_run_or_cancel()


async def _launch_run(app: App, obj: Any, cfg_path: Path, is_graph: bool) -> None:
    await app.push_screen(RunScreen(obj, cfg_path, is_graph, None))
