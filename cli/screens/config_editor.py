from __future__ import annotations

import yaml
from pathlib import Path
from typing import Any, List

from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Static, Tree
from textual.binding import Binding
from textual import work


class ValueEditScreen(ModalScreen[str | None]):
    """Popup to edit a single value."""

    BINDINGS = [
        ("ctrl+c", "cancel", "Cancel"),
        ("escape", "cancel", "Cancel"),
        ("enter", "save", "Save"),
    ]

    def __init__(self, value: str) -> None:
        super().__init__()
        self._value = value

    def compose(self) -> ComposeResult:
        with Container(id="edit-container"):
            yield Static("Edit Value", id="modal-title")
            self.input = Input(value=self._value, id="edit-input")
            yield self.input
            with Horizontal(classes="button-row"):
                yield Button("Save", id="save")
                yield Button("Cancel", id="cancel")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.action_save()

    def action_save(self) -> None:
        self.dismiss(self.input.value)

    def action_cancel(self) -> None:
        self.dismiss(None)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save":
            self.action_save()
        else:
            self.action_cancel()


class ConfigTree(Tree):
    """Tree widget for displaying and editing YAML data."""

    BINDINGS = [
        Binding("e", "edit", "Edit"),
        Binding("k", "move_up", "Move Up"),
        Binding("j", "move_down", "Move Down"),
        Binding("o", "expand_all", "Expand All"),
        Binding("c", "collapse_all", "Collapse All"),
    ]

    def __init__(self, data: Any) -> None:
        super().__init__("root")
        self.data = data
        self.show_root = False
        self._build_tree(self.root, data, [])

    async def action_edit(self) -> None:  # pragma: no cover - delegates
        screen = self.screen
        if screen is not None and hasattr(screen, "action_edit"):
            await screen.action_edit()

    def action_move_up(self) -> None:  # pragma: no cover - delegates
        screen = self.screen
        if screen is not None and hasattr(screen, "action_move_up"):
            screen.action_move_up()

    def action_move_down(self) -> None:  # pragma: no cover - delegates
        screen = self.screen
        if screen is not None and hasattr(screen, "action_move_down"):
            screen.action_move_down()

    def action_collapse_all(self) -> None:  # pragma: no cover - delegates
        print("collapse_all")
        self.root.collapse_all()

    def action_expand_all(self) -> None:  # pragma: no cover - delegates
        print("expand_all")
        self.root.expand_all()

    def _build_tree(self, node: Tree.Node, value: Any, path: List[Any]) -> None:
        if isinstance(value, dict):
            for key, val in value.items():
                child = node.add(str(key))
                child.data = path + [key]
                self._build_tree(child, val, path + [key])
        elif isinstance(value, list):
            for idx, item in enumerate(value):
                label = str(item) if not isinstance(item, (dict, list)) else f"{idx}"
                child = node.add(label)
                child.data = path + [idx]
                self._build_tree(child, item, path + [idx])
        else:
            node.add_leaf(str(value), data=path)


class ConfigEditorScreen(ModalScreen[None]):
    """Full screen editor for a config YAML file."""

    BINDINGS = [
        ("ctrl+c", "close", "Close"),
        ("escape", "close", "Close"),
        ("q", "close", "Close"),
        ("s", "save", "Save"),
    ]

    def __init__(self, path: Path) -> None:
        super().__init__()
        self._path = path
        with open(path) as f:
            self._data = yaml.safe_load(f) or {}

    def compose(self) -> ComposeResult:
        with Container(id="config-container"):
            yield Static("Edit Config", id="modal-title")
            self.cfg_tree = ConfigTree(self._data)
            yield self.cfg_tree
            with Horizontal(classes="button-row"):
                yield Button("Save", id="save")
                yield Button("Close", id="close")

    async def action_close(self) -> None:
        self.dismiss(None)

    async def action_edit(self) -> None:
        node = self.cfg_tree.cursor_node
        if node.parent.is_root:
            return
        if node is None or node.data is None:
            return

        def _edit_sync(result: str | None) -> None:
            print("edit_sync", result)
            if result is not None:
                try:
                    new_value = yaml.safe_load(result)
                    self._set_value(node.data, new_value)
                    print(node.children)

                    if not node.children:
                        node.set_label(str(new_value))
                    else:
                        pass
                except yaml.YAMLError:
                    return

        value = self._get_value(node.data)
        await self.app.push_screen(ValueEditScreen(str(value)), _edit_sync)

    def action_save(self) -> None:
        with open(self._path, "w") as f:
            yaml.dump(self._data, f, sort_keys=False)
        self.dismiss(None)

    def action_move_up(self) -> None:
        self._move_selected(-1)

    def action_move_down(self) -> None:
        self._move_selected(1)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save":
            with open(self._path, "w") as f:
                yaml.dump(self._data, f, sort_keys=False)
        self.dismiss(None)

    def _get_value(self, path: List[Any]) -> Any:
        val = self._data
        for p in path:
            val = val[p]
        return val

    def _set_value(self, path: List[Any], value: Any) -> None:
        obj = self._data
        for p in path[:-1]:
            obj = obj[p]
        obj[path[-1]] = value

    def _move_selected(self, delta: int) -> None:
        node = self.cfg_tree.cursor_node
        if node is None or node.data is None or not node.data:
            return
        path = node.data
        parent = self._data
        for p in path[:-1]:
            parent = parent[p]
        idx = path[-1]
        if not isinstance(parent, list):
            return
        new_idx = idx + delta
        if new_idx < 0 or new_idx >= len(parent):
            return
        parent[idx], parent[new_idx] = parent[new_idx], parent[idx]
        node.parent.children.insert(new_idx, node.parent.children.pop(idx))
        node.data[-1] = new_idx
        for i, child in enumerate(node.parent.children):
            if child.data:
                child.data[-1] = i
