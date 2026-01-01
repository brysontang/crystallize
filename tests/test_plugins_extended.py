"""Extended tests for plugins: SeedPlugin, ArtifactPlugin pruning, and execution plugins."""

import tempfile
from pathlib import Path

import pytest

from crystallize.datasources.datasource import DataSource
from crystallize.experiments.experiment import Experiment
from crystallize.pipelines.pipeline import Pipeline
from crystallize.pipelines.pipeline_step import PipelineStep
from crystallize.plugins.execution import (
    AsyncExecution,
    ParallelExecution,
    SerialExecution,
)
from crystallize.plugins.plugins import ArtifactPlugin, SeedPlugin
from crystallize.utils.context import FrozenContext


class DummySource(DataSource):
    def fetch(self, ctx):
        return 0


class DummyStep(PipelineStep):
    def __call__(self, data, ctx):
        return data

    @property
    def params(self):
        return {}


def _make_experiment(plugins=None) -> Experiment:
    pipeline = Pipeline([DummyStep()])
    ds = DummySource()
    return Experiment(datasource=ds, pipeline=pipeline, plugins=plugins or [])


class TestSeedPluginInitHook:
    """Tests for SeedPlugin.init_hook() random seed generation."""

    def test_init_hook_generates_seed_when_none(self):
        plugin = SeedPlugin(seed=None)
        exp = _make_experiment([plugin])
        plugin.init_hook(exp)
        assert plugin.seed is not None
        assert 0 <= plugin.seed < 2**32

    def test_init_hook_preserves_explicit_seed(self):
        plugin = SeedPlugin(seed=12345)
        exp = _make_experiment([plugin])
        plugin.init_hook(exp)
        assert plugin.seed == 12345

    def test_before_replicate_with_auto_seed_true(self):
        plugin = SeedPlugin(seed=1000, auto_seed=True)
        exp = _make_experiment([plugin])
        ctx = FrozenContext({"replicate": 0})
        plugin.before_replicate(exp, ctx)
        seed_used_0 = ctx.get("seed_used")

        ctx2 = FrozenContext({"replicate": 1})
        plugin.before_replicate(exp, ctx2)
        seed_used_1 = ctx2.get("seed_used")

        # Different replicates should get different seeds
        assert seed_used_0 != seed_used_1

    def test_before_replicate_with_auto_seed_false(self):
        plugin = SeedPlugin(seed=1000, auto_seed=False)
        exp = _make_experiment([plugin])
        ctx = FrozenContext({"replicate": 0})
        plugin.before_replicate(exp, ctx)
        seed_used_0 = ctx.get("seed_used")

        ctx2 = FrozenContext({"replicate": 1})
        plugin.before_replicate(exp, ctx2)
        seed_used_1 = ctx2.get("seed_used")

        # Same seed for all replicates
        assert seed_used_0 == seed_used_1 == 1000

    def test_before_replicate_with_custom_seed_fn(self):
        called_with = []

        def custom_seed_fn(seed):
            called_with.append(seed)

        plugin = SeedPlugin(seed=42, seed_fn=custom_seed_fn)
        exp = _make_experiment([plugin])
        ctx = FrozenContext({"replicate": 0})
        plugin.before_replicate(exp, ctx)
        assert len(called_with) == 1
        assert called_with[0] == 42

    def test_before_replicate_generates_seed_if_still_none(self):
        # Simulates case where init_hook wasn't called
        plugin = SeedPlugin(seed=None)
        exp = _make_experiment([plugin])
        ctx = FrozenContext({"replicate": 0})
        plugin.before_replicate(exp, ctx)
        assert plugin.seed is not None


