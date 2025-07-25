from __future__ import annotations

from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import Button, Checkbox, Collapsible, Input, Label, Static
from textual.screen import ModalScreen

from ..utils import create_experiment_scaffolding


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
                yield Checkbox(
                    "steps.py",
                    value=True,
                    id="steps",
                    tooltip="Defines experiment steps and logic",
                )
                yield Checkbox(
                    "datasources.py",
                    value=True,
                    id="datasources",
                    tooltip="Handles data input sources",
                )
                yield Checkbox(
                    "outputs.py",
                    id="outputs",
                    tooltip="Manages experiment outputs and results",
                )
                yield Checkbox(
                    "hypotheses.py",
                    id="hypotheses",
                    tooltip="Documents hypotheses and assumptions",
                )
            yield Checkbox(
                "Add example code",
                id="examples",
                tooltip="Includes starter code in selected files",
            )
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
        try:
            create_experiment_scaffolding(
                name,
                directory=base,
                steps=self.query_one("#steps", Checkbox).value,
                datasources=self.query_one("#datasources", Checkbox).value,
                outputs=self.query_one("#outputs", Checkbox).value,
                hypotheses=self.query_one("#hypotheses", Checkbox).value,
                examples=self.query_one("#examples", Checkbox).value,
            )
        except FileExistsError:
            self.app.bell()
            return
        self.dismiss(None)
