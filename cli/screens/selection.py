from __future__ import annotations

import random
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Tuple

import yaml
from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.screen import Screen
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Header,
    LoadingIndicator,
    Static,
)
from textual.css.query import NoMatches

from crystallize.experiments.experiment import Experiment
from crystallize.experiments.experiment_graph import ExperimentGraph

from ..constants import ASCII_ART_ARRAY
from ..discovery import discover_configs
from ..errors import ExperimentLoadError, format_load_error
from ..screens.create_experiment import CreateExperimentScreen
from ..screens.command_palette import CommandPaletteScreen
from ..screens.help import HelpScreen
from ..screens.load_error import LoadErrorScreen
from ..screens.run import _launch_run
from ..utils import compute_static_eta, format_seconds

from ..widgets import ConfigEditorWidget
from .loading import LoadingScreen


class SelectionScreen(Screen):
    """Main screen for selecting experiments or graphs."""

    BINDINGS = [
        ("n", "create_experiment", "New Experiment"),
        ("r", "refresh", "Refresh"),
        ("e", "show_errors", "Errors"),
        ("ctrl+p", "open_command_palette", "Command Palette"),
        ("?", "show_help", "Help"),
        ("q", "quit", "Quit"),
        ("enter", "run_selected", "Run"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._load_errors: Dict[str, ExperimentLoadError] = {}
        self._experiments: Dict[str, Dict[str, Any]] = {}
        self._graphs: Dict[str, Dict[str, Any]] = {}
        self._selected_obj: Dict[str, Any] | None = None
        self._selected_row_key: str | None = None
        self._row_data: Dict[str, Dict[str, Any]] = {}
        self._sort_state: tuple[Any, bool] | None = None
        self._table: DataTable | None = None

    async def _update_details(self, data: Dict[str, Any]) -> None:
        """Populate the details panel with information from ``data``."""

        try:
            details = self.query_one("#details", Static)
        except NoMatches:
            return
        cfg_path = Path(data["path"])
        try:
            info = yaml.safe_load(cfg_path.read_text()) or {}
        except Exception as exc:  # noqa: BLE001
            details.update(
                f"⚠️ {data['label']}\nUnable to load config: {exc}\n"
                "Open the config to resolve the issue."
            )
            container = self.query_one("#config-container")
            await container.remove_children()
            await container.mount(ConfigEditorWidget(cfg_path))
            return

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

    def action_open_command_palette(self) -> None:
        if not self._row_data:
            return
        options = list(self._row_data.values())
        self.app.push_screen(
            CommandPaletteScreen(options), self._handle_palette_selection
        )

    def action_show_help(self) -> None:
        self.app.push_screen(HelpScreen(), lambda _result: self._focus_table())

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

        await main_container.mount(Static("Productivity Dashboard", id="dashboard-title"))

        horizontal = Horizontal()
        await main_container.mount(horizontal)

        left_panel = Container(classes="left-panel")
        right_panel = Container(classes="right-panel")
        await horizontal.mount(left_panel)
        await horizontal.mount(right_panel)

        table = DataTable(
            id="object-table",
            cursor_type="row",
            zebra_stripes=True,
            show_row_labels=False,
        )
        table.add_column("Status", key="status")
        table.add_column("Name", key="name")
        table.add_column("Group", key="group")
        table.add_column("Replicates", key="replicates")
        table.add_column("Last Run", key="last_run")
        await left_panel.mount(table)
        self._table = table

        await right_panel.mount(Static(id="details", classes="details-panel"))
        await right_panel.mount(Container(id="config-container"))

        btn_container = Container(id="select-button-container")
        await right_panel.mount(btn_container)
        await btn_container.mount(Button("Run", id="run-btn"))

        self._row_data = {}
        grouped: dict[str, list[dict[str, Any]]] = {}
        for info in graphs.values():
            grouped.setdefault(info["cli"]["group"], []).append(
                {**info, "type": "Graph"}
            )
        for info in experiments.values():
            grouped.setdefault(info["cli"]["group"], []).append(
                {**info, "type": "Experiment"}
            )

        for group_name in sorted(grouped):
            items = sorted(
                grouped[group_name], key=lambda entry: entry["cli"]["priority"]
            )
            for info in items:
                label = info["label"]
                obj_type = info["type"]
                cfg_path = Path(info["path"])
                data_name = info.get("name", cfg_path.parent.name)
                status_icon, last_run = self._get_experiment_status(data_name)
                row_key = str(cfg_path)
                row_details = {
                    "path": cfg_path,
                    "label": label,
                    "type": obj_type,
                    "doc": info["description"] or "No description available.",
                    "replicates": info.get("replicates", 1),
                    "group": info["cli"]["group"],
                    "name": data_name,
                    "status": status_icon,
                    "last_run": last_run,
                    "icon": info["cli"]["icon"],
                }
                self._row_data[row_key] = row_details
                table.add_row(
                    status_icon,
                    label,
                    info["cli"]["group"],
                    info.get("replicates", 1),
                    last_run,
                    key=row_key,
                )

        if not self._row_data:
            details = self.query_one("#details", Static)
            details.update("No experiments found.")
            self._selected_obj = None
            self._selected_row_key = None

        if self._load_errors:
            await main_container.mount(
                Static(
                    f"Failed to load {len(self._load_errors)} file(s), press e for more details",
                    id="error-msg",
                )
            )
        selected_key = self._selected_row_key
        if selected_key is None or selected_key not in self._row_data:
            selected_key = next(iter(self._row_data), None)

        if selected_key is not None:
            try:
                row_index = table.get_row_index(selected_key)
                table.move_cursor(row=row_index)
                await self._set_selection(selected_key)
            except Exception:
                self._selected_obj = None
                self._selected_row_key = None
        self._focus_table()

    def _handle_palette_selection(self, selection: Dict[str, Any] | None) -> None:
        if selection is None:
            self._focus_table()
            return
        self._selected_obj = selection
        self._selected_row_key = str(selection["path"])
        table = self._table
        if table is not None:
            try:
                row_index = table.get_row_index(self._selected_row_key)
                table.move_cursor(row=row_index)
            except Exception:
                pass
        self.run_worker(self._run_interactive_and_exit(selection))

    def _focus_table(self) -> None:
        if self._table is not None:
            self._table.focus()

    async def _set_selection(
        self, row_key: str, *, update_details: bool = True
    ) -> bool:
        data = self._row_data.get(row_key)
        if data is None:
            return False
        if update_details:
            await self._update_details(data)
        self._selected_obj = data
        self._selected_row_key = row_key
        return True

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

    def _get_experiment_status(self, name: str) -> tuple[str, str]:
        """Return status icon and timestamp for the latest run of ``name``."""

        base = Path("data") / name
        if not base.exists():
            return "⚪", "Never"

        versions = sorted(
            [
                int(p.name[1:])
                for p in base.iterdir()
                if p.is_dir() and p.name.startswith("v") and p.name[1:].isdigit()
            ],
            reverse=True,
        )
        if not versions:
            return "⚪", "Never"

        meta_path = base / f"v{versions[0]}" / "metadata.json"
        if meta_path.exists():
            ts = datetime.fromtimestamp(meta_path.stat().st_mtime)
            return "🟢", ts.strftime("%Y-%m-%d %H:%M")

        return "⚪", "Never"

    @on(DataTable.RowHighlighted)
    async def on_data_table_row_highlighted(
        self, event: DataTable.RowHighlighted
    ) -> None:
        if event.data_table.id != "object-table":
            return
        row_key = str(event.row_key)
        await self._set_selection(row_key)

    @on(DataTable.RowSelected)
    async def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        if event.data_table.id != "object-table":
            return
        row_key = str(event.row_key)
        update_details = row_key != self._selected_row_key
        if not await self._set_selection(row_key, update_details=update_details):
            return
        self.run_worker(self._run_interactive_and_exit(self._selected_obj))

    @on(DataTable.HeaderSelected)
    def on_data_table_header_selected(self, event: DataTable.HeaderSelected) -> None:
        if event.data_table.id != "object-table":
            return
        column_key = event.column_key
        reverse = (
            not self._sort_state[1]
            if self._sort_state and self._sort_state[0] == column_key
            else False
        )
        self._sort_state = (column_key, reverse)
        event.data_table.sort(column_key, reverse=reverse)
        if self._selected_row_key is not None:
            try:
                row_index = event.data_table.get_row_index(self._selected_row_key)
                event.data_table.move_cursor(row=row_index)
            except Exception:
                pass

    def action_show_errors(self) -> None:
        if self._load_errors:
            err = next(iter(self._load_errors.values()))
            self.app.push_screen(LoadErrorScreen(str(err)))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "run-btn":
            self.action_run_selected()
