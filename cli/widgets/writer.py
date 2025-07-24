"""WidgetWriter for writing to RichLog widgets."""
from __future__ import annotations

from textual.app import App
from textual.widgets import RichLog


class WidgetWriter:
    """A thread-safe, file-like object that writes to a RichLog widget."""

    def __init__(self, widget: RichLog, app: App) -> None:
        self.widget = widget
        self.app = app

    def write(self, message: str) -> None:
        if message:
            self.app.call_from_thread(self.widget.write, message)
            self.app.call_from_thread(self.widget.refresh)

    def flush(self) -> None:  # pragma: no cover - provided for file-like API
        pass

    def isatty(self) -> bool:  # pragma: no cover - same as above
        return True
