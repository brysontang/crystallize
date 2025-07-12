import pytest

from crystallize.core.exceptions import MissingMetricError
from crystallize.core.hypothesis import Hypothesis
from crystallize.core import from_scipy


def make_verifier(accepted: bool):
    def verifier(baseline, treatment):
        return {"accepted": accepted}

    return verifier


def test_verify_returns_result():
    hyp = Hypothesis(verifier=make_verifier(True), metrics="metric", ranker=lambda r: 0.0)
    result = hyp.verify({"metric": [1, 2]}, {"metric": [3, 4]})
    assert result["accepted"] is True


def test_missing_metric_error():
    hyp = Hypothesis(verifier=make_verifier(True), metrics="metric", ranker=lambda r: 0.0)
    with pytest.raises(MissingMetricError):
        hyp.verify({"other": [1]}, {"metric": [2]})


def test_name_defaults_to_metric():
    hyp = Hypothesis(verifier=make_verifier(True), metrics="metric", ranker=lambda r: 0.0)
    assert hyp.name == "<lambda>"


def test_custom_name():
    hyp = Hypothesis(verifier=make_verifier(True), metrics="metric", ranker=lambda r: 0.0, name="custom")
    assert hyp.name == "custom"


def test_multi_metric():
    def verifier(baseline, treatment):
        return {
            "sum_baseline": sum(baseline["a"]) + sum(baseline["b"]),
            "sum_treatment": sum(treatment["a"]) + sum(treatment["b"]),
        }

    hyp = Hypothesis(verifier=verifier, metrics=["a", "b"], ranker=lambda r: 0.0)
    res = hyp.verify({"a": [1], "b": [2]}, {"a": [3], "b": [4]})
    assert res["sum_baseline"] == 3 and res["sum_treatment"] == 7


def test_grouped_metrics_return_list():
    def verifier(baseline, treatment):
        key = next(iter(baseline))
        return {"diff": sum(treatment[key]) - sum(baseline[key])}

    hyp = Hypothesis(verifier=verifier, metrics=[["x"], ["y"]], ranker=lambda r: r.get("diff", 0))
    out = hyp.verify({"x": [1], "y": [10]}, {"x": [2], "y": [20]})
    assert isinstance(out, list) and len(out) == 2


def test_rank_treatments_with_custom_ranker():
    hyp = Hypothesis(verifier=make_verifier(True), metrics="m", ranker=lambda r: r["score"])
    results = {"t1": {"score": 3}, "t2": {"score": 1}}
    ranking = hyp.rank_treatments(results)
    assert ranking["best"] == "t2"


def test_from_scipy_wrapper_produces_valid_result():
    from scipy import stats
    verifier = from_scipy(stats.ttest_ind)
    hyp = Hypothesis(verifier=verifier, metrics="a", ranker=lambda r: r["p_value"])
    res = hyp.verify({"a": [1, 1]}, {"a": [2, 2]})
    assert 0 <= res["p_value"] <= 1
    assert res["significant"] is (res["p_value"] < 0.05)

