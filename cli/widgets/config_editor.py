from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import yaml

from ..utils import add_placeholder

from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.binding import Binding
from textual.containers import Container, Horizontal
from textual.widgets import Button, Footer, Input, Static, Tree
from textual.widgets._tree import TreeNode

from .style.config_editor import CSS


class IndentDumper(yaml.SafeDumper):
    def increase_indent(self, flow: bool = False, indentless: bool = False) -> None:
        return super().increase_indent(flow, False)


class ValueEditScreen(ModalScreen[str | None]):
    """Popup to edit a single value."""

    CSS = CSS

    BINDINGS = [
        Binding("ctrl+c", "cancel", "Cancel", show=False),
        Binding("q", "cancel", "Close", show=False),
        Binding("ctrl+s", "save", "Save"),
        Binding("escape", "cancel", "Cancel"),
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
        yield Footer()

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


class AddItemScreen(ModalScreen[Dict[str, str] | None]):
    """Popup to collect fields for a new config item."""

    CSS = CSS

    BINDINGS = [
        Binding("ctrl+c", "cancel", "Cancel", show=False),
        Binding("q", "cancel", "Close", show=False),
        Binding("ctrl+s", "save", "Save"),
        Binding("escape", "cancel", "Cancel"),
    ]

    def __init__(self, title: str, fields: List[str]) -> None:
        super().__init__()
        self._title = title
        self._fields = fields
        self.inputs: Dict[str, Input] = {}

    def compose(self) -> ComposeResult:
        with Container(id="edit-container"):
            yield Static(self._title, id="modal-title")
            for field in self._fields:
                inp = Input(placeholder=field, id=f"add-{field.replace(' ', '-')}")
                self.inputs[field] = inp
                yield inp
            with Horizontal(classes="button-row"):
                yield Button("Save", id="save")
                yield Button("Cancel", id="cancel")
        yield Footer()

    def action_save(self) -> None:
        values = {name: inp.value for name, inp in self.inputs.items()}
        self.dismiss(values)

    def action_cancel(self) -> None:
        self.dismiss(None)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save":
            self.action_save()
        else:
            self.action_cancel()


class AddNode(TreeNode):
    """Tree node representing an 'add item' action."""

    def __init__(
        self, tree: Tree, parent: TreeNode | None, label: str, add_type: str
    ) -> None:
        super().__init__(
            tree,
            parent,
            tree._new_id(),
            tree.process_label(label),
            None,
            expanded=False,
            allow_expand=False,
        )
        self.add_type = add_type


class ConfigTree(Tree):
    """Tree widget for displaying and editing YAML data."""

    BINDINGS = [b for b in Tree.BINDINGS if getattr(b, "key", "") != "enter"]

    VALID_KEYS = {"steps", "datasource", "hypotheses", "outputs", "treatments"}

    def __init__(self, data: Any) -> None:
        super().__init__("root")
        self.data = data
        self.show_root = False
        self._build_tree(self.root, data, [])

    def _add_add_node(self, parent: TreeNode, add_type: str) -> None:
        label = f"+ add {add_type[:-1] if add_type.endswith('s') else add_type}"
        node = AddNode(self, parent, label, add_type)
        parent._children.append(node)
        self._tree_nodes[node.id] = node
        self._invalidate()

    async def action_edit(self) -> None:
        screen = self.screen
        if screen is not None and hasattr(screen, "action_edit"):
            await screen.action_edit()

    def action_move_up(self) -> None:
        screen = self.screen
        if screen is not None and hasattr(screen, "action_move_up"):
            screen.action_move_up()

    def action_move_down(self) -> None:
        screen = self.screen
        if screen is not None and hasattr(screen, "action_move_down"):
            screen.action_move_down()

    def action_collapse_all(self) -> None:
        self.root.collapse_all()

    def action_expand_all(self) -> None:
        self.root.expand_all()

    def _build_tree(self, node: Tree.Node, value: Any, path: List[Any]) -> None:
        if isinstance(value, dict):
            for key, val in value.items():
                child = node.add(str(key))
                child.data = path + [key]
                self._build_tree(child, val, path + [key])
                if not path and key in self.VALID_KEYS:
                    self._add_add_node(child, key)
        elif isinstance(value, list):
            for idx, item in enumerate(value):
                if isinstance(item, (dict, list)):
                    label = item.get("name", f"{idx}")
                    child = node.add(label)
                    child.data = path + [idx]
                    self._build_tree(child, item, path + [idx])
                else:
                    label = str(item)
                    node.add_leaf(str(label), data=path + [idx])
            if not path:
                root_key = node.label.plain
                if root_key in self.VALID_KEYS:
                    self._add_add_node(node, root_key)
        else:
            node.add_leaf(str(value), data=path)


class ConfigEditorWidget(Container):
    """Widget for editing a config YAML file."""

    BINDINGS = [
        Binding("e", "edit", "Edit"),
        Binding("k", "move_up", "Move Up"),
        Binding("j", "move_down", "Move Down"),
    ]

    def __init__(self, path: Path) -> None:
        super().__init__(id="config-widget")
        self._path = path
        with open(path) as f:
            self._data = yaml.safe_load(f) or {}

    def compose(self) -> ComposeResult:
        yield Static("Experiment Configuration", id="modal-title")
        self.cfg_tree = ConfigTree(self._data)
        yield self.cfg_tree

    # async def on_mount(self) -> None:
    #     """Open all first level nodes when mounted."""
    #     for node in self.cfg_tree.root.children:
    #         if node.label.plain != "cli":
    #             node.expand()

    async def action_close(self) -> None:
        self.remove()

    async def action_edit(self) -> None:
        node = self.cfg_tree.cursor_node
        if node is None or node.data is None or node.parent is None or node.parent.is_root:
            return

        def _edit_sync(result: str | None) -> None:
            if result is not None:
                try:
                    new_value = yaml.safe_load(result)
                    self._set_value(node.data, new_value)
                    if not node.children:
                        node.set_label(str(new_value))
                    else:
                        pass
                except yaml.YAMLError:
                    return
                self._save()

        value = self._get_value(node.data)
        await self.app.push_screen(ValueEditScreen(str(value)), _edit_sync)

    def _save(self) -> None:
        with open(self._path, "w") as f:
            yaml.dump(self._data, f, Dumper=IndentDumper, sort_keys=False)

    def action_save(self) -> None:
        self._save()
        self.remove()

    def action_move_up(self) -> None:
        self._move_selected(-1)

    def action_move_down(self) -> None:
        self._move_selected(1)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.remove()

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
        if node is None or node.parent is None or node.parent.is_root:
            return

        parent_node = node.parent
        current_line = node.line
        siblings = list(parent_node.children)
        idx = siblings.index(node)
        new_idx = idx + delta

        if not 0 <= new_idx < len(siblings):
            return

        path = node.data
        parent_path = path[:-1]
        parent_obj = self._get_value(parent_path) if parent_path else self._data

        if isinstance(parent_obj, list):
            parent_obj[idx], parent_obj[new_idx] = parent_obj[new_idx], parent_obj[idx]
        elif isinstance(parent_obj, dict):
            keys = list(parent_obj.keys())
            keys[idx], keys[new_idx] = keys[new_idx], keys[idx]
            reordered = {k: parent_obj[k] for k in keys}
            parent_obj.clear()
            parent_obj.update(reordered)
        else:
            return

        parent_node.remove_children()
        self.cfg_tree._build_tree(parent_node, parent_obj, parent_path)
        if self.cfg_tree.validate_cursor_line(current_line + delta):
            self.cfg_tree.move_cursor_to_line(current_line + delta)
        self.cfg_tree.focus()
        self._save()

    async def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        node = event.node
        if isinstance(node, AddNode):
            await self._open_add_screen(node)
        elif not node.allow_expand:
            await self.run_action("edit")

    async def _open_add_screen(self, node: AddNode) -> None:
        add_type = node.add_type
        if add_type == "steps":
            screen = AddItemScreen("Add Step", ["name"])
        elif add_type == "datasource":
            screen = AddItemScreen("Add Datasource", ["data_key", "method"])
        elif add_type == "hypotheses":
            screen = AddItemScreen("Add Hypothesis", ["name", "verifier", "metrics"])
        elif add_type == "outputs":
            screen = AddItemScreen("Add Output", ["alias", "file_name", "loader"])
        elif add_type == "treatments":
            screen = AddItemScreen("Add Treatment", ["name", "context_field", "value"])
        else:
            return

        def _add_sync(result: Dict[str, str] | None) -> None:
            if result is None:
                return
            base = self._path.parent
            if add_type == "steps":
                self._data.setdefault("steps", []).append(result["name"])
                add_placeholder(base, "steps", result["name"])
            elif add_type == "datasource":
                ds = self._data.setdefault("datasource", {})
                ds[result["data_key"]] = result["method"]
                add_placeholder(base, "datasource", result["method"])
            elif add_type == "hypotheses":
                self._data.setdefault("hypotheses", []).append(
                    {
                        "name": result["name"],
                        "verifier": result["verifier"],
                        "metrics": result["metrics"],
                    }
                )
                add_placeholder(base, "verifier", result["verifier"])
            elif add_type == "outputs":
                op = self._data.setdefault("outputs", {})
                entry = {"file_name": result["file_name"]}
                if result.get("loader"):
                    entry["loader"] = result["loader"]
                    add_placeholder(base, "outputs", result["loader"])
                op[result["alias"]] = entry
            elif add_type == "treatments":
                tr = self._data.setdefault("treatments", {})
                try:
                    value = float(result["value"])
                    if value.is_integer():
                        value = int(value)
                except ValueError:
                    value = result["value"]
                tr[result["name"]] = {result["context_field"]: value}
            self.cfg_tree.root.remove_children()
            self.cfg_tree._build_tree(self.cfg_tree.root, self._data, [])
            self.cfg_tree.focus()
            self._save()

        await self.app.push_screen(screen, _add_sync)
