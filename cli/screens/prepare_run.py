"""Screen for selecting run strategy and artifacts to delete."""

from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Button, Footer, Static, SelectionList
from textual.widgets.selection_list import Selection
from textual.binding import Binding

from .selection_screens import ActionableSelectionList, SingleSelectionList
from .style.prepare_run import CSS


class PrepareRunScreen(ModalScreen[tuple[str, tuple[int, ...]] | None]):
    """Collect execution strategy and deletable artifacts."""

    CSS = CSS

    BINDINGS = [
        Binding("r", "run", "Run"),
        Binding("escape", "cancel_and_exit", "Cancel"),
        Binding("ctrl+c", "cancel_and_exit", "Cancel", show=False),
        Binding("q", "cancel_and_exit", "Close", show=False),
    ]

    def __init__(self, deletable: List[Tuple[str, Path]]) -> None:
        super().__init__()
        self._deletable = deletable
        self._strategy: str | None = "rerun"

    def compose(self) -> ComposeResult:
        with Container(id="prepare-run-container"):
            yield Static("Configure Run", id="modal-title")

            self.options = SingleSelectionList(
                Selection(
                    "rerun - Will overwrite existing data",
                    "rerun",
                    id="rerun",
                    initial_state=True,
                ),
                Selection("resume - Will skip existing data", "resume", id="resume"),
                id="run-method",
            )
            yield self.options
            if self._deletable:
                yield Static(
                    "Select data to delete (optional)",
                    id="delete-info",
                    classes="invisible",
                )
                self.list = ActionableSelectionList(classes="invisible")
                for idx, (name, path) in enumerate(self._deletable):
                    self.list.add_option(Selection(f"  {name}: {path}", idx))
                yield self.list
            with Horizontal(classes="button-row"):
                yield Button("Run", variant="success", id="run")
                yield Button("Cancel", variant="error", id="cancel")
            yield Static(id="run-feedback")
        yield Footer()

    def on_mount(self) -> None:
        self.options.focus()

    def on_selection_list_selected_changed(
        self, message: SelectionList.SelectedChanged
    ) -> None:
        if message.selection_list.selected:
            self._strategy = str(message.selection_list.selected[0])
            if self._strategy == "resume" and self._deletable:
                self.list.remove_class("invisible")
                self.query_one("#delete-info").remove_class("invisible")
            elif self._strategy == "rerun" and self._deletable:
                self.query_one("#delete-info").add_class("invisible")
                self.list.add_class("invisible")

    def action_run(self) -> None:
        if self._strategy is None:
            self.query_one("#run-feedback", Static).update(
                f"[red]Select a run strategy to continue[/red]"
            )
            return
        self.dismiss((self._strategy, ()))

    def on_actionable_selection_list_submitted(
        self, message: ActionableSelectionList.Submitted
    ) -> None:
        if self._strategy is not None:
            self.dismiss((self._strategy, message.selected))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "run":
            if self._strategy is None:
                self.query_one("#run-feedback", Static).update(
                    f"[red]Select a run strategy to continue[/red]"
                )
                return
            selections: tuple[int, ...] = ()
            if hasattr(self, "list"):
                selections = tuple(v for v in self.list.selected if isinstance(v, int))
            self.dismiss((self._strategy, selections))
        else:
            self.dismiss(None)

    def action_cancel_and_exit(self) -> None:
        self.dismiss(None)
