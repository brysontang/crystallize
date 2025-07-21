from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, DefaultDict, Mapping

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


@dataclass
class AggregateData:
    """Grouped results collected from all replicates."""

    baseline_metrics: Dict[str, List[Any]]
    treatment_metrics_dict: Dict[str, Dict[str, List[Any]]]
    baseline_seeds: List[int]
    treatment_seeds_agg: Dict[str, List[int]]
    provenance_runs: "DefaultDict[str, Dict[int, List[Mapping[str, Any]]]]"
    errors: Dict[str, Exception]
