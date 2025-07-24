"""Screen for selecting execution strategy."""
from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import Button, OptionList, Static
from textual.widgets.selection_list import Selection
from textual.screen import ModalScreen


class StrategyScreen(ModalScreen[str | None]):
    BINDINGS = [("ctrl+c", "cancel_and_exit", "Cancel")]

    def compose(self) -> ComposeResult:
        with Container():
            yield Static("Execution strategy", id="modal-title")
            self.options = OptionList()
            self.options.add_option(Selection("rerun", "rerun", id="rerun"))
            self.options.add_option(Selection("resume", "resume", id="resume"))
            yield self.options
            yield Button("Cancel", id="cancel")

    def on_option_list_option_selected(
        self, message: OptionList.OptionSelected
    ) -> None:
        self.dismiss(message.option.id)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(None)

    def action_cancel_and_exit(self) -> None:
        self.dismiss(None)
