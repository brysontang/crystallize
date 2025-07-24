"""Textual-based CLI for crystallize."""

from __future__ import annotations

import asyncio
import importlib.util
import inspect
import random
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Type


import networkx as nx
from rich.table import Table
from rich.text import Text
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, VerticalScroll
from textual.css.query import NoMatches
from textual.widgets import (
    Button,
    Footer,
    Header,
    ListItem,
    ListView,
    LoadingIndicator,
    OptionList,
    RichLog,
    SelectionList,
    Static,
)
from textual.widgets.selection_list import Selection
from textual.screen import ModalScreen
from textual.message import Message
from textual.reactive import reactive

from crystallize.experiments.experiment import Experiment
from crystallize.experiments.experiment_graph import ExperimentGraph
from crystallize.plugins.plugins import ArtifactPlugin

OBJ_TYPES = {
    "experiment": Experiment,
    "graph": ExperimentGraph,
}

ASCII_ART = r"""
                      _        _ _
   ___ _ __ _   _ ___| |_ __ _| | (_)_______
  / __| '__| | | / __| __/ _` | | | |_  / _ \
 | (__| |  | |_| \__ \ || (_| | | | |/ /  __/
  \___|_|   \__, |___/\__\__,_|_|_|_/___\___|
            |___/
"""

ASCII_ART_2 = r"""
 ▗▄▄▖▗▄▄▖▗▖  ▗▖▗▄▄▖▗▄▄▄▖▗▄▖ ▗▖   ▗▖   ▗▄▄▄▖▗▄▄▄▄▖▗▄▄▄▖
▐▌   ▐▌ ▐▌▝▚▞▘▐▌     █ ▐▌ ▐▌▐▌   ▐▌     █     ▗▞▘▐▌   
▐▌   ▐▛▀▚▖ ▐▌  ▝▀▚▖  █ ▐▛▀▜▌▐▌   ▐▌     █   ▗▞▘  ▐▛▀▀▘
▝▚▄▄▖▐▌ ▐▌ ▐▌ ▗▄▄▞▘  █ ▐▌ ▐▌▐▙▄▄▖▐▙▄▄▖▗▄█▄▖▐▙▄▄▄▖▐▙▄▄▖
"""

ASCII_ART_3 = r"""
┌─┐┬─┐┬ ┬┌─┐┌┬┐┌─┐┬  ┬  ┬┌─┐┌─┐
│  ├┬┘└┬┘└─┐ │ ├─┤│  │  │┌─┘├┤ 
└─┘┴└─ ┴ └─┘ ┴ ┴ ┴┴─┘┴─┘┴└─┘└─┘
"""

ASCII_ART_4 = r"""
  ___  ____  _  _  ____  ____  __   __    __    __  ____  ____ 
 / __)(  _ \( \/ )/ ___)(_  _)/ _\ (  )  (  )  (  )(__  )(  __)
( (__  )   / )  / \___ \  )( /    \/ (_/\/ (_/\ )(  / _/  ) _) 
 \___)(__\_)(__/  (____/ (__)\_/\_/\____/\____/(__)(____)(____)
"""

ASCII_ART_ARRAY = [ASCII_ART, ASCII_ART_2, ASCII_ART_3, ASCII_ART_4]

# Add some CSS styling as a string (could be loaded from a file)
CSS = """
App {
    background: $background;
}

Header {
    background: $accent;
    content-align: center middle;
}

Static#title {
    content-align: center middle;
    text-style: bold;
    color: $primary;
}

ListView {
    background: $panel;
    border: tall $secondary;
    height: 1fr;
}

ListItem {
    padding: 1;
}

ListItem > Static {
    color: $text;
}

ListItem:hover {
    background: $accent;
}

ListItem.selected {
    background: $success;
}

.experiment-item > Static {
}

.graph-item > Static {
    text-style: bold italic;
}

ModalScreen {
    background: $background 50%;
    align: center middle;
}

DeleteDataScreen Container {
    border: round $warning;
    background: $panel;
    width: 80%;
    height: auto;
    padding: 1;
}

.confirm-delete-container {
    width: 80%;
    height: auto;
    max-height: 80%;
    border: round $error;
    background: $panel;
    padding: 1;
}

.path-list {
    background: $surface;
    border: round $primary;
    margin: 1 0;
    padding: 1;
    height: auto;
    max-height: 10; /* Makes the list scrollable if it's long */
}


SelectionList {
    height: 1fr;
    width: 100%;
}

#dag-display {
    height: auto;
    border: round $primary;
    padding: 0 1;
    margin-bottom: 1;
}

RichLog {
    height: 1fr;
    width: 100%;
    background: $panel;
    border: tall $secondary;
}

Button {
    margin: 1 0;
}

Button#confirm {
    background: $error;
}

Button#yes {
    background: $success;
}

Button#no {
    background: $error;
}

LoadingIndicator {
    color: $accent;
}
"""


