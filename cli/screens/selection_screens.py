"""Reusable selection widgets for the CLI."""

from __future__ import annotations

from typing import Any

from textual.message import Message
from textual.widgets import SelectionList
from textual.widgets.selection_list import Selection
from textual.binding import Binding


class ActionableSelectionList(SelectionList):
    """A SelectionList that emits a Submitted message on Enter."""

    class Submitted(Message):
        def __init__(self, selected: tuple[Any, ...]) -> None:
            self.selected = selected
            super().__init__()

    BINDINGS = [
        Binding("a", "all", "Select All"),
        Binding("d", "deselect_all", "Deselect All"),
    ]

    def action_all(self) -> None:
        self.select_all()
        self.refresh()

    def action_deselect_all(self) -> None:
        self.deselect_all()
        self.refresh()

    def action_submit(self) -> None:
        selected_indices = tuple(
            value for value in self.selected if isinstance(value, int)
        )
        self.post_message(self.Submitted(selected_indices))


class SingleSelectionList(SelectionList):
    """A SelectionList that allows only a single selection."""

    def select(self, selection: Selection | Any) -> "SingleSelectionList":
        self.deselect_all()
        return super().select(selection)

    def toggle(self, selection: Selection | Any) -> "SingleSelectionList":
        if selection in self.selected or (
            isinstance(selection, Selection) and selection.value in self.selected
        ):
            self.deselect_all()
        else:
            self.deselect_all()
            super().select(selection)
        self.refresh()
        return self
