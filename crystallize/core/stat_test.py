from abc import ABC, abstractmethod
from typing import Mapping, Any


class StatisticalTest(ABC):
    """
    Encapsulates a statistical comparison between two (or more) metric samples.

    Sub-classes perform the actual math and return a dictionary that must include:
        - "p_value": float
        - "significant": bool
        - additional test-specific fields (e.g., effect_size).
    """

    @abstractmethod
    def run(
        self,
        baseline: Mapping[str, Any],
        treatment: Mapping[str, Any],
        *,
        alpha: float = 0.05,
    ) -> Mapping[str, Any]:
        """
        Execute the statistical test.

        Args:
            baseline: Metric sample(s) for the control condition.
            treatment: Metric sample(s) for the treatment condition.
            alpha: Significance level.

        Returns:
            Dict containing at minimum {"p_value": float, "significant": bool}.
        """
        raise NotImplementedError()
