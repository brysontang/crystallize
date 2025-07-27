from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.widgets import Button, Collapsible, Input, Label, Static
from textual.widgets.selection_list import Selection

from ..utils import create_experiment_scaffolding
from .selection_screens import ActionableSelectionList


class CreateExperimentScreen(ModalScreen[None]):
    """Interactive screen for creating a new experiment folder."""

    CSS_PATH = "style/create_experiment.tcss"

    BINDINGS = [
        ("ctrl+c", "cancel", "Cancel"),
        ("escape", "cancel", "Cancel"),
        ("q", "cancel", "Close"),
        ("c", "create", "Create"),
    ]

    name_valid = reactive(False)

    def compose(self) -> ComposeResult:
        with Vertical(id="create-exp-container"):
            yield Static("Create New Experiment", id="modal-title")
            yield Input(
                placeholder="Enter experiment name (lowercase, no spaces)",
                id="name-input",
            )
            yield Label(id="name-feedback")  # For validation feedback
            with Collapsible(title="Files to include", collapsed=False):
                self.file_list = ActionableSelectionList(classes="files-to-include")
                self.file_list.add_option(
                    Selection(
                        "steps.py",
                        "steps",
                        initial_state=True,
                        id="steps",
                        disabled=False,
                    )
                )
                self.file_list.add_option(
                    Selection(
                        "datasources.py",
                        "datasources",
                        initial_state=True,
                        id="datasources",
                    )
                )
                self.file_list.add_option(
                    Selection(
                        "outputs.py",
                        "outputs",
                        id="outputs",
                    )
                )
                self.file_list.add_option(
                    Selection(
                        "hypotheses.py",
                        "hypotheses",
                        id="hypotheses",
                    )
                )
                yield self.file_list
            self.examples = ActionableSelectionList(
                Selection("Add example code", "examples", id="examples")
            )
            yield self.examples
            with Horizontal(classes="button-row"):
                yield Button("Create", variant="success", id="create")
                yield Button("Cancel", variant="error", id="cancel")

    def on_mount(self) -> None:
        self.query_one("#name-input", Input).focus()

    def on_input_changed(self, event: Input.Changed) -> None:
        name = event.value.strip()
        feedback = self.query_one("#name-feedback", Label)
        if not name:
            feedback.update("[dim]Enter a name to continue[/dim]")
            self.name_valid = False
        elif not name.islower() or " " in name:
            feedback.update("[red]Name must be lowercase with no spaces[/red]")
            self.name_valid = False
        else:
            feedback.update(f"[green]Path: experiments/{name}[/green]")
            self.name_valid = True

    def action_cancel(self) -> None:
        self.dismiss(None)

    def action_create(self) -> None:
        if self.name_valid:
            self._create()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "create" and self.name_valid:
            self._create()
        else:
            self.dismiss(None)

    def _create(self) -> None:
        name = self.query_one("#name-input", Input).value.strip()
        base = Path("experiments")
        selections = set(self.file_list.selected)
        examples = "examples" in self.examples.selected
        try:
            create_experiment_scaffolding(
                name,
                directory=base,
                steps="steps" in selections,
                datasources="datasources" in selections,
                outputs="outputs" in selections,
                hypotheses="hypotheses" in selections,
                examples=examples,
            )
        except FileExistsError:
            self.app.bell()
            return
        self.dismiss(None)
