"""Tests for DX improvements: standalone_context, ctx.record, Result persistence."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from crystallize import (
    standalone_context,
    quick_experiment,
    FrozenContext,
    data_source,
    get_datasource,
    list_datasources,
    register_datasource,
)
from crystallize.datasources.registry import clear_registry
from crystallize.experiments.result import Result
from crystallize.experiments.result_structs import (
    ExperimentMetrics,
    TreatmentMetrics,
    HypothesisResult,
)


class TestStandaloneContext:
    """Tests for standalone_context() helper."""

    def test_creates_frozen_context(self):
        ctx = standalone_context()
        assert isinstance(ctx, FrozenContext)

    def test_with_initial_data(self):
        ctx = standalone_context({"foo": "bar", "num": 42})
        assert ctx["foo"] == "bar"
        assert ctx["num"] == 42

    def test_empty_by_default(self):
        ctx = standalone_context()
        assert ctx.as_dict() == {}

    def test_metrics_available(self):
        ctx = standalone_context()
        ctx.metrics.add("loss", 0.5)
        assert ctx.metrics["loss"] == (0.5,)

    def test_record_shortcut(self):
        ctx = standalone_context()
        ctx.record("accuracy", 0.95)
        assert ctx.metrics["accuracy"] == (0.95,)


class TestCtxRecord:
    """Tests for ctx.record() explicit metrics API."""

    def test_record_basic(self):
        ctx = standalone_context()
        ctx.record("metric_a", 100)
        assert ctx.metrics["metric_a"] == (100,)

    def test_record_with_tags(self):
        ctx = standalone_context()
        ctx.record("loss", 0.5, tags={"epoch": 1, "split": "train"})
        ctx.record("loss", 0.3, tags={"epoch": 2, "split": "train"})

        assert ctx.metrics["loss"] == (0.5, 0.3)
        assert ctx.metrics.get_tags("loss") == (
            {"epoch": 1, "split": "train"},
            {"epoch": 2, "split": "train"},
        )

    def test_record_without_tags(self):
        ctx = standalone_context()
        ctx.record("val", 1)
        ctx.record("val", 2)

        assert ctx.metrics.get_tags("val") == ({}, {})

    def test_metrics_add_also_supports_tags(self):
        ctx = standalone_context()
        ctx.metrics.add("x", 10, tags={"type": "test"})
        assert ctx.metrics.get_tags("x") == ({"type": "test"},)


class TestResultPersistence:
    """Tests for Result.to_dict(), to_json(), to_parquet()."""

    @pytest.fixture
    def sample_result(self):
        """Create a sample Result for testing."""
        baseline = TreatmentMetrics(metrics={"loss": [0.5, 0.4], "acc": [0.9, 0.92]})
        treatments = {
            "treatment_a": TreatmentMetrics(
                metrics={"loss": [0.3, 0.25], "acc": [0.95, 0.96]}
            )
        }
        hypotheses = [
            HypothesisResult(
                name="improvement_check",
                results={"treatment_a": {"improvement": 0.1}},
                ranking={"treatment_a": 1},
            )
        ]
        metrics = ExperimentMetrics(
            baseline=baseline, treatments=treatments, hypotheses=hypotheses
        )
        return Result(
            metrics=metrics,
            artifacts={"model": b"binary_data"},
            errors={},
            provenance={"pipeline_signature": "abc123"},
        )

    def test_to_dict(self, sample_result):
        data = sample_result.to_dict()

        assert "timestamp" in data
        assert "metrics" in data
        assert "hypotheses" in data
        assert "artifacts" in data
        assert "provenance" in data

        # Check metrics structure
        assert data["metrics"]["baseline"]["loss"] == [0.5, 0.4]
        assert data["metrics"]["treatments"]["treatment_a"]["acc"] == [0.95, 0.96]

        # Check hypotheses
        assert len(data["hypotheses"]) == 1
        assert data["hypotheses"][0]["name"] == "improvement_check"

        # Artifacts are just names (not binary data)
        assert data["artifacts"] == ["model"]

    def test_to_json_string(self, sample_result):
        json_str = sample_result.to_json()

        assert json_str is not None
        data = json.loads(json_str)
        assert data["metrics"]["baseline"]["loss"] == [0.5, 0.4]

    def test_to_json_file(self, sample_result):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "result.json"
            sample_result.to_json(path)

            assert path.exists()
            data = json.loads(path.read_text())
            assert data["metrics"]["baseline"]["acc"] == [0.9, 0.92]

    def test_to_parquet(self, sample_result):
        pytest.importorskip("pandas")
        pytest.importorskip("pyarrow")

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "result.parquet"
            sample_result.to_parquet(path)

            assert path.exists()

            import pandas as pd

            df = pd.read_parquet(path)

            # Should have rows for baseline and treatment metrics
            assert len(df) == 4  # 2 metrics x 2 conditions
            assert set(df["condition"]) == {"baseline", "treatment_a"}
            assert set(df["metric"]) == {"loss", "acc"}

    def test_to_parquet_no_pandas(self, sample_result, monkeypatch):
        # Simulate pandas not being installed
        import builtins

        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "pandas":
                raise ImportError("No module named 'pandas'")
            return original_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", mock_import)

        with pytest.raises(ImportError, match="pandas is required"):
            sample_result.to_parquet("test.parquet")


class TestDatasourceRegistry:
    """Tests for datasource registry and string-based lookups."""

    @pytest.fixture(autouse=True)
    def clean_registry(self):
        """Clear registry before and after each test."""
        clear_registry()
        yield
        clear_registry()

    def test_register_and_get(self):
        @data_source
        def my_data(ctx):
            return [1, 2, 3]

        ds = my_data()
        register_datasource("my_data", ds)

        retrieved = get_datasource("my_data")
        ctx = standalone_context()
        assert retrieved.fetch(ctx) == [1, 2, 3]

    def test_auto_register_with_decorator(self):
        @data_source(register=True)
        def auto_registered(ctx):
            return "auto"

        # Should be automatically registered with function name
        ds = get_datasource("auto_registered")
        ctx = standalone_context()
        assert ds.fetch(ctx) == "auto"

    def test_auto_register_with_custom_name(self):
        @data_source("custom_name", register=True)
        def original_name(ctx):
            return "custom"

        ds = get_datasource("custom_name")
        ctx = standalone_context()
        assert ds.fetch(ctx) == "custom"

    def test_list_datasources(self):
        @data_source(register=True)
        def ds_one(ctx):
            return 1

        @data_source(register=True)
        def ds_two(ctx):
            return 2

        names = list_datasources()
        assert "ds_one" in names
        assert "ds_two" in names

    def test_get_nonexistent_raises(self):
        with pytest.raises(KeyError, match="No datasource registered"):
            get_datasource("nonexistent")

    def test_duplicate_registration_raises(self):
        @data_source(register=True)
        def duplicate(ctx):
            return 1

        with pytest.raises(ValueError, match="already registered"):
            register_datasource("duplicate", duplicate())

    def test_decorator_without_register_does_not_register(self):
        @data_source
        def not_registered(ctx):
            return "nope"

        assert "not_registered" not in list_datasources()

    def test_backwards_compatible_simple_decorator(self):
        # Original usage pattern should still work
        @data_source
        def simple(ctx):
            return 42

        ds = simple()
        ctx = standalone_context()
        assert ds.fetch(ctx) == 42


class TestQuickExperiment:
    """Tests for quick_experiment() on-ramp function."""

    def test_basic_usage(self):
        def my_fn(config):
            return config["value"] * 2

        results = quick_experiment(
            fn=my_fn,
            configs={"test": {"value": 5}},
            replicates=3,
        )

        assert "test" in results
        assert len(results["test"]) == 3
        assert all(r == 10 for r in results["test"])

    def test_multiple_configs(self):
        def my_fn(config):
            return config["x"]

        results = quick_experiment(
            fn=my_fn,
            configs={"a": {"x": 1}, "b": {"x": 2}},
            replicates=2,
        )

        assert results["a"] == [1, 1]
        assert results["b"] == [2, 2]

    def test_with_seed_reproducibility(self):
        import random

        def random_fn(config):
            return random.random()

        # Run twice with same seed
        results1 = quick_experiment(
            fn=random_fn,
            configs={"test": {}},
            replicates=3,
            seed=42,
        )
        results2 = quick_experiment(
            fn=random_fn,
            configs={"test": {}},
            replicates=3,
            seed=42,
        )

        assert results1["test"] == results2["test"]

    def test_with_context_parameter(self):
        def my_fn(config, ctx):
            return {"config": config["name"], "replicate": ctx["replicate"]}

        results = quick_experiment(
            fn=my_fn,
            configs={"foo": {"name": "foo"}},
            replicates=2,
        )

        assert results["foo"][0] == {"config": "foo", "replicate": 0}
        assert results["foo"][1] == {"config": "foo", "replicate": 1}

    def test_no_config(self):
        counter = {"value": 0}

        def my_fn():
            counter["value"] += 1
            return counter["value"]

        results = quick_experiment(fn=my_fn, replicates=3)

        assert "baseline" in results
        assert results["baseline"] == [1, 2, 3]

    def test_verbose_mode(self, capsys):
        def my_fn(config):
            return 1

        quick_experiment(
            fn=my_fn,
            configs={"test": {}},
            replicates=2,
            verbose=True,
        )

        captured = capsys.readouterr()
        assert "Running test replicate 1/2" in captured.out
        assert "Running test replicate 2/2" in captured.out
        assert "Done!" in captured.out
