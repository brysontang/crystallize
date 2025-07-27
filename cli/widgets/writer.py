# """WidgetWriter for writing to RichLog widgets."""

# from __future__ import annotations

# import sys

# from textual.app import App
# from textual.widgets import RichLog


# class WidgetWriter:
#     """A thread-safe, file-like object that writes to a RichLog widget."""

#     def __init__(self, widget: RichLog, app: App) -> None:
#         self.widget = widget
#         self.app = app

#     def write(self, message: str) -> None:
#         if message:
#             self.app.call_from_thread(self.widget.write, message)
#             self.app.call_from_thread(self.widget.refresh)

#     def flush(self) -> None:  # pragma: no cover - provided for file-like API
#         pass

#     def isatty(self) -> bool:  # pragma: no cover - same as above
#         return True

#     def fileno(self) -> int:  # NEW ✨
#         # Fall back to the original stream’s FD so
#         # multiprocessing can safely duplicate it.
#         return sys.__stdout__.fileno()


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
