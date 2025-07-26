from __future__ import annotations

import random
from pathlib import Path
from typing import Any, Dict, Tuple

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import (
    Footer,
    Header,
    ListItem,
    ListView,
    LoadingIndicator,
    Static,
    TabbedContent,
    TabPane,
)
from textual.css.query import NoMatches
from rich.text import Text

from .constants import ASCII_ART_ARRAY, CSS, OBJ_TYPES
from .discovery import _import_module, _run_object, discover_objects
from .screens.run import _launch_run
from .screens.create_experiment import CreateExperimentScreen
from .utils import _build_experiment_table, _write_experiment_summary, _write_summary

# Export these for backward compatibility
__all__ = [
    "CrystallizeApp",
    "run",
    "_import_module",
    "discover_objects",
    "_run_object",
    "_build_experiment_table",
    "_write_experiment_summary",
    "_write_summary",
]


class CrystallizeApp(App):
    """Textual application for running crystallize objects."""

    CSS = CSS
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("r", "refresh", "Refresh"),
        ("c", "create_experiment", "Create Experiment"),
        ("ctrl+c", "quit", "Quit"),
        ("e", "show_errors", "Errors"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._load_errors: Dict[str, BaseException] = {}

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Static(random.choice(ASCII_ART_ARRAY), id="title")
        with Container(id="main-container"):
            yield LoadingIndicator()
            yield Static("Scanning for experiments and graphs...", id="loading-text")
        yield Footer()

    async def on_mount(self) -> None:
        self.run_worker(self._discover())

    def action_refresh(self) -> None:
        self.run_worker(self._discover())

    def action_create_experiment(self) -> None:
        self.push_screen(CreateExperimentScreen())

    def _discover_sync(
        self,
    ) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, BaseException]]:
        path = Path(".")
        graphs, graph_errors = discover_objects(path, OBJ_TYPES["graph"])
        experiments, exp_errors = discover_objects(path, OBJ_TYPES["experiment"])
        return graphs, experiments, {**graph_errors, **exp_errors}

    async def _discover(self) -> None:
        worker = self.run_worker(self._discover_sync, thread=True)
        graphs, experiments, errors = await worker.wait()
        self._load_errors = errors

        main_container = self.query_one("#main-container")
        await main_container.remove_children()

        await main_container.mount(Static("Select an object to run:"))

        horizontal = Horizontal()
        await main_container.mount(horizontal)

        left_panel = Container(classes="left-panel")
        await horizontal.mount(left_panel)

        tabbed_content = TabbedContent()
        await left_panel.mount(tabbed_content)

        initial_tab = None
        if experiments:
            tab_pane_exp = TabPane("Experiments", id="experiments")
            await tabbed_content.add_pane(tab_pane_exp)

            list_view_exp = ListView(classes="experiment-list")
            await tab_pane_exp.mount(list_view_exp)

            for label, obj in experiments.items():
                item = ListItem(classes="experiment-item")
                await list_view_exp.append(item)
                await item.mount(Static(Text(f"🧪 {label}")))
                if obj.__doc__:
                    await item.mount(
                        Static(
                            obj.__doc__.strip()[:200] + "...", classes="item-doc dim"
                        )
                    )
                item.data = {
                    "obj": obj,
                    "type": "Experiment",
                    "doc": obj.__doc__ or "No documentation available.",
                }

            initial_tab = "experiments"

        if graphs:
            tab_pane_graph = TabPane("Graphs", id="graphs")
            await tabbed_content.add_pane(tab_pane_graph)

            list_view_graph = ListView(classes="graph-list")
            await tab_pane_graph.mount(list_view_graph)

            for label, obj in graphs.items():
                item = ListItem(classes="graph-item")
                await list_view_graph.append(item)
                await item.mount(Static(Text(f"📈 {label}")))
                if obj.__doc__:
                    await item.mount(
                        Static(
                            obj.__doc__.strip()[:200] + "...", classes="item-doc dim"
                        )
                    )
                item.data = {
                    "obj": obj,
                    "type": "Graph",
                    "doc": obj.__doc__ or "No documentation available.",
                }

            if initial_tab is None:
                initial_tab = "graphs"

        if initial_tab:
            tabbed_content.active = initial_tab

        right_panel = Container(classes="right-panel")
        await horizontal.mount(right_panel)
        await right_panel.mount(Static(id="details", classes="details-panel"))

        if self._load_errors:
            await main_container.mount(
                Static(
                    f"Failed to load {len(self._load_errors)} file(s), press e for more details",
                    id="error-msg",
                )
            )

        try:
            self.query_one(".experiment-list", ListView).focus()
        except NoMatches:
            try:
                self.query_one(".graph-list", ListView).focus()
            except NoMatches:
                pass

    async def _run_interactive_and_exit(self, obj: Any) -> None:
        await _launch_run(self, obj)

    async def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        if event.item is not None:
            data = event.item.data
            details = self.query_one("#details", Static)
            details.update(f"[bold]Type: {data['type']}[/bold]\n\n{data['doc']}")

    async def on_list_view_selected(self, event: ListView.Selected) -> None:
        obj = event.item.data["obj"]
        self.run_worker(self._run_interactive_and_exit(obj))

    def action_show_errors(self) -> None:
        if self._load_errors:
            from .screens.load_errors import LoadErrorsScreen

            self.push_screen(LoadErrorsScreen(self._load_errors))


def run() -> None:
    CrystallizeApp().run()
