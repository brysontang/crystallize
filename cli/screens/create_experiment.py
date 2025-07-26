from __future__ import annotations

from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Button, Checkbox, Input, Static
from textual.screen import ModalScreen

from ..utils import create_experiment_scaffolding


class CreateExperimentScreen(ModalScreen[None]):
    """Interactive screen for creating a new experiment folder."""

    BINDINGS = [
        ("ctrl+c", "cancel", "Cancel"),
        ("escape", "cancel", "Cancel"),
        ("q", "cancel", "Close"),
        ("c", "create", "Create"),
    ]

    def compose(self) -> ComposeResult:
        with Container(id="create-exp-container"):
            yield Static("Create New Experiment", id="modal-title")
            yield Input(placeholder="experiment name", id="name")
            yield Static("Files to include:")
            with Horizontal():
                yield Checkbox("steps.py", value=True, id="steps")
                yield Checkbox("datasources.py", value=True, id="datasources")
            with Horizontal():
                yield Checkbox("outputs.py", id="outputs")
                yield Checkbox("hypotheses.py", id="hypotheses")
            yield Checkbox("add example code", id="examples")
            with Horizontal(classes="button-row"):
                yield Button("Create", id="create")
                yield Button("Cancel", id="cancel")

    def on_mount(self) -> None:
        self.query_one("#name", Input).focus()

    def action_cancel(self) -> None:
        self.dismiss(None)

    def action_create(self) -> None:
        self._create()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "create":
            self._create()
        else:
            self.dismiss(None)

    def _create(self) -> None:
        name = self.query_one("#name", Input).value.strip()
        if not name or not name.islower() or " " in name:
            self.app.bell()
            return
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
