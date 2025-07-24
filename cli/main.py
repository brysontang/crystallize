"""Textual-based CLI for crystallize."""

from __future__ import annotations

import asyncio
import importlib.util
import inspect
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple, Type

from rich.console import Console
from rich.markup import escape
from rich.table import Table
from rich.text import Text
from simple_term_menu import TerminalMenu
from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import Footer, ListItem, ListView, LoadingIndicator, Static

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


def _select_from_menu(options: Sequence[str], title: str) -> Optional[int]:
    menu = TerminalMenu(options, title=title)
    idx = menu.show()
    return idx if idx is not None else None


def _multi_select(options: Sequence[str], title: str) -> Tuple[int, ...]:
    menu = TerminalMenu(
        options,
        title=title,
        multi_select=True,
        show_multi_select_hint=True,
        multi_select_select_on_accept=False,
    )
    idxs = menu.show()
    return idxs if idxs is not None else tuple()


def _confirm(msg: str) -> bool:
    resp = input(f"{msg} (y/N): ").strip().lower()
    return resp == "y"


async def _run_object(obj: Any, strategy: str, replicates: Optional[int]) -> Any:
    if isinstance(obj, ExperimentGraph):
        return await obj.arun(strategy=strategy, replicates=replicates)
    return await obj.arun(
        strategy=strategy,
        replicates=replicates,
        treatments=getattr(obj, "treatments", None),
        hypotheses=getattr(obj, "hypotheses", None),
    )


def _print_experiment_summary(result: Any) -> None:
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
    console = Console()
    console.print(table)
    if result.errors:
        console.print("[bold red]Errors occurred[/]")
        for cond, err in result.errors.items():
            console.print(f"{cond}: {err}")


def _print_summary(result: Any) -> None:
    if isinstance(result, dict):
        for name, res in result.items():
            Console().print(f"[bold underline]{name}[/]")
            _print_experiment_summary(res)
    else:
        _print_experiment_summary(result)


# Interactive run logic reused from the original CLI


async def _run_interactive(obj: Any) -> None:
    console = Console()
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
            options = ["[ SKIP DELETION AND CONTINUE ]"] + [
                f"{name}: {path}" for name, path in deletable
            ]
            title = "Select data to DELETE (Space to select, Enter to confirm)"
            selected_indices = _multi_select(options, title)
            if not selected_indices:
                console.print(
                    "[yellow]No data selected for deletion. Continuing...[/yellow]"
                )
            elif 0 in selected_indices:
                console.print("[green]Keeping all data. Continuing...[/green]")
            else:
                paths_to_delete = [deletable[i - 1][1] for i in selected_indices]
                console.print(
                    "\n[bold yellow]The following directories will be PERMANENTLY DELETED:[/bold yellow]"
                )
                for p in paths_to_delete:
                    console.print(f"- {p}")
                if _confirm("\nAre you sure you want to proceed?"):
                    for p in paths_to_delete:
                        try:
                            shutil.rmtree(p)
                            console.print(f"[green]Deleted: {p}[/green]")
                        except OSError as e:
                            console.print(
                                f"[bold red]Error deleting {p}: {e}[/bold red]"
                            )
                else:
                    console.print("[red]Deletion cancelled by user. Exiting.[/red]")
                    return
    strat_idx = _select_from_menu(["rerun", "resume"], "Execution strategy")
    if strat_idx is None:
        return
    strategy = ["rerun", "resume"][strat_idx]
    result = await _run_object(selected, strategy, None)
    _print_summary(result)


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

    async def on_list_view_selected(self, event: ListView.Selected) -> None:
        obj = event.item.data["obj"]
        with self.suspend():
            await _run_interactive(obj)
        self.exit()


def run() -> None:
    CrystallizeApp().run()


if __name__ == "__main__":  # pragma: no cover - manual run
    run()
