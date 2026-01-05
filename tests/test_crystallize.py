"""Tests for exp.crystallize() and ConfirmRun."""

import tempfile
import pytest

from crystallize import explore, ConfirmRun


class TestCrystallize:
    """Tests for basic crystallize() functionality."""

    def test_simple_crystallize(self):
        """crystallize() returns a ConfirmRun with hypothesis results."""

        def fn(config, ctx):
            ctx.record("score", config["x"])
            return {"x": config["x"]}

        with tempfile.TemporaryDirectory() as tmpdir:
            exp = explore(
                fn=fn,
                configs={"low": {"x": 1}, "high": {"x": 10}},
                replicates=3,
                progress=False,
                store_root=tmpdir,
            )

            result = exp.crystallize(
                hypothesis="high.score > low.score",
                replicates=5,
                progress=False,
            )

            assert isinstance(result, ConfirmRun)
            assert result.run_id.startswith("conf_")
            assert result.parent_run_id == exp.run_id
            assert result.lineage_id == exp.lineage_id
            assert result.hypothesis == "high.score > low.score"
            assert result.supported is True
            assert result.hypothesis_result is not None
            assert result.hypothesis_result.p_value < 0.05

    def test_crystallize_not_supported(self):
        """crystallize() correctly identifies unsupported hypothesis."""

        def fn(config, ctx):
            ctx.record("score", config["x"])

        with tempfile.TemporaryDirectory() as tmpdir:
            exp = explore(
                fn=fn,
                configs={"a": {"x": 5}, "b": {"x": 5}},
                replicates=3,
                progress=False,
                store_root=tmpdir,
            )

            result = exp.crystallize(
                hypothesis="a.score > b.score",
                replicates=10,
                progress=False,
            )

            # With equal scores, hypothesis should not be supported
            assert result.supported is False

    def test_crystallize_writes_prereg(self):
        """crystallize() writes pre-registration artifact."""

        def fn(config, ctx):
            ctx.record("score", config["x"])

        with tempfile.TemporaryDirectory() as tmpdir:
            exp = explore(
                fn=fn,
                configs={"a": {"x": 1}, "b": {"x": 2}},
                replicates=2,
                progress=False,
                store_root=tmpdir,
            )

            result = exp.crystallize(
                hypothesis="b.score > a.score",
                replicates=5,
                progress=False,
            )

            import os

            assert result.prereg_path is not None
            assert os.path.exists(result.prereg_path)

    def test_crystallize_with_seed(self):
        """Seeded crystallize() produces reproducible results."""
        import random

        def fn(config, ctx):
            ctx.record("score", config["x"] + random.random() * 0.001)

        with tempfile.TemporaryDirectory() as tmpdir:
            exp = explore(
                fn=fn,
                configs={"a": {"x": 1}, "b": {"x": 10}},
                replicates=2,
                seed=42,
                progress=False,
                store_root=tmpdir,
            )

            result1 = exp.crystallize(
                hypothesis="b.score > a.score",
                replicates=5,
                seed=123,
                progress=False,
            )

            # Run again with same seed - need new experiment
            exp2 = explore(
                fn=fn,
                configs={"a": {"x": 1}, "b": {"x": 10}},
                replicates=2,
                seed=42,
                progress=False,
                store_root=tmpdir,
            )

            result2 = exp2.crystallize(
                hypothesis="b.score > a.score",
                replicates=5,
                seed=123,
                progress=False,
            )

            # p-values should be the same with same seed
            assert abs(result1.hypothesis_result.p_value - result2.hypothesis_result.p_value) < 0.01


class TestCrystallizeValidation:
    """Tests for crystallize() validation."""

    def test_invalid_hypothesis_format(self):
        """crystallize() raises on invalid hypothesis format."""

        def fn(config, ctx):
            ctx.record("x", 1)

        with tempfile.TemporaryDirectory() as tmpdir:
            exp = explore(
                fn=fn,
                configs={"test": {}},
                replicates=1,
                progress=False,
                store_root=tmpdir,
            )

            with pytest.raises(ValueError, match="Invalid hypothesis"):
                exp.crystallize(hypothesis="invalid format", replicates=5)

    def test_hypothesis_references_missing_config(self):
        """crystallize() raises when hypothesis references missing config."""

        def fn(config, ctx):
            ctx.record("x", 1)

        with tempfile.TemporaryDirectory() as tmpdir:
            exp = explore(
                fn=fn,
                configs={"a": {}},
                replicates=1,
                progress=False,
                store_root=tmpdir,
            )

            with pytest.raises(ValueError, match="references 'b'"):
                exp.crystallize(hypothesis="a.x > b.x", replicates=5)


class TestConfirmRunReport:
    """Tests for ConfirmRun.report()."""

    def test_report_contains_integrity(self):
        """report() includes integrity status."""

        def fn(config, ctx):
            ctx.record("score", config["x"])

        with tempfile.TemporaryDirectory() as tmpdir:
            exp = explore(
                fn=fn,
                configs={"a": {"x": 1}, "b": {"x": 2}},
                replicates=2,
                progress=False,
                store_root=tmpdir,
            )

            result = exp.crystallize(
                hypothesis="b.score > a.score",
                replicates=5,
                progress=False,
            )

            report = result.report()
            assert "Integrity:" in report
            assert result.run_id in report

    def test_report_contains_proof_block(self):
        """report() includes proof block."""

        def fn(config, ctx):
            ctx.record("score", config["x"])

        with tempfile.TemporaryDirectory() as tmpdir:
            exp = explore(
                fn=fn,
                configs={"a": {"x": 1}, "b": {"x": 2}},
                replicates=2,
                progress=False,
                store_root=tmpdir,
            )

            result = exp.crystallize(
                hypothesis="b.score > a.score",
                replicates=5,
                progress=False,
            )

            report = result.report()
            assert "Proof:" in report
            assert "run_id:" in report
            assert "parent:" in report
            assert "lineage:" in report


class TestConfirmRunSerialization:
    """Tests for ConfirmRun serialization."""

    def test_to_dict(self):
        """ConfirmRun.to_dict() returns serializable dict."""

        def fn(config, ctx):
            ctx.record("score", config["x"])

        with tempfile.TemporaryDirectory() as tmpdir:
            exp = explore(
                fn=fn,
                configs={"a": {"x": 1}, "b": {"x": 2}},
                replicates=2,
                progress=False,
                store_root=tmpdir,
            )

            result = exp.crystallize(
                hypothesis="b.score > a.score",
                replicates=5,
                progress=False,
            )

            d = result.to_dict()
            assert "run_id" in d
            assert "hypothesis" in d
            assert "supported" in d
            assert "integrity" in d
            assert "hypothesis_result" in d
