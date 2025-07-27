"""Screen for selecting run strategy and artifacts to delete."""

from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Button, OptionList, Static
from textual.widgets.selection_list import Selection
from textual.screen import ModalScreen

from .selection_screens import ActionableSelectionList


class PrepareRunScreen(ModalScreen[tuple[str, tuple[int, ...]] | None]):
    """Collect execution strategy and deletable artifacts."""

    BINDINGS = [
        ("ctrl+c", "cancel_and_exit", "Cancel"),
        ("escape", "cancel_and_exit", "Cancel"),
        ("q", "cancel_and_exit", "Close"),
    ]

    def __init__(self, deletable: List[Tuple[str, Path]]) -> None:
        super().__init__()
        self._deletable = deletable
        self._strategy: str | None = None

    def compose(self) -> ComposeResult:
        with Container(id="prepare-run-container"):
            yield Static("Configure Run", id="modal-title")
            self.options = OptionList()
            self.options.add_option(Selection("rerun", "rerun", id="rerun"))
            self.options.add_option(Selection("resume", "resume", id="resume"))
            yield self.options
            if self._deletable:
                yield Static(
                    "Select data to delete (optional)", id="delete-info"
                )
                self.list = ActionableSelectionList()
                for idx, (name, path) in enumerate(self._deletable):
                    self.list.add_option(Selection(f"  {name}: {path}", idx))
                yield self.list
            with Horizontal(classes="button-row"):
                yield Button("Run", variant="success", id="run")
                yield Button("Cancel", variant="error", id="cancel")

    def on_mount(self) -> None:
        self.options.focus()

    def on_option_list_option_selected(
        self, message: OptionList.OptionSelected
    ) -> None:
        self._strategy = message.option.id

    def on_actionable_selection_list_submitted(
        self, message: ActionableSelectionList.Submitted
    ) -> None:
        if self._strategy is not None:
            self.dismiss((self._strategy, message.selected))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "run":
            if self._strategy is None:
                return
            selections: tuple[int, ...] = ()
            if hasattr(self, "list"):
                selections = tuple(
                    v for v in self.list.selected if isinstance(v, int)
                )
            self.dismiss((self._strategy, selections))
        else:
            self.dismiss(None)

    def action_cancel_and_exit(self) -> None:
        self.dismiss(None)
