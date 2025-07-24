"""Reusable selection widgets for the CLI."""
from __future__ import annotations

from typing import Any

from textual.message import Message
from textual.widgets import SelectionList


class ActionableSelectionList(SelectionList):
    """A SelectionList that emits a Submitted message on Enter."""

    class Submitted(Message):
        def __init__(self, selected: tuple[Any, ...]) -> None:
            self.selected = selected
            super().__init__()

    BINDINGS = [("enter", "submit", "Submit")]

    def action_submit(self) -> None:
        selected_indices = tuple(value for value in self.selected if isinstance(value, int))
        self.post_message(self.Submitted(selected_indices))
