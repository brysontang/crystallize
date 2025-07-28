"""Screen for running experiments and graphs."""

from __future__ import annotations

import asyncio
import shutil
import sys
import traceback
from pathlib import Path
from typing import Any, Callable, List, Tuple
import queue  # Import queue

import networkx as nx
from rich.text import Text
from textual.app import App, ComposeResult
from textual.containers import VerticalScroll, Container
from textual.css.query import NoMatches
from textual.binding import Binding
from textual.message import Message
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, RichLog, Static, TextArea

from crystallize.experiments.experiment import Experiment
from crystallize.experiments.experiment_graph import ExperimentGraph
from crystallize.plugins.plugins import ArtifactPlugin
from ..status_plugin import CLIStatusPlugin
from ..discovery import _run_object
from ..widgets.writer import WidgetWriter
from .delete_data import ConfirmScreen
from .prepare_run import PrepareRunScreen
from .summary import SummaryScreen


def _inject_status_plugin(
    obj: Any, callback: Callable[[str, dict[str, Any]], None]
) -> None:
    """Inject CLIStatusPlugin into experiments if not already present."""
    if isinstance(obj, ExperimentGraph):
        for node in obj._graph.nodes:
            exp: Experiment = obj._graph.nodes[node]["experiment"]
            if exp.get_plugin(CLIStatusPlugin) is None:
                exp.plugins.append(CLIStatusPlugin(callback))
    else:
        if obj.get_plugin(CLIStatusPlugin) is None:
            obj.plugins.append(CLIStatusPlugin(callback))


