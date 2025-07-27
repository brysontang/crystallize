from __future__ import annotations

import random
from pathlib import Path
from typing import Any, Dict, Tuple

import yaml
from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.screen import Screen
from textual.widgets import (
    Button,
    Footer,
    Header,
    LoadingIndicator,
    Static,
    Tree,
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

        tree = Tree("root", id="object-tree")
        tree.show_root = False
        await left_panel.mount(tree)

        groups: dict[str, list[tuple[str, Dict[str, Any]]]] = {}
        for label, info in graphs.items():
            groups.setdefault(info["cli"]["group"], []).append(("Graph", info))
        for label, info in experiments.items():
            groups.setdefault(info["cli"]["group"], []).append(("Experiment", info))

        for group_name in sorted(groups):
            parent = tree.root.add(group_name, expand=True)
            items = sorted(groups[group_name], key=lambda t: t[1]["cli"]["priority"])
            for obj_type, info in items:
                label = info["label"]
                icon = info["cli"]["icon"]
                color = info["cli"].get("color")
                text = Text(f"{icon} {label} [dim]({obj_type})[/dim]")
                if color:
                    text.stylize(color)
                parent.add_leaf(
                    text,
                    {
                        "path": info["path"],
                        "label": label,
                        "type": obj_type,
                        "doc": info["description"] or "No description available.",
                    },
                )

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

        tree.focus()

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

    async def on_tree_node_highlighted(self, event: Tree.NodeHighlighted) -> None:
        if event.node.data is not None:
            data = event.node.data
            details = self.query_one("#details", Static)
            details.update(f"[bold]Type: {data['type']}[/bold]\n\n{data['doc']}")
            self._selected_obj = data

    async def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        if event.node.data is not None:
            data = event.node.data
            details = self.query_one("#details", Static)
            details.update(f"[bold]Type: {data['type']}[/bold]\n\n{data['doc']}")
            self._selected_obj = data


    def action_show_errors(self) -> None:
        if self._load_errors:
            from ..screens.load_errors import LoadErrorsScreen

            self.app.push_screen(LoadErrorsScreen(self._load_errors))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "run-btn":
            self.action_run_selected()
