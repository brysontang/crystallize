import logging

from cli.status_plugin import ContextFilter, TextualLoggingPlugin, WidgetLogHandler
from cli.widgets.writer import WidgetWriter


class DummyWidget:
    def write(self, msg: str) -> None:  # pragma: no cover - simple stub
        pass

    def refresh(self) -> None:  # pragma: no cover - simple stub
        pass


class DummyApp:
    def call_from_thread(self, func, *args, **kwargs) -> None:  # pragma: no cover
        func(*args, **kwargs)


class DummyExperiment:
    replicates = 1
    treatments: list = []
    hypotheses: list = []

    def get_plugin(self, cls):  # pragma: no cover - simple stub
        return None


def test_textual_logging_plugin_resets_handlers() -> None:
    logger = logging.getLogger("crystallize")
    logger.handlers.clear()
    logger.filters.clear()

    writer = WidgetWriter(DummyWidget(), DummyApp(), [])
    plugin = TextualLoggingPlugin(writer=writer)
    exp = DummyExperiment()

    plugin.before_run(exp)
    handlers = [h for h in logger.handlers if isinstance(h, WidgetLogHandler)]
    assert len(handlers) == 1
    first_id = id(handlers[0])
    assert sum(isinstance(f, ContextFilter) for f in logger.filters) == 1
    assert not logger.propagate

    plugin.before_run(exp)
    handlers = [h for h in logger.handlers if isinstance(h, WidgetLogHandler)]
    assert len(handlers) == 1
    assert id(handlers[0]) != first_id
    second_id = id(handlers[0])
    assert sum(isinstance(f, ContextFilter) for f in logger.filters) == 1
    assert not logger.propagate

    no_writer = TextualLoggingPlugin(writer=None)
    no_writer.before_run(exp)
    handlers = [h for h in logger.handlers if isinstance(h, WidgetLogHandler)]
    assert len(handlers) == 1
    assert id(handlers[0]) == second_id
    assert sum(isinstance(f, ContextFilter) for f in logger.filters) == 1
    assert not logger.propagate
