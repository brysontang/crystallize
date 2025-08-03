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
from textual.binding import Binding

from crystallize.experiments.experiment import Experiment
from crystallize.experiments.experiment_graph import ExperimentGraph

from ..constants import ASCII_ART_ARRAY
from ..discovery import discover_configs
from ..errors import ExperimentLoadError, format_load_error
from ..screens.create_experiment import CreateExperimentScreen
from ..screens.load_error import LoadErrorScreen
from ..screens.run import _launch_run
from ..utils import compute_static_eta, format_seconds

from ..widgets import ConfigEditorWidget
from .loading import LoadingScreen


class ExperimentTree(Tree):
    """Tree widget with custom binding for experiment selection."""

    BINDINGS = [b for b in Tree.BINDINGS if getattr(b, "key", "") != "enter"] + [
        Binding("enter", "run_selected", "Run", show=True)
    ]

    def action_run_selected(self) -> None:  # pragma: no cover - delegates
        screen = self.screen
        if screen is not None and hasattr(screen, "action_run_selected"):
            screen.action_run_selected()

        try:
            line = self._tree_lines[self.cursor_line]
        except IndexError:
            pass
        else:
            node = line.path[-1]
            self.post_message(Tree.NodeSelected(node))


class SelectionScreen(Screen):
    """Main screen for selecting experiments or graphs."""

    BINDINGS = [
        ("n", "create_experiment", "New Experiment"),
        ("r", "refresh", "Refresh"),
        ("e", "show_errors", "Errors"),
        ("q", "quit", "Quit"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._load_errors: Dict[str, ExperimentLoadError] = {}
        self._experiments: Dict[str, Dict[str, Any]] = {}
        self._graphs: Dict[str, Dict[str, Any]] = {}
        self._selected_obj: Dict[str, Any] | None = None
        self._selected_line: int | None = None

    async def _update_details(self, data: Dict[str, Any]) -> None:
        """Populate the details panel with information from ``data``."""

        details = self.query_one("#details", Static)
        cfg_path = Path(data["path"])
        info = yaml.safe_load(cfg_path.read_text()) or {}

        desc = info.get("description", data.get("doc", ""))
        cli_info = info.get("cli", {})
        icon = cli_info.get("icon", "🧪")
        eta = compute_static_eta(cfg_path)
        if data.get("type") == "Graph":
            total = eta
            for cfg in cfg_path.parent.rglob("config.yaml"):
                if cfg == cfg_path:
                    continue
                total += compute_static_eta(cfg)
            eta = total
        eta_str = format_seconds(eta.total_seconds())
        details.update(f"{icon} {data['label']}\n{desc}\n⏳ Estimated runtime: {eta_str}")

        container = self.query_one("#config-container")
        await container.remove_children()
        await container.mount(ConfigEditorWidget(cfg_path))

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
        def _refresh_sync(inp: Any) -> None:
            self.run_worker(self._discover())

        self.app.push_screen(CreateExperimentScreen(), _refresh_sync)

    def _discover_sync(
        self,
    ) -> Tuple[
        Dict[str, Dict[str, Any]],
        Dict[str, Dict[str, Any]],
        Dict[str, ExperimentLoadError],
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

        tree = ExperimentTree("root", id="object-tree")
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
                text = Text(f"{icon} {label} ({obj_type})")
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
        await right_panel.mount(Container(id="config-container"))

        btn_container = Container(id="select-button-container")
        await right_panel.mount(btn_container)
        await btn_container.mount(Button("Run", id="run-btn"))

        if self._load_errors:
            await main_container.mount(
                Static(
                    f"Failed to load {len(self._load_errors)} file(s), press e for more details",
                    id="error-msg",
                )
            )
        if self._selected_line is not None:
            tree.move_cursor_to_line(self._selected_line)
        else:
            try:
                tree.move_cursor_to_line(0)  # pragma: no cover
            except IndexError:
                pass

        tree.focus()

    async def _run_interactive_and_exit(self, info: Dict[str, Any]) -> None:
        cfg = info["path"]
        obj_type = info["type"]
        try:
            await self.app.push_screen(LoadingScreen())
            if obj_type == "Graph":
                obj = ExperimentGraph.from_yaml(cfg)
            else:
                obj = Experiment.from_yaml(cfg)
        except BaseException as exc:  # noqa: BLE001
            load_err = format_load_error(cfg, exc)
            self._load_errors[str(cfg)] = load_err
            self.app.pop_screen()
            self.app.push_screen(LoadErrorScreen(str(load_err)))
            return

        self.app.pop_screen()
        await _launch_run(self.app, obj, cfg, obj_type == "Graph")

    def action_run_selected(self) -> None:
        if self._selected_obj is not None:
            self.run_worker(self._run_interactive_and_exit(self._selected_obj))

    async def on_tree_node_highlighted(self, event: Tree.NodeHighlighted) -> None:
        if event.control.id != "object-tree":
            return
        if event.node.data is not None:
            data = event.node.data
            await self._update_details(data)
            self._selected_obj = data
            self._selected_line = event.node.line
        else:
            # details = self.query_one("#details", Static)
            # details.update("")
            self._selected_obj = None
            if not event.node.is_root:
                self._selected_line = event.node.line

    async def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        if event.control.id != "object-tree":
            return
        if event.node.data is not None:
            data = event.node.data
            await self._update_details(data)
            self._selected_obj = data
            self._selected_line = event.node.line

    def action_show_errors(self) -> None:
        if self._load_errors:
            err = next(iter(self._load_errors.values()))
            self.app.push_screen(LoadErrorScreen(str(err)))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "run-btn":
            self.action_run_selected()
