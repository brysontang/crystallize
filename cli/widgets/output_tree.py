from __future__ import annotations

from textual.binding import Binding
from textual.widgets import Tree


class OutputTree(Tree):
    """Tree widget with custom binding for output selection."""

    BINDINGS = [b for b in Tree.BINDINGS if getattr(b, "key", "") != "enter"] + [
        Binding("enter", "toggle_output", "Select", show=True)
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
