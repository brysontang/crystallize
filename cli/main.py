"""Textual-based CLI for crystallize."""

from __future__ import annotations

import asyncio
import importlib.util
import inspect
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple, Type

from rich.table import Table
from rich.text import Text
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import (
    Button,
    Footer,
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
        replicates=replicates,
        treatments=getattr(obj, "treatments", None),
        hypotheses=getattr(obj, "hypotheses", None),
    )


def _build_experiment_table(result: Any) -> Table:
    metrics = result.metrics
    treatments = list(metrics.treatments.keys())
    table = Table(title="Metrics")
    table.add_column("Metric", style="cyan")
    table.add_column("Baseline", style="magenta")
    for t in treatments:
        table.add_column(t, style="green")
    metric_names = set(metrics.baseline.metrics)
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
    log.write(table)
    if result.errors:
        log.write("[bold red]Errors occurred[/]")
        for cond, err in result.errors.items():
            log.write(f"{cond}: {err}")


def _write_summary(log: RichLog, result: Any) -> None:
    if isinstance(result, dict):
        for name, res in result.items():
            log.write(f"[bold underline]{name}[/]")
            _write_experiment_summary(log, res)
    else:
        _write_experiment_summary(log, result)


# Interactive run logic reused from the original CLI


class DeleteDataScreen(ModalScreen[tuple[int, ...] | None]):
    def __init__(self, deletable: List[Tuple[str, Path]]) -> None:
        super().__init__()
        self._deletable = deletable

    def compose(self) -> ComposeResult:
        yield Static("Select data to DELETE (space to toggle)")
        self.list = SelectionList[int]()
        for idx, (name, path) in enumerate(self._deletable):
            # FIX: Wrap the prompt and value in a Selection object
            self.list.add_option(Selection(f"{name}: {path}", idx))
        yield self.list
        yield Horizontal(
            Button("Confirm", id="confirm"),
            Button("Skip", id="skip"),
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "confirm":
            self.dismiss(tuple(self.list.selected))
        else:
            self.dismiss(None)


class ConfirmScreen(ModalScreen[bool]):
    def __init__(self, msg: str) -> None:
        super().__init__()
        self._msg = msg

    def compose(self) -> ComposeResult:
        yield Static(self._msg)
        yield Horizontal(Button("Yes", id="yes"), Button("No", id="no"))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "yes")


class StrategyScreen(ModalScreen[str | None]):
    def compose(self) -> ComposeResult:
        yield Static("Execution strategy")
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


class SummaryScreen(ModalScreen[None]):
    def __init__(self, result: Any) -> None:
        super().__init__()
        self._result = result

    def compose(self) -> ComposeResult:
        self.log_widget = RichLog()
        yield self.log_widget
        yield Button("Close", id="close")

    async def on_mount(self) -> None:
        _write_summary(self.log_widget, self._result)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(None)


async def _run_interactive(app: App, obj: Any) -> None:
    selected = obj
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
            idxs = await app.push_screen(
                DeleteDataScreen(deletable), wait_for_dismiss=True
            )
            if idxs:
                paths_to_delete = [deletable[i][1] for i in idxs]
                confirm = await app.push_screen(
                    ConfirmScreen("\nAre you sure you want to proceed?"),
                    wait_for_dismiss=True,
                )
                if confirm:
                    for p in paths_to_delete:
                        try:
                            shutil.rmtree(p)
                        except OSError:
                            pass
                else:
                    return
    strategy = await app.push_screen(StrategyScreen(), wait_for_dismiss=True)
    if strategy is None:
        return
    result = await _run_object(selected, strategy, None)
    await app.push_screen(SummaryScreen(result), wait_for_dismiss=True)


class CrystallizeApp(App):
    """Textual application for running crystallize objects."""

    BINDINGS = [("q", "quit", "Quit")]

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Static(ASCII_ART)
        yield Container(
            LoadingIndicator(),
            Static("Scanning for experiments and graphs...", id="loading-text"),
            id="main-container",
        )
        yield Footer()

    async def on_mount(self) -> None:
        """Called when the app is mounted. Kicks off discovery."""
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

        list_view = ListView(initial_index=0)
        await main_container.mount(Static("Select an object to run:"))
        await main_container.mount(list_view)

        for label, obj in graphs.items():
            escaped_label = Text(f"[Graph] {label}")
            item = ListItem(Static(escaped_label))
            item.data = {"obj": obj, "type": "Graph"}
            list_view.append(item)
        for label, obj in experiments.items():
            escaped_label = Text(f"[Experiment] {label}")
            item = ListItem(Static(escaped_label))
            item.data = {"obj": obj, "type": "Experiment"}
            list_view.append(item)

        list_view.focus()

    async def _run_interactive_and_exit(self, obj: Any) -> None:
        """Worker to run the interactive flow and then exit the app."""
        await _run_interactive(self, obj)
        self.exit()

    async def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle item selection by running the interactive flow in a worker."""
        obj = event.item.data["obj"]
        self.run_worker(self._run_interactive_and_exit(obj))


def run() -> None:
    CrystallizeApp().run()


if __name__ == "__main__":  # pragma: no cover - manual run
    run()
