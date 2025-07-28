"""Screens for confirming deletion of artifacts."""

from __future__ import annotations

from pathlib import Path


from textual.app import ComposeResult
from textual.containers import Container, Horizontal, VerticalScroll
from textual.widgets import Button, Footer, Static
from textual.screen import ModalScreen
from textual.binding import Binding


class ConfirmScreen(ModalScreen[bool]):
    BINDINGS = [
        Binding("ctrl+c", "cancel_and_exit", "Cancel", show=False),
        Binding("q", "cancel_and_exit", "Close", show=False),
        Binding("y", "confirm_and_exit", "Confirm"),
        Binding("escape", "cancel_and_exit", "Cancel"),
        Binding("n", "cancel_and_exit", "Cancel", show=False),
    ]

    def __init__(self, paths_to_delete: list[Path]) -> None:
        super().__init__()
        self._paths = paths_to_delete

    def compose(self) -> ComposeResult:
        with Container(classes="confirm-delete-container"):
            yield Static(
                "[bold red]The following will be permanently deleted:[/bold red]"
            )
            with VerticalScroll(classes="path-list"):
                if not self._paths:
                    yield Static("  (Nothing selected)")
                for path in self._paths:
                    yield Static(f"• {path}")
            yield Static("\nAre you sure you want to proceed?")
            yield Horizontal(
                Button("Yes, Delete", id="yes"),
                Button("No, Cancel", id="no"),
            )
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#no", Button).focus()

    def action_confirm_and_exit(self) -> None:
        self.dismiss(True)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "yes")

    def action_cancel_and_exit(self) -> None:
        self.dismiss(False)
