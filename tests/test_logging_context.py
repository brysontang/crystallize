# tests/test_logging_context.py
import logging

import pytest

from crystallize.utils.context import FrozenContext
from crystallize.utils.context import LoggingContext  # adjust the import!


# --------------------------------------------------------------------------- #
@pytest.fixture(autouse=True)
def silence_root_logger():
    """Keep CI output clean."""
    logging.getLogger().handlers.clear()


@pytest.fixture
def base_ctx():
    ctx = FrozenContext({"foo": 1, "bar": 2})
    ctx.metrics.add("m", 42)
    ctx.add("baz", 3)  # new key via add()
    return ctx


def test_subclass(base_ctx):
    """LoggingContext should behave like a FrozenContext."""
    log_ctx = LoggingContext(base_ctx, logging.getLogger("test"))
    assert isinstance(log_ctx, FrozenContext)
    assert log_ctx["foo"] == 1
    with pytest.raises(KeyError):
        _ = log_ctx["does_not_exist"]


def test_reads_are_tracked(base_ctx, caplog):
    logger = logging.getLogger("test")
    log_ctx = LoggingContext(base_ctx, logger)

    with caplog.at_level(logging.DEBUG, logger="test"):
        assert log_ctx["foo"] == 1
        assert log_ctx.get("bar") == 2
        assert log_ctx.get("missing", default="d") == "d"

    # 2 real reads + 1 defaulted read
    assert log_ctx.reads == {"foo": 1, "bar": 2}
    # DEBUG lines were emitted
    assert any("Read foo" in rec.message for rec in caplog.records)


def test_metrics_and_artifacts_are_shared(base_ctx):
    log_ctx = LoggingContext(base_ctx, logging.getLogger("test"))
    # Should be the EXACT same objects, not copies
    assert log_ctx.metrics is base_ctx.metrics
    assert log_ctx.artifacts is base_ctx.artifacts
    # And mutations flow through
    log_ctx.metrics.add("x", 99)
    assert base_ctx.metrics["x"] == (99,)


def test_immutability_is_preserved(base_ctx):
    log_ctx = LoggingContext(base_ctx, logging.getLogger("test"))
    # Mutating an existing key must raise
    with pytest.raises(Exception):
        log_ctx.add("foo", 999)

    # Adding a new key is fine
    log_ctx.add("new", 7)
    assert log_ctx["new"] == 7

    # Direct item assignment delegates to the inner context
    log_ctx["direct"] = 5
    assert log_ctx["direct"] == 5