class WidgetWriter:
    """A thread-safe, file-like object that writes to a RichLog widget and forces a refresh."""

    def __init__(self, widget: RichLog, app: App):
        self.widget = widget
        self.app = app

    def write(self, message: str) -> None:
        if message:
            # Schedule the write operation
            self.app.call_from_thread(self.widget.write, message)
            # CRITICAL: Also schedule a refresh to force the widget to repaint
            self.app.call_from_thread(self.widget.refresh)

    def flush(self) -> None:
        pass

    def isatty(self) -> bool:
        return True


# Discovery helpers copied from the original CLI


def _import_module(file_path: Path, root_path: Path) -> Optional[Any]:
    """Import ``file_path`` as a module relative to ``root_path``."""
    try:
        relative_path = file_path.relative_to(root_path)
    except ValueError:
        spec = importlib.util.spec_from_file_location(file_path.stem, file_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            try:
                spec.loader.exec_module(module)  # type: ignore[arg-type]
                return module
            except Exception:
                return None
        return None

    module_name = ".".join(relative_path.with_suffix("").parts)

    try:
        if str(root_path) not in sys.path:
            sys.path.insert(0, str(root_path))
        return importlib.import_module(module_name)
    except Exception:
        return None


def discover_objects(directory: Path, obj_type: Type[Any]) -> Dict[str, Any]:
    abs_directory = directory.resolve()
    root_path = Path.cwd()
    found: Dict[str, Any] = {}
    for file in abs_directory.rglob("*.py"):
        mod = _import_module(file, root_path)
        if not mod:
            continue
        for name, obj in inspect.getmembers(mod, lambda x: isinstance(x, obj_type)):
            try:
                rel = file.relative_to(root_path)
            except ValueError:
                rel = file
            found[f"{rel}:{name}"] = obj
    return found


async def _run_object(obj: Any, strategy: str, replicates: Optional[int]) -> Any:
    if isinstance(obj, ExperimentGraph):
        return await obj.arun(strategy=strategy, replicates=replicates)
    return await obj.arun(
        strategy=strategy,
        replicates=None,
        treatments=getattr(obj, "treatments", None),
        hypotheses=getattr(obj, "hypotheses", None),
    )


def _build_experiment_table(result: Any) -> Table:
    metrics = result.metrics
    treatments = list(metrics.treatments.keys())
    table = Table(title="Metrics", border_style="bright_magenta", expand=True)
    table.add_column("Metric", style="cyan")
    table.add_column("Baseline", style="magenta")
    for t in treatments:
        table.add_column(t, style="green")
    metric_names = set(metrics.baseline.metrics)
    if not metric_names:
        return None
    for t in treatments:
        metric_names.update(metrics.treatments[t].metrics)
    for name in sorted(metric_names):
        row = [name, str(metrics.baseline.metrics.get(name))]
        for t in treatments:
            row.append(str(metrics.treatments[t].metrics.get(name)))
        table.add_row(*row)
    return table


def _write_experiment_summary(log: RichLog, result: Any) -> None:
    table = _build_experiment_table(result)
    if table:
        log.write(table)
    if result.errors:
        log.write("[bold red]Errors occurred[/]")
        for cond, err in result.errors.items():
            log.write(f"{cond}: {err}")


def _write_summary(log: RichLog, result: Any) -> None:
    if isinstance(result, dict):
        for name, res in result.items():
            has_table = _build_experiment_table(res) is not None
            has_errors = bool(res.errors)

            if has_table or has_errors:
                log.write(Text(name, style="bold underline"))
                _write_experiment_summary(log, res)
    else:
        _write_experiment_summary(log, result)


# Interactive run logic reused from the original CLI


class ActionableSelectionList(SelectionList):
    """A SelectionList that triggers a custom message on Enter."""

    # Define a custom message that this widget can send
    class Submitted(Message):
        def __init__(self, selected: tuple[Any, ...]) -> None:
            self.selected = selected
            super().__init__()

    # Override the default bindings
    BINDINGS = [("enter", "submit", "Submit")]

    def action_submit(self) -> None:
        """Called when the user presses Enter."""
        # Get all selected values that are actual items (integers)
        selected_indices = tuple(
            value for value in self.selected if isinstance(value, int)
        )
        # Post our custom message with the selected items
        self.post_message(self.Submitted(selected_indices))


class DeleteDataScreen(ModalScreen[tuple[int, ...] | None]):
    BINDINGS = [("ctrl+c", "cancel_and_exit", "Cancel")]

    def __init__(self, deletable: List[Tuple[str, Path]]) -> None:
        super().__init__()
        self._deletable = deletable

    def compose(self) -> ComposeResult:
        with Container():
            yield Static(
                "Use space to toggle, enter to confirm.",
                id="modal-title",
            )
            # Use our new ActionableSelectionList instead of the default one
            self.list = ActionableSelectionList()

            # Add the deletable files
            for idx, (name, path) in enumerate(self._deletable):
                self.list.add_option(Selection(f"  {name}: {path}", idx))

            yield self.list

    def on_mount(self) -> None:
        """Set focus to the selection list when the screen is mounted."""
        self.query_one(ActionableSelectionList).focus()

    # Add this new handler for our custom message
    def on_actionable_selection_list_submitted(
        self, message: ActionableSelectionList.Submitted
    ) -> None:
        """Handles when the user presses Enter in the list."""
        self.dismiss(message.selected)

    def action_cancel_and_exit(self) -> None:
        """Called when the user presses Ctrl+C. Closes the modal."""
        self.dismiss(None)

    def action_cancel_and_exit(self) -> None:
        """Called when the user presses Ctrl+C."""
        self.dismiss(None)


class ConfirmScreen(ModalScreen[bool]):
    BINDINGS = [
        ("ctrl+c", "cancel_and_exit", "Cancel"),
        ("y", "confirm_and_exit", "Confirm"),
        ("n", "cancel_and_exit", "Cancel"),
    ]

    def __init__(self, paths_to_delete: list[Path]) -> None:
        super().__init__()
        self._paths = paths_to_delete

    def compose(self) -> ComposeResult:
        with Container(classes="confirm-delete-container"):
            yield Static(
                "[bold red]The following will be permanently deleted:[/bold red]"
            )

            with VerticalScroll(classes="path-list"):
                if not self._paths:
                    yield Static("  (Nothing selected)")
                for path in self._paths:
                    yield Static(f"• {path}")

            yield Static("\nAre you sure you want to proceed? (y/n)")

            yield Horizontal(
                Button("Yes, Delete", variant="error", id="yes"),
                Button("No, Cancel", variant="primary", id="no"),
            )

    def on_mount(self) -> None:
        # Focus the "No" button by default as a safety measure
        self.query_one("#no", Button).focus()

    def action_confirm_and_exit(self) -> None:
        """Called when the user presses y."""
        self.dismiss(True)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "yes")

    def action_cancel_and_exit(self) -> None:
        """Called when the user presses Ctrl+C."""
        self.dismiss(False)  # Ctrl+C is the same as cancelling


