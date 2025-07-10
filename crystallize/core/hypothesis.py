from typing import Any, Mapping, Optional, Sequence

from crystallize.core.exceptions import MissingMetricError
from crystallize.core.stat_test import StatisticalTest


class Hypothesis:
    """
    A quantifiable assertion to verify after experiment execution.

    Example:
        Hypothesis(
            metric="validation_loss",
            direction="decrease",
            statistical_test=WelchTTest()
        )
    """

    def __init__(
        self,
        metric: str,
        statistical_test: StatisticalTest,
        alpha: float = 0.05,
        direction: Optional[str] = None,
        name: Optional[str] = None,
    ):
        assert direction in {"increase", "decrease", "equal", None}
        self.metric = metric
        self.name = name or metric
        self.direction = direction
        self.statistical_test = statistical_test
        self.alpha = alpha

    # ---- public API -----------------------------------------------------

    def verify(
        self,
        baseline_metrics: Mapping[str, Sequence[float]],
        treatment_metrics: Mapping[str, Sequence[float]],
    ) -> Mapping[str, Any]:
        try:
            baseline_samples = baseline_metrics[self.metric]
            treatment_samples = treatment_metrics[self.metric]
        except KeyError:
            raise MissingMetricError(self.metric)

        test_result = self.statistical_test.run(
            baseline_samples,
            treatment_samples,
            alpha=self.alpha,
        )

        result = {**test_result, "accepted": test_result["significant"]}

        if self.direction and test_result["significant"]:
            baseline_mean = sum(baseline_samples) / len(baseline_samples)
            treatment_mean = sum(treatment_samples) / len(treatment_samples)

            if self.direction == "increase":
                result["accepted"] = treatment_mean > baseline_mean
            elif self.direction == "decrease":
                result["accepted"] = treatment_mean < baseline_mean
            elif self.direction == "equal":
                result["accepted"] = abs(treatment_mean - baseline_mean) < 1e-6

            result.update(
                {
                    "baseline_mean": baseline_mean,
                    "treatment_mean": treatment_mean,
                }
            )

        return result