class TestArtifactPluginPruning:
    """Tests for ArtifactPlugin pruning methods."""

    def test_prune_old_versions_keeps_recent(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            plugin = ArtifactPlugin(root_dir=tmpdir, versioned=True, artifact_retention=2)
            base = Path(tmpdir) / "test_exp"

            # Create version directories
            for v in range(5):
                version_dir = base / f"v{v}"
                version_dir.mkdir(parents=True)
                (version_dir / "results.json").write_text("{}")

            plugin._prune_old_versions(base)

            # Should keep only last 2 versions (v3, v4) with full data
            # Earlier versions pruned to metrics only
            remaining = sorted([p.name for p in base.glob("v*")])
            assert "v3" in remaining
            assert "v4" in remaining

    def test_prune_large_files_removes_big_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            plugin = ArtifactPlugin(root_dir=tmpdir, big_file_threshold_mb=1)
            version_dir = Path(tmpdir) / "v0"
            version_dir.mkdir(parents=True)

            # Create a file larger than threshold
            big_file = version_dir / "big_model.pkl"
            big_file.write_bytes(b"x" * (2 * 1024 * 1024))  # 2MB

            # Create a small file
            small_file = version_dir / "small.txt"
            small_file.write_text("small")

            # Create protected files
            (version_dir / "results.json").write_text("{}")

            plugin._prune_large_files(version_dir, 1 * 1024 * 1024)

            assert not big_file.exists()
            assert small_file.exists()
            assert (version_dir / "results.json").exists()

    def test_prune_to_metrics_keeps_only_results(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            plugin = ArtifactPlugin(root_dir=tmpdir)
            version_dir = Path(tmpdir) / "v0"
            sub_dir = version_dir / "condition" / "step"
            sub_dir.mkdir(parents=True)

            # Create various files
            (sub_dir / "results.json").write_text("{}")
            (sub_dir / "model.pkl").write_bytes(b"model data")
            (sub_dir / "checkpoint.pt").write_bytes(b"checkpoint")

            plugin._prune_to_metrics(version_dir)

            assert (sub_dir / "results.json").exists()
            assert not (sub_dir / "model.pkl").exists()
            assert not (sub_dir / "checkpoint.pt").exists()

    def test_prune_old_versions_with_no_versions(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            plugin = ArtifactPlugin(root_dir=tmpdir, versioned=True)
            base = Path(tmpdir) / "empty_exp"
            base.mkdir(parents=True)

            # Should not raise
            plugin._prune_old_versions(base)

    def test_prune_old_versions_with_retention_zero(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            plugin = ArtifactPlugin(root_dir=tmpdir, versioned=True, artifact_retention=0)
            base = Path(tmpdir) / "test_exp"

            for v in range(3):
                (base / f"v{v}").mkdir(parents=True)
                (base / f"v{v}" / "results.json").write_text("{}")

            plugin._prune_old_versions(base)

            # retention=0 means keep all
            assert (base / "v0").exists()
            assert (base / "v1").exists()
            assert (base / "v2").exists()


class TestSerialExecutionEdgeCases:
    """Tests for SerialExecution with edge cases."""

    @pytest.mark.asyncio
    async def test_serial_execution_zero_replicates(self):
        plugin = SerialExecution(progress=False)
        exp = _make_experiment([plugin])
        exp.replicates = 0

        results = []

        async def replicate_fn(rep):
            results.append(rep)
            return rep

        output = await plugin.run_experiment_loop(exp, replicate_fn)
        assert output == []
        assert results == []

    @pytest.mark.asyncio
    async def test_serial_execution_single_replicate(self):
        plugin = SerialExecution(progress=False)
        exp = _make_experiment([plugin])
        exp.replicates = 1

        async def replicate_fn(rep):
            return rep * 2

        output = await plugin.run_experiment_loop(exp, replicate_fn)
        assert output == [0]

    @pytest.mark.asyncio
    async def test_serial_execution_with_progress_disabled(self):
        plugin = SerialExecution(progress=False)
        exp = _make_experiment([plugin])
        exp.replicates = 3

        async def replicate_fn(rep):
            return rep

        output = await plugin.run_experiment_loop(exp, replicate_fn)
        assert output == [0, 1, 2]

    @pytest.mark.asyncio
    async def test_serial_execution_with_progress_single_replicate(self):
        # Progress bar not shown for single replicate
        plugin = SerialExecution(progress=True)
        exp = _make_experiment([plugin])
        exp.replicates = 1

        async def replicate_fn(rep):
            return rep

        output = await plugin.run_experiment_loop(exp, replicate_fn)
        assert output == [0]


class TestParallelExecutionEdgeCases:
    """Tests for ParallelExecution edge cases."""

    def test_parallel_execution_invalid_executor_type(self):
        plugin = ParallelExecution(executor_type="invalid")
        exp = _make_experiment([plugin])
        exp.replicates = 1

        def replicate_fn(rep):
            return rep

        with pytest.raises(ValueError, match="executor_type must be one of"):
            plugin.run_experiment_loop(exp, replicate_fn)

    def test_parallel_execution_rejects_async_function(self):
        plugin = ParallelExecution()
        exp = _make_experiment([plugin])
        exp.replicates = 1

        async def async_replicate_fn(rep):
            return rep

        with pytest.raises(TypeError, match="only supports synchronous tasks"):
            plugin.run_experiment_loop(exp, async_replicate_fn)

    def test_parallel_execution_thread_single_replicate(self):
        plugin = ParallelExecution(executor_type="thread", progress=False)
        exp = _make_experiment([plugin])
        exp.replicates = 1

        def replicate_fn(rep):
            return rep * 10

        output = plugin.run_experiment_loop(exp, replicate_fn)
        assert output == [0]

    def test_parallel_execution_thread_multiple_replicates(self):
        plugin = ParallelExecution(executor_type="thread", max_workers=2, progress=False)
        exp = _make_experiment([plugin])
        exp.replicates = 4

        def replicate_fn(rep):
            return rep

        output = plugin.run_experiment_loop(exp, replicate_fn)
        assert sorted(output) == [0, 1, 2, 3]


class TestAsyncExecutionEdgeCases:
    """Tests for AsyncExecution edge cases."""

    @pytest.mark.asyncio
    async def test_async_execution_zero_replicates(self):
        plugin = AsyncExecution(progress=False)
        exp = _make_experiment([plugin])
        exp.replicates = 0

        async def replicate_fn(rep):
            return rep

        output = await plugin.run_experiment_loop(exp, replicate_fn)
        assert output == []

    @pytest.mark.asyncio
    async def test_async_execution_single_replicate(self):
        plugin = AsyncExecution(progress=False)
        exp = _make_experiment([plugin])
        exp.replicates = 1

        async def replicate_fn(rep):
            return rep + 100

        output = await plugin.run_experiment_loop(exp, replicate_fn)
        assert output == [100]

    @pytest.mark.asyncio
    async def test_async_execution_multiple_concurrent(self):
        import asyncio

        plugin = AsyncExecution(progress=False)
        exp = _make_experiment([plugin])
        exp.replicates = 5

        async def replicate_fn(rep):
            await asyncio.sleep(0.01)
            return rep

        output = await plugin.run_experiment_loop(exp, replicate_fn)
        assert output == [0, 1, 2, 3, 4]
