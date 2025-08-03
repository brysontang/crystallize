from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Container
from textual.screen import ModalScreen
from textual.widgets import Button, Static


class LoadErrorScreen(ModalScreen[None]):
    """Modal screen displaying a single load error."""

    BINDINGS = [
        ("ctrl+c", "close", "Close"),
        ("escape", "close", "Close"),
        ("q", "close", "Close"),
    ]

    def __init__(self, message: str) -> None:
        super().__init__()
        self._message = message

    def compose(self) -> ComposeResult:
        with Container():
            yield Static("Load Error", id="modal-title")
            yield Static(self._message, id="error-msg")
            yield Button("Close", id="close")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(None)

    def action_close(self) -> None:
        self.dismiss(None)
