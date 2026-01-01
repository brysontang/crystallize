"""Extended tests for Result, HypothesisResult, and ExperimentMetrics edge cases."""

import pytest
from crystallize.experiments.result import Result
from crystallize.experiments.result_structs import (
    ExperimentMetrics,
    TreatmentMetrics,
    HypothesisResult,
)


class TestResultGetHypothesis:
    """Tests for Result.get_hypothesis() method."""

    def test_get_hypothesis_returns_matching_hypothesis(self):
        hyp = HypothesisResult(
            name="test_hyp",
            results={"t1": {"p_value": 0.05}},
            ranking={"best": "t1"},
        )
        metrics = ExperimentMetrics(
            baseline=TreatmentMetrics({"a": [1]}),
            treatments={},
            hypotheses=[hyp],
        )
        result = Result(metrics=metrics)
        assert result.get_hypothesis("test_hyp") is hyp

    def test_get_hypothesis_returns_none_for_missing(self):
        metrics = ExperimentMetrics(
            baseline=TreatmentMetrics({"a": [1]}),
            treatments={},
            hypotheses=[],
        )
        result = Result(metrics=metrics)
        assert result.get_hypothesis("nonexistent") is None

    def test_get_hypothesis_with_empty_hypotheses_list(self):
        metrics = ExperimentMetrics(
            baseline=TreatmentMetrics({}),
            treatments={},
            hypotheses=[],
        )
        result = Result(metrics=metrics)
        assert result.get_hypothesis("any_name") is None

    def test_get_hypothesis_with_multiple_hypotheses(self):
        hyp1 = HypothesisResult(name="hyp1", results={}, ranking={})
        hyp2 = HypothesisResult(name="hyp2", results={}, ranking={})
        hyp3 = HypothesisResult(name="hyp3", results={}, ranking={})
        metrics = ExperimentMetrics(
            baseline=TreatmentMetrics({}),
            treatments={},
            hypotheses=[hyp1, hyp2, hyp3],
        )
        result = Result(metrics=metrics)
        assert result.get_hypothesis("hyp2") is hyp2
        assert result.get_hypothesis("hyp1") is hyp1
        assert result.get_hypothesis("hyp3") is hyp3

    def test_get_hypothesis_returns_first_match_for_duplicates(self):
        hyp1 = HypothesisResult(name="dup", results={"first": {}}, ranking={})
        hyp2 = HypothesisResult(name="dup", results={"second": {}}, ranking={})
        metrics = ExperimentMetrics(
            baseline=TreatmentMetrics({}),
            treatments={},
            hypotheses=[hyp1, hyp2],
        )
        result = Result(metrics=metrics)
        found = result.get_hypothesis("dup")
        assert found is hyp1
        assert "first" in found.results


class TestResultPrintTreeFormatValidation:
    """Tests for Result.print_tree() format validation."""

    def _make_result_with_provenance(self):
        metrics = ExperimentMetrics(
            baseline=TreatmentMetrics({}),
            treatments={},
            hypotheses=[],
        )
        provenance = {
            "ctx_changes": {
                "baseline": {
                    0: [
                        {
                            "step": "TestStep",
                            "ctx_changes": {"reads": {"x": 1}, "wrote": {}, "metrics": {}},
                        }
                    ]
                }
            }
        }
        return Result(metrics=metrics, provenance=provenance)

    def test_print_tree_raises_on_unknown_token(self):
        result = self._make_result_with_provenance()
        with pytest.raises(ValueError, match="Invalid format spec"):
            result.print_tree("treatment > unknown > step")

    def test_print_tree_raises_when_action_not_final(self):
        result = self._make_result_with_provenance()
        with pytest.raises(ValueError, match="'action' must be the final element"):
            result.print_tree("action > treatment > step")

    def test_print_tree_raises_when_action_in_middle(self):
        result = self._make_result_with_provenance()
        with pytest.raises(ValueError, match="'action' must be the final element"):
            result.print_tree("treatment > action > step")

    def test_print_tree_with_action_as_final_element(self, capsys):
        result = self._make_result_with_provenance()
        # Format must include treatment, replicate, step for color assignment
        result.print_tree("treatment > replicate > step > action")
        output = capsys.readouterr().out
        assert "TestStep" in output

    def test_print_tree_with_empty_format_raises(self):
        result = self._make_result_with_provenance()
        # Empty string after split becomes ['']
        with pytest.raises(ValueError, match="Invalid format spec"):
            result.print_tree("")

    def test_print_tree_with_only_action_requires_all_tokens(self):
        # The current implementation requires treatment, replicate, step
        # to be in the format for get_color to work. Test that limitation.
        result = self._make_result_with_provenance()
        # This would fail due to get_color trying to find missing tokens
        with pytest.raises(ValueError):
            result.print_tree("action")

    def test_print_tree_different_format_orders(self, capsys):
        result = self._make_result_with_provenance()
        # replicate > treatment > step
        result.print_tree("replicate > treatment > step")
        output = capsys.readouterr().out
        assert "Replicate" in output
        assert "Treatment" in output

    def test_print_tree_with_no_ctx_changes(self, capsys):
        metrics = ExperimentMetrics(
            baseline=TreatmentMetrics({}),
            treatments={},
            hypotheses=[],
        )
        result = Result(metrics=metrics, provenance={})
        result.print_tree()
        output = capsys.readouterr().out
        assert "Experiment Summary" in output

    def test_print_tree_with_empty_ctx_changes(self, capsys):
        metrics = ExperimentMetrics(
            baseline=TreatmentMetrics({}),
            treatments={},
            hypotheses=[],
        )
        result = Result(metrics=metrics, provenance={"ctx_changes": {}})
        result.print_tree()
        output = capsys.readouterr().out
        assert "Experiment Summary" in output

    def test_print_tree_with_writes_and_metrics(self, capsys):
        metrics = ExperimentMetrics(
            baseline=TreatmentMetrics({}),
            treatments={},
            hypotheses=[],
        )
        provenance = {
            "ctx_changes": {
                "treatment_a": {
                    0: [
                        {
                            "step": "WriteStep",
                            "ctx_changes": {
                                "reads": {},
                                "wrote": {"key": {"before": None, "after": "value"}},
                                "metrics": {"metric1": {"before": 0, "after": 1}},
                            },
                        }
                    ]
                }
            }
        }
        result = Result(metrics=metrics, provenance=provenance)
        result.print_tree()
        output = capsys.readouterr().out
        assert "WriteStep" in output


