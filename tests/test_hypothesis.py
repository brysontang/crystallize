import pytest

from crystallize.core.exceptions import MissingMetricError
from crystallize.core.hypothesis import Hypothesis
from crystallize.core.stat_test import StatisticalTest


class DummyStatTest(StatisticalTest):
    def __init__(self, significant: bool):
        self.significant = significant

    def run(self, baseline, treatment, *, alpha: float = 0.05):
        return {"p_value": 0.01, "significant": self.significant}


def test_hypothesis_increase_accepted():
    h = Hypothesis(
        metric="metric", direction="increase", statistical_test=DummyStatTest(True)
    )
    result = h.verify({"metric": 1}, {"metric": 2})
    assert result["accepted"] is True


def test_hypothesis_not_significant():
    h = Hypothesis(
        metric="metric", direction="increase", statistical_test=DummyStatTest(False)
    )
    result = h.verify({"metric": 1}, {"metric": 2})
    assert result["accepted"] is False


def test_missing_metric_error():
    h = Hypothesis(
        metric="missing", direction="increase", statistical_test=DummyStatTest(True)
    )
    with pytest.raises(MissingMetricError):
        h.verify({"metric": 1}, {"metric": 2})
