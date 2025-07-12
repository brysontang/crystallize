from __future__ import annotations

from typing import Any, Dict, Optional

from .result_structs import ExperimentMetrics, HypothesisResult


class Result:
    def __init__(
        self,
        metrics: ExperimentMetrics,
        artifacts: Optional[Dict[str, Any]] = None,
        errors: Optional[Dict[str, Exception]] = None,
        provenance: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.metrics = metrics
        self.artifacts = artifacts or {}
        self.errors = errors or {}
        self.provenance = provenance or {}

    def get_artifact(self, name: str) -> Any:
        return self.artifacts.get(name)

    # Convenience
    def get_hypothesis(self, name: str) -> Optional[HypothesisResult]:
        return next(
            (h for h in self.metrics.hypotheses if h.name == name),
            None,
        )
