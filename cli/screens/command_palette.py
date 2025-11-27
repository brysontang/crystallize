from __future__ import annotations

from difflib import SequenceMatcher
from typing import Any, Dict, List

from textual.app import ComposeResult
from textual.containers import Container
from textual.screen import ModalScreen
from textual.widgets import Input, OptionList
from textual.widgets.option_list import Option


class CommandPaletteScreen(ModalScreen[Dict[str, Any] | None]):
    """Modal command palette for quickly running experiments or graphs."""

    BINDINGS = [
        ("escape", "close", "Close"),
        ("ctrl+c", "close", "Close"),
    ]

    def __init__(self, options: List[Dict[str, Any]]) -> None:
        super().__init__()
        self._options = options
        self._option_map: Dict[str, Dict[str, Any]] = {}

    def compose(self) -> ComposeResult:
        with Container(id="command-palette"):
            yield Input(
                placeholder="Run an experiment or graph...",
                id="palette-input",
            )
            yield OptionList(id="palette-options")

    async def on_mount(self) -> None:
        self._refresh_options("")
        self.query_one(Input).focus()

    def action_close(self) -> None:
        self.dismiss(None)

    def on_input_changed(self, event: Input.Changed) -> None:
        self._refresh_options(event.value)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self._select_highlighted()

    def on_option_list_option_selected(
        self, event: OptionList.OptionSelected
    ) -> None:
        self._dismiss_option(event.option_id)

    def _refresh_options(self, query: str) -> None:
        option_list = self.query_one(OptionList)
        option_list.clear_options()
        self._option_map.clear()

        for option in self._filter_options(query):
            option_id = str(option["path"])
            self._option_map[option_id] = option
            label = self._format_label(option)
            option_list.add_option(Option(label, id=option_id))

        if option_list.option_count:
            option_list.highlighted = 0
        else:
            option_list.highlighted = None

    def _format_label(self, option: Dict[str, Any]) -> str:
        icon = option.get("icon", "🧪")
        group = option.get("group", "")
        kind = option.get("type", "")
        return f"{icon} {option['label']} ({kind}) [{group}]"

    def _filter_options(self, query: str) -> List[Dict[str, Any]]:
        if not query:
            return self._options

        needle = query.lower()
        scored: list[tuple[float, int, Dict[str, Any]]] = []
        for idx, option in enumerate(self._options):
            haystack = f"{option['label']} {option.get('group', '')} {option.get('type', '')}".lower()
            if needle in haystack:
                score = 2.0
            else:
                score = SequenceMatcher(None, needle, haystack).ratio()
            if score >= 0.25:
                scored.append((score, idx, option))

        scored.sort(key=lambda item: (-item[0], item[1]))
        return [opt for _, _, opt in scored]

    def _select_highlighted(self) -> None:
        option_list = self.query_one(OptionList)
        highlighted = option_list.highlighted
        if highlighted is None:
            return
        option = option_list.get_option_at_index(highlighted)
        if option is None:
            return
        self._dismiss_option(option.id or option.prompt)

    def _dismiss_option(self, option_id: str | None) -> None:
        if option_id is None:
            return
        selection = self._option_map.get(option_id)
        if selection is None:
            return
        self.dismiss(selection)