class RunScreen(Screen):
    """Display live output of a running experiment."""

    class NodeStatusChanged(Message):
        def __init__(self, node_name: str, status: str) -> None:
            self.node_name = node_name
            self.status = status
            super().__init__()

    class ExperimentComplete(Message):
        def __init__(self, result: Any) -> None:
            self.result = result
            super().__init__()

    BINDINGS = [
        Binding("q", "cancel_and_exit", "Close", show=False),
        Binding("ctrl+c", "cancel_and_exit", "Close", show=False),
        Binding("s", "summary", "Summary"),
        Binding("t", "toggle_plain_text", "Toggle Plain Text"),
        Binding("escape", "cancel_and_exit", "Close"),
    ]

    node_states: dict[str, str] = reactive({})
    replicate_info: str = reactive("")
    progress_percent: float = reactive(0.0)
    step_states: dict[str, str] = reactive({})
    treatment_states: dict[str, str] = reactive({})
    plain_text: bool = reactive(False)

    def __init__(self, obj: Any, strategy: str, replicates: int | None) -> None:
        super().__init__()
        self._obj = obj
        self._strategy = strategy
        self._replicates = replicates
        self._result: Any = None
        self.event_queue = queue.Queue()
        self.log_history: list[str] = []

    def watch_node_states(self) -> None:
        if not isinstance(self._obj, ExperimentGraph):
            return
        try:
            dag_widget = self.query_one("#dag-display", Static)
        except NoMatches:
            return

        text = Text(justify="center")
        order = list(nx.topological_sort(self._obj._graph))
        for i, node in enumerate(order):
            status = self.node_states.get(node, "pending")
            style = {
                "completed": "bold green",
                "running": "bold blue",
                "pending": "bold white",
            }.get(status, "bold white")
            text.append(f"[ {node} ]", style=style)
            if i < len(order) - 1:
                text.append(" ⟶  ", style="white")
        dag_widget.update(text)

    def on_node_status_changed(self, message: NodeStatusChanged) -> None:
        self.node_states = {**self.node_states, message.node_name: message.status}

    def watch_treatment_states(self) -> None:
        if not self.treatment_states:
            return
        try:
            treatment_widget = self.query_one("#treatment-display", Static)
        except NoMatches:
            return
        text = Text("Treatments: ", justify="center")
        total_treatments = len(self.treatment_states)
        for i, (name, status) in enumerate(self.treatment_states.items()):
            style = {
                "running": "bold blue",
                "pending": "bold white",
            }.get(status, "bold white")
            text.append(f"{name}", style=style).append(
                f"{' | ' if i < total_treatments - 1 else ''}"
            )
        treatment_widget.update(text)

    def watch_step_states(self) -> None:
        if not self.step_states:
            return
        try:
            step_widget = self.query_one("#step-display", Static)
        except NoMatches:
            return

        text = Text(justify="center")
        steps = list(self.step_states.keys())

        for i, step in enumerate(steps):
            status = self.step_states[step]
            style = {
                "completed": "bold green",
                "running": "bold blue",
                "pending": "bold white",
            }.get(status, "bold white")
            text.append(f"[ {step} ]", style=style)
            if i < len(steps) - 1:
                text.append(" ⟶  ", style="white")
        step_widget.update(text)

    def watch_replicate_info(self) -> None:
        try:
            rep_widget = self.query_one("#replicate-display", Static)
        except NoMatches:
            return
        rep_widget.update(self.replicate_info)

    def watch_progress_percent(self) -> None:
        try:
            prog_widget = self.query_one("#progress-display", Static)
        except NoMatches:
            return
        filled = int(self.progress_percent * 20)
        bar = "[" + "#" * filled + "-" * (20 - filled) + "]"
        prog_widget.update(f"{bar} {self.progress_percent*100:.0f}%")

    def watch_plain_text(self) -> None:
        """Toggles visibility between the RichLog and the plain text TextArea."""
        try:
            log_widget = self.query_one("#live_log", RichLog)
            text_widget = self.query_one("#plain_log", TextArea)
        except NoMatches:
            return

        if self.plain_text:
            # Switched TO plain text mode
            # Join the history and load it into the TextArea
            full_log = "".join(self.log_history)
            text_widget.load_text(full_log)

            # Hide the RichLog and show the TextArea
            log_widget.display = False
            text_widget.display = True
            text_widget.focus()  # Focus the TextArea so it can be scrolled/selected
        else:
            # Switched BACK to rich text mode
            log_widget.display = True
            text_widget.display = False

    def _handle_status_event(self, event: str, info: dict[str, Any]) -> None:
        if event == "start":
            self.step_states = {name: "pending" for name in info.get("steps", [])}
            self.treatment_states = {
                name: "pending" for name in info.get("treatments", [])
            }
            self.progress_percent = 0.0
            self.replicate_info = "Run started"
        elif event == "replicate":
            rep = info.get("replicate", 0)
            total = info.get("total", 0)
            cond = info.get("condition", "")
            # Update treatment states for this replicate
            self.treatment_states = {
                name: "running" if name == cond else "pending"
                for name in self.treatment_states
            }

            self.replicate_info = f"Replicate {rep}/{total}"
            self.step_states = {name: "pending" for name in self.step_states}
        elif event == "step":
            step = info.get("step")
            self.progress_percent = info.get("percent", 0.0)
            if step and step in self.step_states:
                self.step_states = {**self.step_states, step: "running"}
        elif event == "step_finished":
            step = info.get("step")
            if step and step in self.step_states:
                self.step_states = {**self.step_states, step: "completed"}
        elif event == "reset_progress":
            self.progress_percent = 0.0

    def compose(self) -> ComposeResult:
        with VerticalScroll(id="run-container"):
            yield Header(show_clock=True)
            yield Static(f"⚡ Running: {self._obj.name}", id="modal-title")
            yield Static("Run started", id="replicate-display")
            yield Static(id="treatment-display")
            yield Static(id="step-display")
            yield Static(id="progress-display")
            yield Static(id="dag-display", classes="invisible")

            with Container(id="log-viewer"):
                yield RichLog(highlight=True, markup=True, id="live_log")
                yield TextArea(
                    "",
                    read_only=True,
                    show_line_numbers=False,
                    id="plain_log",
                    classes="hidden",
                )

            yield Footer()

    def open_summary_screen(self, result: Any) -> None:
        self.app.push_screen(SummaryScreen(result))

    def process_queue(self) -> None:
        """Polls the queue and processes events from the worker thread."""
        try:
            while not self.event_queue.empty():
                event, info = self.event_queue.get_nowait()
                self._handle_status_event(event, info)
        except queue.Empty:
            pass

    def on_mount(self) -> None:
        if isinstance(self._obj, ExperimentGraph):
            self.node_states = {node: "pending" for node in self._obj._graph.nodes}
            self.query_one("#dag-display").remove_class("invisible")
        log = self.query_one("#live_log", RichLog)

        def queue_callback(event: str, info: dict[str, Any]) -> None:
            """A simple, thread-safe callback that puts events onto a queue."""
            self.event_queue.put((event, info))

        _inject_status_plugin(self._obj, queue_callback)
        self.queue_timer = self.set_interval(1 / 15, self.process_queue)

        async def progress_callback(status: str, name: str) -> None:
            self.app.call_from_thread(
                self.on_node_status_changed, self.NodeStatusChanged(name, status)
            )

        def run_experiment_sync() -> None:
            original_stdout = sys.stdout
            sys.stdout = WidgetWriter(log, self.app, self.log_history)
            result = None
            try:

                async def run_with_callback():
                    if isinstance(self._obj, ExperimentGraph):
                        return await self._obj.arun(
                            strategy=self._strategy,
                            replicates=self._replicates,
                            progress_callback=progress_callback,
                        )
                    else:
                        return await _run_object(
                            self._obj, self._strategy, self._replicates
                        )

                result = asyncio.run(run_with_callback())

            except Exception:
                tb_str = traceback.format_exc()
                print(
                    f"[bold red]An error occurred in the worker:\n{tb_str}[/bold red]"
                )
            finally:
                sys.stdout = original_stdout
                self.app.call_from_thread(
                    self.on_experiment_complete, self.ExperimentComplete(result)
                )

        self.worker = self.run_worker(run_experiment_sync, thread=True)

    def on_experiment_complete(self, message: ExperimentComplete) -> None:
        self.process_queue()  # Process any final messages
        self._result = message.result
        try:
            if self._result is not None:
                self.open_summary_screen(self._result)
        except NoMatches:
            pass

    def on_unmount(self) -> None:
        """Clean up resources when the screen is removed."""
        if hasattr(self, "queue_timer"):
            self.queue_timer.stop()
        if hasattr(self, "worker") and not self.worker.is_finished:
            self.worker.cancel()

    def action_cancel_and_exit(self) -> None:
        self.app.pop_screen()

    def action_toggle_plain_text(self) -> None:
        self.plain_text = not self.plain_text

    def action_summary(self) -> None:
        if self._result is not None:
            self.open_summary_screen(self._result)


async def _launch_run(app: App, obj: Any) -> None:
    selected = obj
    deletable: List[Tuple[str, Path]] = []
    if isinstance(selected, ExperimentGraph):
        for node in selected._graph.nodes:
            exp: Experiment = selected._graph.nodes[node]["experiment"]
            plugin = exp.get_plugin(ArtifactPlugin)
            if not plugin or not exp.name:
                continue
            base = Path(plugin.root_dir) / exp.name
            if base.exists():
                deletable.append((node, base))

    result = await app.push_screen_wait(PrepareRunScreen(deletable))
    if result is None:
        return
    strategy, idxs = result
    paths_to_delete = [deletable[i][1] for i in idxs]
    if paths_to_delete:
        confirm = await app.push_screen_wait(ConfirmScreen(paths_to_delete))
        if not confirm:
            return
        for p in paths_to_delete:
            try:
                shutil.rmtree(p)
            except OSError:
                pass
    await app.push_screen(RunScreen(selected, strategy, None))
