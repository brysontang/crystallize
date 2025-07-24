"""Textual application wiring for the Crystallize CLI."""

from __future__ import annotations

import random
from pathlib import Path
from typing import Any, Dict, Tuple

from textual.app import App, ComposeResult
from textual.containers import Container, VerticalScroll
from textual.widgets import Footer, Header, ListItem, ListView, LoadingIndicator, Static
from textual.css.query import NoMatches
from rich.text import Text

from .constants import ASCII_ART_ARRAY, CSS, OBJ_TYPES
from .discovery import _import_module, _run_object, discover_objects
from .screens.run import _launch_run
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
        ("ctrl+c", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Static(random.choice(ASCII_ART_ARRAY), id="title")
        with Container(id="main-container"):
            yield LoadingIndicator()
            yield Static("Scanning for experiments and graphs...", id="loading-text")
        yield Footer()

    async def on_mount(self) -> None:
        self.run_worker(self._discover)

    def action_refresh(self) -> None:
        self.run_worker(self._discover)

    def _discover_sync(self) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        path = Path(".")
        graphs = discover_objects(path, OBJ_TYPES["graph"])
        experiments = discover_objects(path, OBJ_TYPES["experiment"])
        return graphs, experiments

    async def _discover(self) -> None:
        worker = self.run_worker(self._discover_sync, thread=True)
        graphs, experiments = await worker.wait()

        main_container = self.query_one("#main-container")
        await main_container.remove_children()

        await main_container.mount(Static("Select an object to run:"))
        list_view = ListView(initial_index=0)
        await main_container.mount(VerticalScroll(list_view))

        for label, obj in graphs.items():
            escaped_label = Static(Text(f"[Graph] {label}"))
            item = ListItem(escaped_label, classes="graph-item")
            item.data = {"obj": obj, "type": "Graph"}
            await list_view.append(item)
        for label, obj in experiments.items():
            escaped_label = Static(Text(f"[Experiment] {label}"))
            item = ListItem(escaped_label, classes="experiment-item")
            item.data = {"obj": obj, "type": "Experiment"}
            await list_view.append(item)

        list_view.focus()

    async def _run_interactive_and_exit(self, obj: Any) -> None:
        await _launch_run(self, obj)

    async def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        if event.item is not None:
            try:
                type_text = self.query_one("#type-text", Static)
                type_text.update(f"Type: {event.item.data['type']}")
            except NoMatches:  # pragma: no cover - optional widget
                pass

    async def on_list_view_selected(self, event: ListView.Selected) -> None:
        obj = event.item.data["obj"]
        self.run_worker(self._run_interactive_and_exit(obj))


def run() -> None:
    CrystallizeApp().run()
