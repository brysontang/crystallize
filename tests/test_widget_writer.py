from __future__ import annotations

import os

from cli.widgets.writer import WidgetWriter


class DummyWidget:
    def write(self, msg: str) -> None:  # pragma: no cover - stub
        pass

    def refresh(self) -> None:  # pragma: no cover - stub
        pass


class DummyApp:
    def call_from_thread(self, func, *args, **kwargs) -> None:  # pragma: no cover
        func(*args, **kwargs)


def test_widget_writer_caches_fd_and_closes() -> None:
    writer = WidgetWriter(DummyWidget(), DummyApp())

    fd1 = writer.fileno()
    fd2 = writer.fileno()
    assert fd1 == fd2

    writer.close()

    try:
        os.fstat(fd1)
    except OSError:
        pass
    else:  # pragma: no cover - fd still open
        raise AssertionError("duplicate fd was not closed")

    fd3 = writer.fileno()
    os.fstat(fd3)
    writer.close()
