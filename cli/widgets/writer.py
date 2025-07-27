import sys
import os


class WidgetWriter:
    """A thread-safe, file-like object that writes to a RichLog widget."""

    def __init__(self, widget, app, history: list[str] | None = None) -> None:
        self.widget = widget
        self.app = app
        self.history = history

    def write(self, message: str) -> None:
        if self.history is not None:
            # Store the raw message in our history list
            self.history.append(message)

        if message:
            self.app.call_from_thread(self.widget.write, message)
            self.app.call_from_thread(self.widget.refresh)

    def flush(self) -> None:
        pass

    def isatty(self) -> bool:
        return True

    def fileno(self) -> int:
        # Return a unique duplicate of the real stdout FD
        # to avoid FD list duplication in multiprocessing
        return os.dup(sys.__stdout__.fileno())
