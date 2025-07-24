"""Screen for displaying run summaries."""
from __future__ import annotations

from typing import Any

from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import Button, RichLog, Static
from textual.screen import ModalScreen

from ..utils import _write_summary


class SummaryScreen(ModalScreen[None]):
    """Display the summary of an experiment run."""

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
