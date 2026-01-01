"""Extended tests for FrozenContext and LoggingContext."""

import logging

import pytest

from crystallize.utils.context import FrozenContext, LoggingContext
from crystallize.utils.exceptions import ContextMutationError


class TestFrozenContextDeepNested:
    """Tests for FrozenContext with deeply nested values."""

    def test_nested_dict_isolation(self):
        original = {"outer": {"inner": {"deep": [1, 2, 3]}}}
        ctx = FrozenContext(original)

        # Modify original after context creation
        original["outer"]["inner"]["deep"].append(4)
        original["outer"]["new_key"] = "new_value"

        # Context should have the original values
        retrieved = ctx["outer"]
        assert retrieved["inner"]["deep"] == [1, 2, 3]
        assert "new_key" not in retrieved

    def test_nested_list_isolation(self):
        original = {"items": [[1, 2], [3, 4]]}
        ctx = FrozenContext(original)

        # Modify original
        original["items"][0].append(99)
        original["items"].append([5, 6])

        retrieved = ctx["items"]
        assert retrieved == [[1, 2], [3, 4]]

    def test_retrieved_value_cannot_affect_context(self):
        ctx = FrozenContext({"data": {"nested": [1, 2, 3]}})

        # Get and modify
        data = ctx["data"]
        data["nested"].append(4)
        data["new"] = "value"

        # Context should be unchanged
        fresh = ctx["data"]
        assert fresh["nested"] == [1, 2, 3]
        assert "new" not in fresh

    def test_get_with_nested_default(self):
        ctx = FrozenContext({})
        default = {"a": [1, 2]}
        result = ctx.get("missing", default)

        # Modify result
        result["a"].append(3)

        # Default should be unchanged (deep copied)
        assert default["a"] == [1, 2]

    def test_as_dict_returns_immutable_view(self):
        ctx = FrozenContext({"x": {"y": 1}})
        view = ctx.as_dict()

        # MappingProxyType doesn't allow modification
        with pytest.raises(TypeError):
            view["new"] = "value"


class TestFrozenContextMutation:
    """Tests for FrozenContext mutation protection."""

    def test_cannot_mutate_existing_key(self):
        ctx = FrozenContext({"key": "original"})
        with pytest.raises(ContextMutationError, match="Cannot mutate existing key"):
            ctx["key"] = "new_value"

    def test_can_add_new_key(self):
        ctx = FrozenContext({"existing": 1})
        ctx["new"] = 2
        assert ctx["new"] == 2

    def test_add_method_same_as_setitem(self):
        ctx = FrozenContext({})
        ctx.add("key", "value")
        assert ctx["key"] == "value"

        with pytest.raises(ContextMutationError):
            ctx.add("key", "different")


class TestFrozenMetrics:
    """Tests for FrozenContext.metrics functionality."""

    def test_metrics_add_and_retrieve(self):
        ctx = FrozenContext({})
        ctx.metrics.add("loss", 0.5)
        ctx.metrics.add("loss", 0.4)
        ctx.metrics.add("loss", 0.3)

        assert ctx.metrics["loss"] == (0.5, 0.4, 0.3)

    def test_metrics_returns_tuple(self):
        ctx = FrozenContext({})
        ctx.metrics.add("x", 1)
        result = ctx.metrics["x"]
        assert isinstance(result, tuple)

    def test_metrics_as_dict(self):
        ctx = FrozenContext({})
        ctx.metrics.add("a", 1)
        ctx.metrics.add("b", 2)
        d = ctx.metrics.as_dict()
        assert d["a"] == (1,)
        assert d["b"] == (2,)


class TestLoggingContextProxy:
    """Tests for LoggingContext proxy behavior."""

    def test_logging_context_records_reads(self):
        inner = FrozenContext({"x": 1, "y": 2})
        ctx = LoggingContext(inner)

        _ = ctx["x"]
        _ = ctx["y"]

        assert ctx.reads == {"x": 1, "y": 2}

    def test_logging_context_get_records_read(self):
        inner = FrozenContext({"key": "value"})
        ctx = LoggingContext(inner)

        result = ctx.get("key")
        assert result == "value"
        assert "key" in ctx.reads

    def test_logging_context_get_missing_key_no_read(self):
        inner = FrozenContext({})
        ctx = LoggingContext(inner)

        result = ctx.get("missing", "default")
        assert result == "default"
        assert "missing" not in ctx.reads

    def test_logging_context_delegates_setitem(self):
        inner = FrozenContext({})
        ctx = LoggingContext(inner)

        ctx["new_key"] = "new_value"
        assert inner["new_key"] == "new_value"

    def test_logging_context_delegates_add(self):
        inner = FrozenContext({})
        ctx = LoggingContext(inner)

        ctx.add("key", "value")
        assert inner["key"] == "value"

    def test_logging_context_shares_metrics(self):
        inner = FrozenContext({})
        ctx = LoggingContext(inner)

        ctx.metrics.add("metric", 1)
        assert inner.metrics["metric"] == (1,)

    def test_logging_context_shares_artifacts(self):
        inner = FrozenContext({})
        ctx = LoggingContext(inner)

        # Same artifacts object
        assert ctx.artifacts is inner.artifacts

    def test_logging_context_as_dict(self):
        inner = FrozenContext({"a": 1})
        ctx = LoggingContext(inner)

        assert ctx.as_dict() == inner.as_dict()

    def test_logging_context_getattr_fallback(self):
        inner = FrozenContext({})
        inner._custom_attr = "custom_value"
        ctx = LoggingContext(inner)

        # Falls back to inner context
        assert ctx._custom_attr == "custom_value"

    def test_logging_context_logs_debug_on_read(self, caplog):
        inner = FrozenContext({"key": "value"})
        logger = logging.getLogger("test_logger")
        ctx = LoggingContext(inner, logger=logger)

        with caplog.at_level(logging.DEBUG, logger="test_logger"):
            _ = ctx["key"]

        assert any("Read key" in r.message for r in caplog.records)

    def test_logging_context_mutation_protection(self):
        inner = FrozenContext({"existing": 1})
        ctx = LoggingContext(inner)

        with pytest.raises(ContextMutationError):
            ctx["existing"] = 2


class TestFrozenContextEdgeCases:
    """Edge cases for FrozenContext."""

    def test_context_with_none_values(self):
        ctx = FrozenContext({"key": None})
        assert ctx["key"] is None
        assert ctx.get("key") is None

    def test_context_with_empty_collections(self):
        ctx = FrozenContext({"list": [], "dict": {}, "tuple": ()})
        assert ctx["list"] == []
        assert ctx["dict"] == {}
        # Tuples don't need deep copy
        assert ctx.get("tuple") == ()

    def test_context_get_with_none_default(self):
        ctx = FrozenContext({})
        assert ctx.get("missing", None) is None
        assert ctx.get("missing") is None

    def test_context_with_custom_logger(self):
        custom_logger = logging.getLogger("custom")
        ctx = FrozenContext({}, logger=custom_logger)
        assert ctx.logger is custom_logger

    def test_context_default_logger(self):
        ctx = FrozenContext({})
        assert ctx.logger.name == "crystallize"