class StrategyScreen(ModalScreen[str | None]):
    BINDINGS = [("ctrl+c", "cancel_and_exit", "Cancel")]

    def compose(self) -> ComposeResult:
        with Container():
            yield Static("Execution strategy", id="modal-title")
            self.options = OptionList()
            self.options.add_option(Selection("rerun", "rerun", id="rerun"))
            self.options.add_option(Selection("resume", "resume", id="resume"))
            yield self.options
            yield Button("Cancel", id="cancel")

    def on_option_list_option_selected(
        self, message: OptionList.OptionSelected
    ) -> None:
        self.dismiss(message.option.id)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(None)

    def action_cancel_and_exit(self) -> None:
        """Called when the user presses Ctrl+C."""
        self.dismiss(None)


class SummaryScreen(ModalScreen[None]):
    """A screen to display the summary of a run."""

    BINDINGS = [("ctrl+c", "close", "Close")]

    def __init__(self, result: Any) -> None:
        super().__init__()
        self._result = result

    def compose(self) -> ComposeResult:
        with Container():
            yield Static("Execution Summary", id="modal-title")
            self.log_widget = RichLog()
            yield self.log_widget
            yield Button("Close", id="close")

    async def on_mount(self) -> None:
        _write_summary(self.log_widget, self._result)

    def action_close(self) -> None:
        self.dismiss(None)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(None)


