from typing import Any, Callable, Mapping, Sequence, Optional, Dict, List

from crystallize.core.exceptions import MissingMetricError


class Hypothesis:
    """A quantifiable assertion to verify after experiment execution."""

    def __init__(
        self,
        metric: str | Sequence[str],
        verifier: Callable[[Mapping[str, Sequence[Any]], Mapping[str, Sequence[Any]]], Mapping[str, Any]],
        name: Optional[str] = None,
    ) -> None:
        self.metric_list: List[str] = [metric] if isinstance(metric, str) else list(metric)
        self.name = name or (metric if isinstance(metric, str) else "_".join(self.metric_list))
        self.verifier = verifier

    # ---- public API -----------------------------------------------------

    def verify(
        self,
        baseline_metrics: Mapping[str, Sequence[Any]],
        treatment_metrics: Mapping[str, Sequence[Any]],
    ) -> Mapping[str, Any]:
        baseline_samples: Dict[str, Sequence[Any]] = {}
        treatment_samples: Dict[str, Sequence[Any]] = {}

        for m in self.metric_list:
            try:
                baseline_samples[m] = baseline_metrics[m]
                treatment_samples[m] = treatment_metrics[m]
            except KeyError:
                raise MissingMetricError(m)

        return self.verifier(baseline_samples, treatment_samples)
