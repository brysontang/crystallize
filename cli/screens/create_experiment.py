from __future__ import annotations

from pathlib import Path
import yaml

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.widgets import (
    Button,
    Checkbox,
    Collapsible,
    Input,
    Label,
    Static,
    SelectionList,
)
from textual.widgets.selection_list import Selection

from ..utils import create_experiment_scaffolding
from .selection_screens import ActionableSelectionList, SingleSelectionList


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
        with VerticalScroll(id="create-exp-container"):
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
            yield Checkbox(
                "Use outputs from other experiments",
                id="graph-mode",
            )
            with Vertical(id="graph-container", classes="invisible"):
                self.exp_list = SelectionList(id="exp-list")
                self.out_list = SelectionList(id="out-list")
                yield self.exp_list
                yield self.out_list
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
        base = Path("experiments")
        self._outputs: dict[str, list[str]] = {}
        self._selected: dict[str, set[str]] = {}
        if base.exists():
            for p in base.iterdir():
                cfg = p / "config.yaml"
                if cfg.exists():
                    with open(cfg) as f:
                        data = yaml.safe_load(f) or {}
                    cli_cfg = data.get("cli", {}) or {}
                    if cli_cfg.get("disabled"):
                        continue
                    outs = list((data.get("outputs") or {}).keys())
                    if outs:
                        self._outputs[p.name] = outs
        for name in sorted(self._outputs):
            self.exp_list.add_option(Selection(name, name, id=name))

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

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        if event.checkbox.id == "graph-mode":
            container = self.query_one("#graph-container")
            if event.value:
                container.remove_class("invisible")
            else:
                container.add_class("invisible")

    def on_selection_list_selected_changed(
        self, message: SelectionList.SelectedChanged
    ) -> None:
        if message.selection_list.id == "exp-list" and message.selection_list.selected:
            exp = str(message.selection_list.selected[0])
            self._current_exp = exp
            out_list = self.query_one("#out-list", SelectionList)
            out_list.clear_options()
            for out in self._outputs.get(exp, []):
                out_list.add_option(Selection(out, out, id=out))
        elif message.selection_list.id == "out-list" and hasattr(self, "_current_exp"):
            self._selected.setdefault(self._current_exp, set())
            self._selected[self._current_exp] = {
                str(val) for val in message.selection_list.selected
            }

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
        examples = self.query_one("#examples", Checkbox).value
        artifact_inputs = {}
        if self.query_one("#graph-mode", Checkbox).value:
            for exp, outs in self._selected.items():
                for out in outs:
                    alias = f"{exp}_{out}" if out in artifact_inputs else out
                    artifact_inputs[alias] = f"{exp}#{out}"
        try:
            create_experiment_scaffolding(
                name,
                directory=base,
                steps="steps" in selections,
                datasources="datasources" in selections,
                outputs="outputs" in selections,
                hypotheses="hypotheses" in selections,
                examples=examples,
                artifact_inputs=artifact_inputs or None,
            )
        except FileExistsError:
            self.app.bell()
            return
        self.dismiss(None)
