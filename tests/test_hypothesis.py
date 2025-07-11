import pytest

from crystallize.core.exceptions import MissingMetricError
from crystallize.core.hypothesis import Hypothesis


def make_verifier(accepted: bool):
    def verifier(baseline, treatment):
        return {"accepted": accepted}

    return verifier


def test_verify_returns_result():
    hyp = Hypothesis(metric="metric", verifier=make_verifier(True))
    result = hyp.verify({"metric": [1, 2]}, {"metric": [3, 4]})
    assert result["accepted"] is True


def test_missing_metric_error():
    hyp = Hypothesis(metric="metric", verifier=make_verifier(True))
    with pytest.raises(MissingMetricError):
        hyp.verify({"other": [1]}, {"metric": [2]})


def test_name_defaults_to_metric():
    hyp = Hypothesis(metric="metric", verifier=make_verifier(True))
    assert hyp.name == "metric"


def test_custom_name():
    hyp = Hypothesis(metric="metric", verifier=make_verifier(True), name="custom")
    assert hyp.name == "custom"


def test_multi_metric():
    def verifier(baseline, treatment):
        return {
            "sum_baseline": sum(baseline["a"]) + sum(baseline["b"]),
            "sum_treatment": sum(treatment["a"]) + sum(treatment["b"]),
        }

    hyp = Hypothesis(metric=["a", "b"], verifier=verifier)
    res = hyp.verify({"a": [1], "b": [2]}, {"a": [3], "b": [4]})
    assert res["sum_baseline"] == 3 and res["sum_treatment"] == 7

