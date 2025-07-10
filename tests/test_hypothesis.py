import pytest

from crystallize.core.exceptions import MissingMetricError
from crystallize.core.hypothesis import Hypothesis
from crystallize.core.stat_test import StatisticalTest


class DummyStatTest(StatisticalTest):
    def __init__(self, significant: bool):
        self.significant = significant

    def run(self, baseline, treatment, *, alpha: float = 0.05):
        return {"p_value": 0.01, "significant": self.significant}


# Now baseline/treatment metrics are lists (multiple samples):


def test_hypothesis_increase_accepted():
    h = Hypothesis(
        metric="metric",
        direction="increase",
        statistical_test=DummyStatTest(True),
    )
    result = h.verify({"metric": [1, 1.2, 0.9]}, {"metric": [2, 2.1, 2.2]})
    assert result["accepted"] is True


def test_hypothesis_decrease_accepted():
    h = Hypothesis(
        metric="metric",
        direction="decrease",
        statistical_test=DummyStatTest(True),
    )
    result = h.verify({"metric": [2, 2.1, 2.2]}, {"metric": [1, 1.2, 0.9]})
    assert result["accepted"] is True


def test_hypothesis_increase_not_accepted_due_to_direction():
    h = Hypothesis(
        metric="metric",
        direction="increase",
        statistical_test=DummyStatTest(True),
    )
    result = h.verify({"metric": [2, 2.1, 2.2]}, {"metric": [1, 1.1, 1.2]})
    assert result["accepted"] is False


def test_hypothesis_not_significant():
    h = Hypothesis(
        metric="metric",
        direction="increase",
        statistical_test=DummyStatTest(False),
    )
    result = h.verify({"metric": [1, 1.1, 1.2]}, {"metric": [2, 2.1, 2.2]})
    assert result["accepted"] is False


def test_missing_metric_error():
    h = Hypothesis(
        metric="missing",
        direction="increase",
        statistical_test=DummyStatTest(True),
    )
    with pytest.raises(MissingMetricError):
        h.verify({"metric": [1, 1.1, 1.2]}, {"metric": [2, 2.1, 2.2]})


# New test for no-direction hypothesis
def test_hypothesis_no_direction():
    h = Hypothesis(
        metric="metric",
        statistical_test=DummyStatTest(True),
        direction=None,
    )
    result = h.verify({"metric": [1, 1.2, 1.1]}, {"metric": [3, 3.2, 3.1]})
    assert result["accepted"] is True
    assert "baseline_mean" not in result
    assert "treatment_mean" not in result


def test_hypothesis_name_defaults_to_metric():
    h = Hypothesis(metric="metric", statistical_test=DummyStatTest(True))
    assert h.name == "metric"


def test_hypothesis_custom_name():
    h = Hypothesis(metric="metric", statistical_test=DummyStatTest(True), name="custom")
    assert h.name == "custom"


def test_verify_empty_samples():
    h = Hypothesis(
        metric="metric",
        direction="increase",
        statistical_test=DummyStatTest(True),
    )
    with pytest.raises(ZeroDivisionError):
        h.verify({"metric": []}, {"metric": []})
