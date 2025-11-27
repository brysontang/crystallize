from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Container
from textual.screen import ModalScreen
from textual.widgets import Markdown


HELP_MARKDOWN = """
# config.yaml cheat sheet

## Core keys
- `name`: Human-friendly experiment or graph name (defaults to folder).
- `description`: Short summary shown in the CLI and docs.
- `replicates`: Number of times to repeat the run (integer).
- `datasource`: Mapping of input names to loader callables or `experiment#output` refs.
- `steps`: Ordered list of step callables (functions or dotted paths).
- `treatments`: Mapping of treatment names to context overrides.
- `hypotheses`: List of `{name, verifier, metrics}` blocks.
- `outputs`: `{alias: {file_name, loader}}` describing artifacts to persist.

## CLI section
- `cli.group`: Column used to group entries in the selector (default: Experiments/Graphs).
- `cli.priority`: Lower values float to the top of lists.
- `cli.icon` / `cli.color`: Emoji and optional color for the selector.
- `cli.hidden`: Hide this experiment/graph from discovery when `true`.

## Execution toggles
- `plugins`: Extra plugin instances to load.
- `strategy`: Override execution strategy (e.g., threaded/process/async).
- `cache`: Enable/disable cache per-step (`true`/`false`).
"""


class HelpScreen(ModalScreen[None]):
    """Modal help overlay with config reference."""

    BINDINGS = [
        ("escape", "close", "Close"),
        ("q", "close", "Close"),
        ("ctrl+c", "close", "Close"),
    ]

    def compose(self) -> ComposeResult:
        with Container(id="help-container"):
            yield Markdown(HELP_MARKDOWN, id="help-markdown")

    def action_close(self) -> None:
        self.dismiss()