class TestHypothesisResultGetForTreatment:
    """Tests for HypothesisResult.get_for_treatment() method."""

    def test_get_for_treatment_returns_correct_result(self):
        hyp = HypothesisResult(
            name="test",
            results={"t1": {"p_value": 0.05}, "t2": {"p_value": 0.01}},
            ranking={"best": "t2"},
        )
        assert hyp.get_for_treatment("t1") == {"p_value": 0.05}
        assert hyp.get_for_treatment("t2") == {"p_value": 0.01}

    def test_get_for_treatment_returns_none_for_missing(self):
        hyp = HypothesisResult(
            name="test",
            results={"t1": {"p_value": 0.05}},
            ranking={},
        )
        assert hyp.get_for_treatment("nonexistent") is None

    def test_get_for_treatment_with_empty_results(self):
        hyp = HypothesisResult(name="test", results={}, ranking={})
        assert hyp.get_for_treatment("any") is None

    def test_get_for_treatment_with_none_treatment_name(self):
        hyp = HypothesisResult(
            name="test",
            results={"t1": {"value": 1}},
            ranking={},
        )
        # None as key lookup
        assert hyp.get_for_treatment(None) is None


class TestExperimentMetricsToDataFrame:
    """Tests for ExperimentMetrics.to_df() edge cases."""

    def test_to_df_with_empty_hypotheses(self):
        pytest.importorskip("pandas")
        metrics = ExperimentMetrics(
            baseline=TreatmentMetrics({"a": [1, 2]}),
            treatments={"t1": TreatmentMetrics({"a": [3, 4]})},
            hypotheses=[],
        )
        df = metrics.to_df()
        assert len(df) == 0

    def test_to_df_with_multiple_hypotheses_and_treatments(self):
        pytest.importorskip("pandas")
        hyp1 = HypothesisResult(
            name="hyp1",
            results={"t1": {"p": 0.05}, "t2": {"p": 0.01}},
            ranking={},
        )
        hyp2 = HypothesisResult(
            name="hyp2",
            results={"t1": {"score": 10}},
            ranking={},
        )
        metrics = ExperimentMetrics(
            baseline=TreatmentMetrics({}),
            treatments={},
            hypotheses=[hyp1, hyp2],
        )
        df = metrics.to_df()
        assert len(df) == 3  # 2 from hyp1, 1 from hyp2
        assert set(df["hypothesis"].unique()) == {"hyp1", "hyp2"}

    def test_to_df_with_hypothesis_missing_some_treatments(self):
        pytest.importorskip("pandas")
        hyp = HypothesisResult(
            name="partial",
            results={"t1": {"val": 1}},  # Only t1, not t2
            ranking={},
        )
        metrics = ExperimentMetrics(
            baseline=TreatmentMetrics({}),
            treatments={"t1": TreatmentMetrics({}), "t2": TreatmentMetrics({})},
            hypotheses=[hyp],
        )
        df = metrics.to_df()
        assert len(df) == 1
        assert df.iloc[0]["condition"] == "t1"
