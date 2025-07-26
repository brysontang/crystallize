from __future__ import annotations

from typing import Dict

from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import Button, Static, Tree
from textual.screen import ModalScreen


class LoadErrorsScreen(ModalScreen[None]):
    """Display import errors found during discovery."""

    BINDINGS = [
        ("ctrl+c", "close", "Close"),
        ("escape", "close", "Close"),
        ("q", "close", "Close"),
    ]

    def __init__(self, errors: Dict[str, BaseException]) -> None:
        super().__init__()
        self._errors = errors

    def compose(self) -> ComposeResult:
        with Container():
            yield Static("Load Errors", id="modal-title")
            tree = Tree("Failed to load files")
            for file, err in self._errors.items():
                node = tree.root.add(str(file))
                node.add(str(err))
            yield tree
            yield Button("Close", id="close")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(None)

    def action_close(self) -> None:
        self.dismiss(None)