class RunScreen(ModalScreen[None]):
    """A screen to display the live output of a running experiment."""

    class NodeStatusChanged(Message):
        def __init__(self, node_name: str, status: str) -> None:
            self.node_name = node_name
            self.status = status
            super().__init__()

    class ExperimentComplete(Message):
        """Posted when the experiment worker finishes."""

        def __init__(self, result: Any) -> None:
            self.result = result
            super().__init__()

    BINDINGS = [("ctrl+c", "cancel_and_exit", "Cancel and Go Back")]

    node_states: dict[str, str] = reactive({})

    def __init__(self, obj: Any, strategy: str, replicates: int | None) -> None:
        super().__init__()
        self._obj = obj
        self._strategy = strategy
        self._replicates = replicates
        self._result: Any = None
        # DO NOT initialize reactive variables here

    def watch_node_states(self) -> None:
        """Called when the node_states dictionary is updated."""
        if not isinstance(self._obj, ExperimentGraph):
            return

        try:
            dag_widget = self.query_one("#dag-display", Static)
        except NoMatches:
            # This can happen if the watcher is triggered before mount.
            return

        # Build the colored, linear DAG display
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
        """Update the state of a node."""
        self.node_states = {**self.node_states, message.node_name: message.status}

    def compose(self) -> ComposeResult:
        with VerticalScroll(id="run-container"):
            yield Header(show_clock=True)
            yield Static(f"⚡ Running: {self._obj.name}", id="modal-title")
            yield Static(id="dag-display", classes="hidden")
            yield RichLog(highlight=True, markup=True, id="live_log")
            yield Button("Close", id="close_run")

    def open_summary_screen(self, result: Any) -> None:
        self.app.push_screen(SummaryScreen(result))

    def on_mount(self) -> None:
        # Initialize all nodes to "pending". The backend will update their true status.
        if isinstance(self._obj, ExperimentGraph):
            self.node_states = {node: "pending" for node in self._obj._graph.nodes}
            self.query_one("#dag-display").remove_class("hidden")

        log = self.query_one("#live_log", RichLog)

        async def progress_callback(status: str, name: str) -> None:
            self.app.call_from_thread(
                self.on_node_status_changed, self.NodeStatusChanged(name, status)
            )

        def run_experiment_sync() -> None:
            original_stdout = sys.stdout
            sys.stdout = WidgetWriter(log, self.app)
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
            except Exception as e:
                print(f"[bold red]An error occurred in the worker:\n{e}[/bold red]")
            finally:
                sys.stdout = original_stdout
                self.app.call_from_thread(
                    self.on_experiment_complete, self.ExperimentComplete(result)
                )

        self.worker = self.run_worker(run_experiment_sync, thread=True)

    def on_experiment_complete(self, message: ExperimentComplete) -> None:
        """Called when the ExperimentComplete message is received."""
        self._result = message.result
        try:
            # log = self.query_one("#live_log", RichLog)
            if self._result is not None:
                self.open_summary_screen(self._result)

            self.query_one("#close_run").remove_class("hidden")
        except NoMatches:
            pass

    def action_cancel_and_exit(self) -> None:
        if self.worker and not self.worker.is_finished:
            self.worker.cancel()
        self.app.pop_screen()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "close_run":
            self.app.pop_screen()


