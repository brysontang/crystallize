from typing import Mapping, Any
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
        test_result = self.statistical_test.run(
            baseline_metrics[self.metric],
            treatment_metrics[self.metric],
            alpha=self.alpha,
        )

        accepted = False
        if test_result["significant"]:
            if self.direction == "decrease":
                accepted = (
                    treatment_metrics[self.metric] < baseline_metrics[self.metric]
                )
            elif self.direction == "increase":
                accepted = (
                    treatment_metrics[self.metric] > baseline_metrics[self.metric]
                )
            else:  # "equal"
                accepted = True

        return {**test_result, "accepted": accepted}
