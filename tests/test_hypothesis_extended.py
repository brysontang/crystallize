"""Extended tests for Hypothesis class and rank_by_p_value function."""

from crystallize.experiments.hypothesis import Hypothesis, rank_by_p_value


class TestRankByPValue:
    """Tests for the rank_by_p_value function."""

    def test_rank_by_p_value_returns_p_value(self):
        result = {"p_value": 0.05, "other": "data"}
        assert rank_by_p_value(result) == 0.05

    def test_rank_by_p_value_returns_1_for_missing(self):
        result = {"other_key": 0.05}
        assert rank_by_p_value(result) == 1.0

    def test_rank_by_p_value_with_zero(self):
        result = {"p_value": 0.0}
        assert rank_by_p_value(result) == 0.0

    def test_rank_by_p_value_with_empty_dict(self):
        result = {}
        assert rank_by_p_value(result) == 1.0

    def test_rank_by_p_value_with_very_small_value(self):
        result = {"p_value": 1e-10}
        assert rank_by_p_value(result) == 1e-10


class TestHypothesisVerifyAutoDetect:
    """Tests for Hypothesis.verify() with metrics_spec=None (auto-detect)."""

    def test_verify_auto_detect_single_metric(self):
        def verifier(baseline, treatment):
            return {"sum": sum(treatment["m1"]) - sum(baseline["m1"])}

        hyp = Hypothesis(verifier=verifier, metrics=None)
        result = hyp.verify({"m1": [1, 2, 3]}, {"m1": [4, 5, 6]})
        assert result["sum"] == 9  # (4+5+6) - (1+2+3)

    def test_verify_auto_detect_multiple_metrics(self):
        def verifier(baseline, treatment):
            keys = list(baseline.keys())
            return {"keys": sorted(keys)}

        hyp = Hypothesis(verifier=verifier, metrics=None)
        result = hyp.verify(
            {"a": [1], "b": [2], "c": [3]}, {"a": [4], "b": [5], "c": [6]}
        )
        assert result["keys"] == ["a", "b", "c"]

    def test_verify_auto_detect_uses_baseline_keys(self):
        def verifier(baseline, treatment):
            return {"baseline_keys": list(baseline.keys())}

        hyp = Hypothesis(verifier=verifier, metrics=None)
        # Treatment has extra keys not in baseline
        result = hyp.verify({"x": [1]}, {"x": [2], "y": [3]})
        assert result["baseline_keys"] == ["x"]


class TestHypothesisNameResolution:
    """Tests for Hypothesis name resolution from ranker function."""

    def test_name_from_ranker_function(self):
        def custom_ranker(result):
            return result.get("score", 0)

        hyp = Hypothesis(
            verifier=lambda b, t: {}, metrics="m", ranker=custom_ranker
        )
        assert hyp.name == "custom_ranker"

    def test_name_from_explicit_parameter(self):
        hyp = Hypothesis(
            verifier=lambda b, t: {},
            metrics="m",
            ranker=lambda r: 0,
            name="explicit_name",
        )
        assert hyp.name == "explicit_name"

    def test_name_defaults_to_hypothesis(self):
        # When no name and ranker has no __name__ attribute
        class RankerClass:
            def __call__(self, result):
                return 0

        hyp = Hypothesis(verifier=lambda b, t: {}, metrics="m", ranker=RankerClass())
        assert hyp.name == "hypothesis"

    def test_default_ranker_is_rank_by_p_value(self):
        hyp = Hypothesis(verifier=lambda b, t: {"p_value": 0.05}, metrics="m")
        # Default ranker should be rank_by_p_value
        assert hyp.ranker is rank_by_p_value


class TestHypothesisRankTreatments:
    """Tests for Hypothesis.rank_treatments() method."""

    def test_rank_treatments_sorts_by_score(self):
        hyp = Hypothesis(
            verifier=lambda b, t: {},
            metrics="m",
            ranker=lambda r: r["score"],
        )
        results = {"t1": {"score": 5}, "t2": {"score": 1}, "t3": {"score": 3}}
        ranking = hyp.rank_treatments(results)
        assert ranking["best"] == "t2"
        assert ranking["ranked"] == [("t2", 1), ("t3", 3), ("t1", 5)]

    def test_rank_treatments_with_empty_results(self):
        hyp = Hypothesis(
            verifier=lambda b, t: {},
            metrics="m",
            ranker=lambda r: r.get("score", 0),
        )
        ranking = hyp.rank_treatments({})
        assert ranking["best"] is None
        assert ranking["ranked"] == []

    def test_rank_treatments_single_treatment(self):
        hyp = Hypothesis(
            verifier=lambda b, t: {},
            metrics="m",
            ranker=lambda r: r["val"],
        )
        ranking = hyp.rank_treatments({"only": {"val": 42}})
        assert ranking["best"] == "only"
        assert ranking["ranked"] == [("only", 42)]


class TestHypothesisVerifyGroupedMetrics:
    """Tests for Hypothesis.verify() with grouped metrics specifications."""

    def test_verify_with_single_string_metric(self):
        def verifier(baseline, treatment):
            return {"diff": treatment["x"][0] - baseline["x"][0]}

        hyp = Hypothesis(verifier=verifier, metrics="x")
        result = hyp.verify({"x": [1]}, {"x": [5]})
        assert result["diff"] == 4

    def test_verify_with_list_of_strings(self):
        def verifier(baseline, treatment):
            return {"count": len(baseline) + len(treatment)}

        hyp = Hypothesis(verifier=verifier, metrics=["a", "b"])
        result = hyp.verify({"a": [1], "b": [2]}, {"a": [3], "b": [4]})
        assert result["count"] == 4  # 2 keys from each

    def test_verify_with_nested_groups_returns_list(self):
        def verifier(baseline, treatment):
            key = list(baseline.keys())[0]
            return {"key": key}

        hyp = Hypothesis(verifier=verifier, metrics=[["x"], ["y"]])
        result = hyp.verify({"x": [1], "y": [2]}, {"x": [3], "y": [4]})
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["key"] == "x"
        assert result[1]["key"] == "y"

    def test_verify_with_three_groups(self):
        def verifier(baseline, treatment):
            return {"sum": sum(list(baseline.values())[0])}

        hyp = Hypothesis(verifier=verifier, metrics=[["a"], ["b"], ["c"]])
        result = hyp.verify(
            {"a": [1, 2], "b": [3, 4], "c": [5, 6]},
            {"a": [1], "b": [1], "c": [1]},
        )
        assert isinstance(result, list)
        assert len(result) == 3
