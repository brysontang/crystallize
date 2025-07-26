from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Container
from textual.screen import ModalScreen
from textual.widgets import Button, Checkbox, Input, OptionList, Static
from textual.widgets.selection_list import Selection

from crystallize.experiments.experiment import Experiment

from ..constants import OBJ_TYPES
from ..discovery import discover_objects
from ..utils import create_experiment_scaffolding
from .selection_screens import ActionableSelectionList


class CreateExperimentScreen(ModalScreen[None]):
    """Interactive screen for creating a new experiment folder."""

    BINDINGS = [
        ("ctrl+c", "cancel", "Cancel"),
        ("q", "cancel", "Close"),
        ("c", "create", "Create"),
    ]

    def compose(self) -> ComposeResult:
        with Container():
            yield Static("Create New Experiment", id="modal-title")
            yield Input(placeholder="experiment name", id="name")
            yield Checkbox("steps.py", value=True, id="steps")
            yield Checkbox("datasources.py", value=True, id="datasources")
            yield Checkbox("outputs.py", id="outputs")
            yield Checkbox("hypotheses.py", id="hypotheses")
            yield Checkbox("add example code", id="examples")
            yield Checkbox("experiment is a graph", id="graph")
            yield Button("Create", id="create")
            yield Button("Cancel", id="cancel")

    def on_mount(self) -> None:
        self.query_one("#name", Input).focus()

    def action_cancel(self) -> None:
        self.dismiss(None)

    async def action_create(self) -> None:
        await self._create()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "create":
            await self._create()
        else:
            self.dismiss(None)

    async def _create(self) -> None:
        name = self.query_one("#name", Input).value.strip()
        if not name or not name.islower() or " " in name:
            self.app.bell()
            return
        base = Path("experiments")
        inputs = None
        if self.query_one("#graph", Checkbox).value:
            exps = discover_objects(Path("."), OBJ_TYPES["experiment"])
            mapping = await self.app.push_screen_wait(SelectInputsScreen(exps))
            if mapping is None:
                return
            inputs = mapping
        try:
            create_experiment_scaffolding(
                name,
                directory=base,
                steps=self.query_one("#steps", Checkbox).value,
                datasources=self.query_one("#datasources", Checkbox).value,
                outputs=self.query_one("#outputs", Checkbox).value,
                hypotheses=self.query_one("#hypotheses", Checkbox).value,
                examples=self.query_one("#examples", Checkbox).value,
                input_artifacts=inputs,
            )
        except FileExistsError:
            self.app.bell()
            return
        self.dismiss(None)


class SelectInputsScreen(ModalScreen[dict[str, str] | None]):
    """Allow the user to choose outputs from existing experiments."""

    BINDINGS = [
        ("ctrl+c", "cancel", "Cancel"),
        ("q", "cancel", "Close"),
        ("enter", "confirm", "Confirm"),
    ]

    def __init__(self, experiments: dict[str, Experiment]) -> None:
        super().__init__()
        self._experiments = experiments
        self._current: str | None = None

    def compose(self) -> ComposeResult:
        with Container():
            yield Static("Select experiment inputs", id="modal-title")
            with Container(id="input-select"):
                self.exp_list = OptionList(id="exp-list")
                for name in self._experiments:
                    self.exp_list.add_option(Selection(name, name))
                self.out_list = ActionableSelectionList(id="out-list")
                yield self.exp_list
                yield self.out_list
            yield Button("Confirm", id="confirm")
            yield Button("Cancel", id="cancel")

    def on_mount(self) -> None:
        if self.exp_list.options:
            first = self.exp_list.options[0]
            self._current = first.id if hasattr(first, "id") else first.value
            self._update_outputs(self._current)
        self.exp_list.focus()

    def _update_outputs(self, exp: str) -> None:
        self.out_list.clear_options()
        for out in self._experiments[exp].outputs:
            self.out_list.add_option(Selection(out, out))

    def on_option_list_option_selected(
        self, message: OptionList.OptionSelected
    ) -> None:
        self._current = message.option.id
        self._update_outputs(message.option.id)

    def action_confirm(self) -> None:
        if self._current is None:
            self.dismiss(None)
            return
        selected = [o for o in self.out_list.selected if isinstance(o, int)]
        outputs = list(self._experiments[self._current].outputs)
        mapping = {outputs[i]: f"{self._current}#{outputs[i]}" for i in selected}
        self.dismiss(mapping)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "confirm":
            self.action_confirm()
        else:
            self.dismiss(None)

    def action_cancel(self) -> None:
        self.dismiss(None)
