from __future__ import annotations

import random
from pathlib import Path
from typing import Any, Dict, Tuple

import yaml
from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.css.query import NoMatches
from textual.screen import Screen
from textual.widgets import (
    Button,
    Footer,
    Header,
    Input,
    ListItem,
    ListView,
    LoadingIndicator,
    Static,
    TabbedContent,
    TabPane,
)

from crystallize.experiments.experiment import Experiment
from crystallize.experiments.experiment_graph import ExperimentGraph

from ..constants import ASCII_ART_ARRAY
from ..discovery import discover_configs
from ..screens.create_experiment import CreateExperimentScreen
from ..screens.run import _launch_run


class SelectionScreen(Screen):
    """Main screen for selecting experiments or graphs."""

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("r", "refresh", "Refresh"),
        ("c", "create_experiment", "Create Experiment"),
        ("e", "show_errors", "Errors"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._load_errors: Dict[str, BaseException] = {}
        self._experiments: Dict[str, Dict[str, Any]] = {}
        self._graphs: Dict[str, Dict[str, Any]] = {}
        self._selected_obj: Dict[str, Any] | None = None

    async def _filter_list(self, query: str, selector: str) -> None:
        list_view = self.query_one(selector, ListView)
        for item in list_view.children:
            label = item.data.get("label", "").lower()
            item.display = query.lower() in label

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Static(random.choice(ASCII_ART_ARRAY), id="title")
        with Container(id="main-container"):
            yield LoadingIndicator()
            yield Static(
                "Scanning for experiments and graphs...",
                id="loading-text",
            )
        yield Footer()

    async def on_mount(self) -> None:
        self.run_worker(self._discover())

    def action_refresh(self) -> None:
        self.run_worker(self._discover())

    def action_create_experiment(self) -> None:
        self.app.push_screen(CreateExperimentScreen())

    def _discover_sync(
        self,
    ) -> Tuple[
        Dict[str, Dict[str, Any]],
        Dict[str, Dict[str, Any]],
        Dict[str, BaseException],
    ]:
        """Locate ``config.yaml`` files and classify them."""

        return discover_configs(Path("."))

    async def _discover(self) -> None:
        worker = self.run_worker(self._discover_sync, thread=True)
        graphs, experiments, errors = await worker.wait()
        self._load_errors = errors
        self._experiments = experiments
        self._graphs = graphs

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

        if graphs:
            tab_pane_graph = TabPane("Graphs", id="graphs")
            await tabbed_content.add_pane(tab_pane_graph)

            search_graph = Input(placeholder="Search graphs...", id="search-graph")
            await tab_pane_graph.mount(search_graph)
            list_view_graph = ListView(classes="graph-list")
            await tab_pane_graph.mount(list_view_graph)

            for label, info in graphs.items():
                item = ListItem(classes="graph-item")
                await list_view_graph.append(item)
                await item.mount(Static(Text(f"📈 {label}")))
                if info["description"]:
                    await item.mount(
                        Static(
                            info["description"].strip()[:200] + "...",
                            classes="item-doc dim",
                        )
                    )
                item.data = {
                    "path": info["path"],
                    "label": label,
                    "type": "Graph",
                    "doc": info["summary"],
                }

            initial_tab = "graphs"

        if experiments:
            tab_pane_exp = TabPane("Experiments", id="experiments")
            await tabbed_content.add_pane(tab_pane_exp)

            search_exp = Input(placeholder="Search experiments...", id="search-exp")
            await tab_pane_exp.mount(search_exp)
            list_view_exp = ListView(classes="experiment-list")
            await tab_pane_exp.mount(list_view_exp)

            for label, info in experiments.items():
                item = ListItem(classes="experiment-item")
                await list_view_exp.append(item)
                await item.mount(Static(Text(f"🧪 {label}")))
                if info["description"]:
                    await item.mount(
                        Static(
                            info["description"].strip()[:200] + "...",
                            classes="item-doc dim",
                        )
                    )
                item.data = {
                    "path": info["path"],
                    "label": label,
                    "type": "Experiment",
                    "doc": info["summary"],
                }

            if initial_tab is None:
                initial_tab = "experiments"

        if initial_tab:
            tabbed_content.active = initial_tab

        right_panel = Container(classes="right-panel")
        await horizontal.mount(right_panel)
        await right_panel.mount(Static(id="details", classes="details-panel"))
        await right_panel.mount(Button("Run", id="run-btn"))

        if self._load_errors:
            await main_container.mount(
                Static(
                    f"Failed to load {len(self._load_errors)} file(s), press e for more details",
                    id="error-msg",
                )
            )

        try:
            self.query_one(".graph-list", ListView).focus()
        except NoMatches:
            try:
                self.query_one(".experiment-list", ListView).focus()
            except NoMatches:
                pass

    async def _run_interactive_and_exit(self, info: Dict[str, Any]) -> None:
        cfg = info["path"]
        obj_type = info["type"]
        try:
            if obj_type == "Graph":
                obj = ExperimentGraph.from_yaml(cfg)
            else:
                obj = Experiment.from_yaml(cfg)
        except BaseException as exc:  # noqa: BLE001
            self._load_errors[str(cfg)] = exc
            from ..screens.load_errors import LoadErrorsScreen

            self.app.push_screen(LoadErrorsScreen({str(cfg): exc}))
            return

        await _launch_run(self.app, obj)

    def action_run_selected(self) -> None:
        if self._selected_obj is not None:
            self.run_worker(self._run_interactive_and_exit(self._selected_obj))

    async def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        if event.item is not None:
            data = event.item.data
            details = self.query_one("#details", Static)
            details.update(f"[bold]Type: {data['type']}[/bold]\n\n{data['doc']}")
            self._selected_obj = data

    async def on_list_view_selected(self, event: ListView.Selected) -> None:
        data = event.item.data
        details = self.query_one("#details", Static)
        details.update(f"[bold]Type: {data['type']}[/bold]\n\n{data['doc']}")
        self._selected_obj = data

    async def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "search-exp":
            await self._filter_list(event.value, ".experiment-list")
        elif event.input.id == "search-graph":
            await self._filter_list(event.value, ".graph-list")

    def action_show_errors(self) -> None:
        if self._load_errors:
            from ..screens.load_errors import LoadErrorsScreen

            self.app.push_screen(LoadErrorsScreen(self._load_errors))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "run-btn":
            self.action_run_selected()
