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
    Footer,
    Static,
    Tree,
)
from textual.binding import Binding
from textual.widgets.selection_list import Selection

from ..utils import create_experiment_scaffolding
from .selection_screens import ActionableSelectionList
from .style.create_experiment import CSS


class OutputTree(Tree):
    """Tree widget with custom binding for output selection."""

    BINDINGS = [b for b in Tree.BINDINGS if getattr(b, "key", "") != "enter"] + [
        Binding("enter", "toggle_output", "Toggle", show=True)
    ]

    def action_toggle_output(self) -> None:  # pragma: no cover - delegates
        screen = self.screen
        if screen is not None and hasattr(screen, "action_toggle_output"):
            screen.action_toggle_output()

        try:
            line = self._tree_lines[self.cursor_line]
        except IndexError:
            pass
        else:
            node = line.path[-1]
            self.post_message(Tree.NodeSelected(node))


class CreateExperimentScreen(ModalScreen[None]):
    """Interactive screen for creating a new experiment folder."""

    # Add CSS
    CSS = CSS

    BINDINGS = [
        Binding("ctrl+c", "cancel", "Cancel", show=False),
        Binding("q", "cancel", "Close", show=False),
        Binding("c", "create", "Create"),
        Binding("enter", "toggle_output", "Select"),
        Binding("escape", "cancel", "Cancel"),
    ]

    name_valid = reactive(False)

    def _fmt_label(self, exp: str, out: str) -> str:
        marker = "[X]" if out in self._selected.get(exp, set()) else "[ ]"
        return f"{marker} {out}"

    def compose(self) -> ComposeResult:
        with VerticalScroll(id="create-exp-container"):
            yield Static("Create New Experiment", id="modal-title")
            yield Input(
                placeholder="Enter experiment name (lowercase, no spaces)",
                id="name-input",
            )
            yield Label(
                "[dim]Enter a name to continue[/dim]", id="name-feedback"
            )  # For validation feedback
            with Horizontal(classes="button-row"):
                yield Checkbox(
                    "Use outputs from other experiments",
                    id="graph-mode",
                )
                yield Checkbox(
                    "Add example code",
                    id="examples",
                    tooltip="Includes starter code in selected files (steps.py, verifiers.py, etc.)",
                )

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
                        "verifiers.py",
                        "hypotheses",
                        id="hypotheses",
                    )
                )
                yield self.file_list

            with Vertical(id="graph-container", classes="invisible"):
                with Collapsible(title="Select outputs to use", collapsed=False):
                    self.out_tree = OutputTree("root", id="out-tree")
                    self.out_tree.show_root = False
                    yield self.out_tree

            with Horizontal(classes="button-row"):
                yield Button("Create", variant="success", id="create")
                yield Button("Cancel", variant="error", id="cancel")
        yield Footer()

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
                    outs = list((data.get("outputs") or {}).keys())
                    if outs:
                        self._outputs[p.name] = outs
        if hasattr(self, "out_tree"):
            for name in sorted(self._outputs):
                node = self.out_tree.root.add(name)
                for out in self._outputs[name]:
                    leaf = node.add_leaf(self._fmt_label(name, out))
                    leaf.data = (name, out)

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

    def action_toggle_output(self) -> None:
        if hasattr(self, "out_tree"):
            node = self.out_tree.cursor_node
            if node is not None and node.data is not None:
                exp, out = node.data
                selected = self._selected.setdefault(exp, set())
                if out in selected:
                    selected.remove(out)
                else:
                    selected.add(out)
                node.set_label(self._fmt_label(exp, out))

    def action_cancel(self) -> None:
        self.dismiss(None)

    def action_create(self) -> None:
        if self.name_valid:
            self._create()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "create" and self.name_valid:
            self._create()
        else:
            return

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
