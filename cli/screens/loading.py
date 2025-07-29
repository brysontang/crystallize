from textual.screen import ModalScreen
from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import Static


class LoadingScreen(ModalScreen):
    CSS = """
    #loading-container {
        layout: vertical;
        width: 40%;
        height: 20%;
        border: round $primary;
        background: $panel;
        text-align: center;
        content-align: center middle;
    }
    """

    def compose(self) -> ComposeResult:
        with Container(id="loading-container"):
            yield Static("Loading...")
