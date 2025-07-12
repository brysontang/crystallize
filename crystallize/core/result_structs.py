from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

try:
    import pandas as pd
except Exception:  # pragma: no cover - pandas is optional
    pd = None  # type: ignore


@dataclass
class TreatmentMetrics:
    metrics: Dict[str, List[Any]]


@dataclass
class HypothesisResult:
    name: str
    results: Dict[str, Dict[str, Any]]
    ranking: Dict[str, Any]

    def get_for_treatment(self, treatment: str) -> Optional[Dict[str, Any]]:
        return self.results.get(treatment)


@dataclass
class ExperimentMetrics:
    baseline: TreatmentMetrics
    treatments: Dict[str, TreatmentMetrics]
    hypotheses: List[HypothesisResult]

    def to_df(self):
        if pd is None:  # pragma: no cover - optional dependency
            raise ImportError("pandas is required for to_df()")
        rows = []
        for hyp in self.hypotheses:
            for treat, res in hyp.results.items():
                rows.append({"condition": treat, "hypothesis": hyp.name, **res})
        return pd.DataFrame(rows)
