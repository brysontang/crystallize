"""Tests for crystallize.run()"""

import pytest
from crystallize import run, RunResult, Context


class TestBasicRun:
    """Basic functionality tests."""

    def test_simple_function(self):
        def fn(config):
            return config["x"] * 2

        result = run(
            fn=fn,
            configs={"test": {"x": 5}},
            replicates=3,
            progress=False,
        )

        assert isinstance(result, RunResult)
        assert result.results["test"] == [10, 10, 10]

    def test_multiple_configs(self):
        def fn(config):
            return config["value"]

        result = run(
            fn=fn,
            configs={"a": {"value": 1}, "b": {"value": 2}},
            replicates=2,
            progress=False,
        )

        assert result.results["a"] == [1, 1]
        assert result.results["b"] == [2, 2]

    def test_with_context(self):
        def fn(config, ctx):
            ctx.record("doubled", config["x"] * 2)
            return config["x"]

        result = run(
            fn=fn,
            configs={"test": {"x": 5}},
            replicates=3,
            progress=False,
        )

        assert result.metrics["test"]["doubled"] == [10, 10, 10]

    def test_default_config(self):
        def fn(config):
            return 42

        result = run(fn=fn, replicates=2, progress=False)

        assert "baseline" in result.results
        assert result.results["baseline"] == [42, 42]


class TestSeeding:
    """Reproducibility tests."""

    def test_seed_reproducibility(self):
        import random

        def fn(config):
            return random.random()

        result1 = run(fn=fn, configs={"test": {}}, replicates=5, seed=42, progress=False)
        result2 = run(fn=fn, configs={"test": {}}, replicates=5, seed=42, progress=False)

        assert result1.results["test"] == result2.results["test"]

    def test_different_seeds_different_results(self):
        import random

        def fn(config):
            return random.random()

        result1 = run(fn=fn, configs={"test": {}}, replicates=5, seed=42, progress=False)
        result2 = run(fn=fn, configs={"test": {}}, replicates=5, seed=123, progress=False)

        assert result1.results["test"] != result2.results["test"]


class TestHypothesis:
    """Hypothesis testing."""

    def test_hypothesis_parsing(self):
        def fn(config, ctx):
            ctx.record("score", config["value"])
            return config["value"]

        result = run(
            fn=fn,
            configs={"high": {"value": 10}, "low": {"value": 1}},
            replicates=5,
            hypothesis="high.score > low.score",
            progress=False,
        )

        assert result.hypothesis_result is not None
        assert result.hypothesis_result.supported is True
        assert result.hypothesis_result.left_mean == 10
        assert result.hypothesis_result.right_mean == 1

    def test_hypothesis_not_supported(self):
        def fn(config, ctx):
            ctx.record("score", config["value"])
            return config["value"]

        result = run(
            fn=fn,
            configs={"high": {"value": 10}, "low": {"value": 1}},
            replicates=5,
            hypothesis="low.score > high.score",
            progress=False,
        )

        assert result.hypothesis_result is not None
        assert result.hypothesis_result.supported is False

    def test_invalid_hypothesis_format(self):
        def fn(config):
            return 1

        with pytest.raises(ValueError, match="Invalid hypothesis"):
            run(fn=fn, configs={"a": {}}, hypothesis="invalid", progress=False)

    def test_hypothesis_references_missing_config(self):
        def fn(config):
            return 1

        with pytest.raises(ValueError, match="references 'missing'"):
            run(
                fn=fn,
                configs={"a": {}},
                hypothesis="missing.x > a.x",
                progress=False,
            )


class TestOnEvent:
    """Event callback tests."""

    def test_events_fired(self):
        events = []

        def fn(config, ctx):
            ctx.record("x", 1)
            return 1

        run(
            fn=fn,
            configs={"test": {}},
            replicates=2,
            on_event=lambda e: events.append(e),
            progress=False,
        )

        event_types = [e["type"] for e in events]
        assert "start" in event_types
        assert "replicate_start" in event_types
        assert "replicate_end" in event_types
        assert "metric" in event_types
        assert "end" in event_types

    def test_metric_event_has_value(self):
        events = []

        def fn(config, ctx):
            ctx.record("score", 42)
            return 1

        run(
            fn=fn,
            configs={"test": {}},
            replicates=1,
            on_event=lambda e: events.append(e),
            progress=False,
        )

        metric_events = [e for e in events if e["type"] == "metric"]
        assert len(metric_events) == 1
        assert metric_events[0]["metric"] == "score"
        assert metric_events[0]["value"] == 42


class TestContext:
    """Context recording tests."""

    def test_record_multiple_metrics(self):
        def fn(config, ctx):
            ctx.record("a", 1)
            ctx.record("b", 2)
            return 0

        result = run(fn=fn, configs={"test": {}}, replicates=1, progress=False)

        assert result.metrics["test"]["a"] == [1]
        assert result.metrics["test"]["b"] == [2]

    def test_record_with_tags(self):
        ctx = Context(replicate=0, config_name="test")
        ctx.record("x", 1, tags={"source": "a"})
        ctx.record("x", 2, tags={"source": "b"})

        assert ctx.metrics["x"] == [1, 2]
        assert ctx._tags["x"] == [{"source": "a"}, {"source": "b"}]


class TestResultSerialization:
    """Result persistence tests."""

    def test_to_dict(self):
        def fn(config, ctx):
            ctx.record("x", 1)
            return 1

        result = run(fn=fn, configs={"test": {}}, replicates=1, progress=False)
        data = result.to_dict()

        assert "results" in data
        assert "metrics" in data
        assert data["results"]["test"] == [1]
        assert data["metrics"]["test"]["x"] == [1]

    def test_to_json_string(self):
        import json

        def fn(config):
            return 1

        result = run(fn=fn, configs={"test": {}}, replicates=1, progress=False)
        json_str = result.to_json()

        assert json_str is not None
        data = json.loads(json_str)
        assert "timestamp" in data
        assert data["results"]["test"] == [1]

    def test_to_json_file(self, tmp_path):
        def fn(config):
            return 1

        result = run(fn=fn, configs={"test": {}}, replicates=1, progress=False)
        path = tmp_path / "result.json"
        result.to_json(str(path))

        assert path.exists()