async def _launch_run(app: App, obj: Any) -> None:
    selected = obj
    # This should only happen if it's an experiment graph
    if isinstance(selected, ExperimentGraph):
        deletable: List[Tuple[str, Path]] = []
        for node in selected._graph.nodes:
            exp: Experiment = selected._graph.nodes[node]["experiment"]
            plugin = exp.get_plugin(ArtifactPlugin)
            if not plugin or not exp.name:
                continue
            base = Path(plugin.root_dir) / exp.name
            if base.exists():
                deletable.append((node, base))

        if deletable:
            idxs = await app.push_screen_wait(DeleteDataScreen(deletable))

            # If the user cancelled or skipped the delete screen, stop here.
            if idxs is None:
                return

            # This part only runs if the user clicked "Confirm".
            if idxs:  # Check if they actually selected anything
                paths_to_delete = [deletable[i][1] for i in idxs]
                confirm = await app.push_screen_wait(ConfirmScreen(paths_to_delete))
                if confirm:
                    for p in paths_to_delete:
                        try:
                            shutil.rmtree(p)
                        except OSError:
                            pass
                else:
                    return  # Stop if they cancel the confirmation

    strategy = await app.push_screen_wait(StrategyScreen())
    if strategy is None:
        return
    await app.push_screen(RunScreen(selected, strategy, None))


class CrystallizeApp(App):
    """Textual application for running crystallize objects."""

    CSS = CSS
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("r", "refresh", "Refresh"),
        ("ctrl+c", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header(show_clock=True)
        yield Static(random.choice(ASCII_ART_ARRAY), id="title")
        with Container(id="main-container"):
            yield LoadingIndicator()
            yield Static("Scanning for experiments and graphs...", id="loading-text")
        yield Footer()

    async def on_mount(self) -> None:
        """Called when the app is mounted. Kicks off discovery."""
        self.run_worker(self._discover)

    def action_refresh(self) -> None:
        """Refresh the app."""
        self.run_worker(self._discover)

    def _discover_sync(self) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Synchronous discovery function to run in a thread."""
        path = Path(".")
        graphs = discover_objects(path, ExperimentGraph)
        experiments = discover_objects(path, Experiment)
        return graphs, experiments

    async def _discover(self) -> None:
        """Discover experiments and graphs and populate the list view."""
        worker = self.run_worker(self._discover_sync, thread=True)
        graphs, experiments = await worker.wait()

        main_container = self.query_one("#main-container")
        await main_container.remove_children()  # Clear "Loading..."

        await main_container.mount(Static("Select an object to run:"))
        list_view = ListView(initial_index=0)
        await main_container.mount(VerticalScroll(list_view))

        for label, obj in graphs.items():
            escaped_label = Text(f"[Graph] {label}")
            item = ListItem(Static(escaped_label), classes="graph-item")
            item.data = {"obj": obj, "type": "Graph"}  # type: ignore
            await list_view.append(item)
        for label, obj in experiments.items():
            escaped_label = Text(f"[Experiment] {label}")
            item = ListItem(Static(escaped_label), classes="experiment-item")
            item.data = {"obj": obj, "type": "Experiment"}  # type: ignore
            await list_view.append(item)

        list_view.focus()

    async def _run_interactive_and_exit(self, obj: Any) -> None:
        """Worker to run the interactive flow and then exit the app."""
        await _launch_run(self, obj)

    async def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        if event.item is not None:
            try:
                type_text = self.query_one("#type-text", Static)
                type_text.update(f"Type: {event.item.data['type']}")
            except NoMatches:
                pass

    async def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle item selection by running the interactive flow in a worker."""
        obj = event.item.data["obj"]  # type: ignore
        self.run_worker(self._run_interactive_and_exit(obj))


def run() -> None:
    CrystallizeApp().run()


if __name__ == "__main__":  # pragma: no cover - manual run
    run()
