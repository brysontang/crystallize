"""Tests for the explore() function and Experiment class."""

import tempfile

from crystallize import explore, Experiment


class TestExplore:
    """Tests for basic explore() functionality."""

    def test_simple_explore(self):
        """explore() returns an Experiment with results and metrics."""

        def fn(config, ctx):
            ctx.record("score", config["x"] * 2)
            return {"value": config["x"]}

        exp = explore(
            fn=fn,
            configs={"a": {"x": 1}, "b": {"x": 2}},
            replicates=3,
            progress=False,
        )

        assert isinstance(exp, Experiment)
        assert exp.run_id.startswith("exp_")
        assert exp.lineage_id.startswith("lin_")
        assert len(exp.results["a"]) == 3
        assert len(exp.results["b"]) == 3
        assert exp.metrics["a"]["score"] == [2, 2, 2]
        assert exp.metrics["b"]["score"] == [4, 4, 4]

    def test_explore_with_seed(self):
        """Seeded explore() produces reproducible results."""
        import random

        def fn(config, ctx):
            ctx.record("random", random.random())
            return None

        exp1 = explore(
            fn=fn,
            configs={"test": {}},
            replicates=5,
            seed=42,
            progress=False,
        )

        exp2 = explore(
            fn=fn,
            configs={"test": {}},
            replicates=5,
            seed=42,
            progress=False,
        )

        assert exp1.metrics["test"]["random"] == exp2.metrics["test"]["random"]

    def test_explore_generates_config_fingerprints(self):
        """explore() generates fingerprints for each config."""

        def fn(config, ctx):
            ctx.record("x", 1)

        exp = explore(
            fn=fn,
            configs={"a": {"model": "gpt-4"}, "b": {"model": "claude"}},
            replicates=1,
            progress=False,
        )

        assert "a" in exp.config_fingerprints
        assert "b" in exp.config_fingerprints
        # Different configs should have different fingerprints
        assert exp.config_fingerprints["a"] != exp.config_fingerprints["b"]

    def test_explore_stores_function_fingerprint(self):
        """explore() captures function fingerprint."""

        def fn(config, ctx):
            ctx.record("x", 1)

        exp = explore(
            fn=fn,
            configs={"test": {}},
            replicates=1,
            progress=False,
        )

        assert "sha256" in exp.fn_fingerprint
        assert "method" in exp.fn_fingerprint


class TestExperimentMethods:
    """Tests for Experiment methods."""

    def test_hidden_variables_report(self):
        """hidden_variables() returns a report."""

        def fn(config, ctx):
            ctx.record("x", 1)

        exp = explore(
            fn=fn,
            configs={"test": {}},
            replicates=1,
            progress=False,
        )

        report = exp.hidden_variables()
        assert hasattr(report, "items")
        assert hasattr(report, "pretty")

    def test_protocol_diff(self):
        """protocol_diff() returns a diff object."""

        def fn(config, ctx):
            ctx.record("x", config.get("x", 0))

        exp = explore(
            fn=fn,
            configs={"a": {"x": 1}, "b": {"x": 2}},
            replicates=1,
            progress=False,
        )

        diff = exp.protocol_diff()
        assert hasattr(diff, "pairs")
        assert hasattr(diff, "pretty")

    def test_to_dict(self):
        """Experiment.to_dict() returns serializable dict."""

        def fn(config, ctx):
            ctx.record("x", 1)

        exp = explore(
            fn=fn,
            configs={"test": {}},
            replicates=1,
            progress=False,
        )

        d = exp.to_dict()
        assert "run_id" in d
        assert "lineage_id" in d
        assert "metrics" in d
        assert "protocol" in d


class TestExploreWithCustomStore:
    """Tests for explore() with custom store root."""

    def test_custom_store_root(self):
        """explore() can use a custom store root."""
        from crystallize.store import reset_store

        def fn(config, ctx):
            ctx.record("x", 1)

        with tempfile.TemporaryDirectory() as tmpdir:
            # Reset global store before test
            reset_store()

            _exp = explore(  # noqa: F841
                fn=fn,
                configs={"test": {}},
                replicates=1,
                progress=False,
                store_root=tmpdir,
            )

            # Check that files were created
            import os

            assert os.path.exists(os.path.join(tmpdir, "runs"))
            assert os.path.exists(os.path.join(tmpdir, "ledger"))

            # Reset again after test to not affect other tests
            reset_store()


class TestExploreOnEvent:
    """Tests for explore() on_event callback."""

    def test_events_fired(self):
        """explore() fires events during execution."""
        events = []

        def on_event(e):
            events.append(e)

        def fn(config, ctx):
            ctx.record("x", 1)

        explore(
            fn=fn,
            configs={"test": {}},
            replicates=2,
            on_event=on_event,
            progress=False,
        )

        event_types = [e["type"] for e in events]
        assert "start" in event_types
        assert "replicate_start" in event_types
        assert "replicate_end" in event_types
        assert "metric" in event_types
        assert "end" in event_types
