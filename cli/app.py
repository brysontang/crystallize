from __future__ import annotations

from textual.app import App

from .constants import CSS
from .discovery import _import_module, _run_object, discover_objects
from .utils import _build_experiment_table, _write_experiment_summary, _write_summary
from .screens.selection import SelectionScreen

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
        ("ctrl+c", "quit", "Quit"),
    ]

    def on_mount(self) -> None:
        self.push_screen(SelectionScreen())


def run() -> None:
    import sys

    if "--serve" in sys.argv:
        from textual_serve.server import Server

        server = Server("crystallize")

        server.serve()
        return

    CrystallizeApp().run()
