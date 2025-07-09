from typing import Any, Mapping

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
        direction: str,
        statistical_test: StatisticalTest,
        alpha: float = 0.05,
    ):
        assert direction in {"increase", "decrease", "equal"}
        self.metric = metric
        self.direction = direction
        self.statistical_test = statistical_test
        self.alpha = alpha

    # ---- public API -----------------------------------------------------

    def verify(
        self,
        baseline_metrics: Mapping[str, Any],
        treatment_metrics: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        """
        Verify hypothesis using the provided metrics.

        Args:
            baseline_metrics: Dict of aggregated baseline metrics.
            treatment_metrics: Dict of aggregated treatment metrics.

        Returns:
            Dict with the statistical test result plus an `accepted` boolean.
        """
        try:
            baseline_sample = baseline_metrics[self.metric]
            treatment_sample = treatment_metrics[self.metric]
        except KeyError:
            raise MissingMetricError(self.metric)

        test_result = self.statistical_test.run(
            baseline_sample,
            treatment_sample,
            alpha=self.alpha,
        )

        accepted = False
        if test_result["significant"]:
            if self.direction == "decrease":
                accepted = treatment_sample < baseline_sample
            elif self.direction == "increase":
                accepted = treatment_sample > baseline_sample
            else:  # "equal"
                accepted = True

        return {**test_result, "accepted": accepted}
