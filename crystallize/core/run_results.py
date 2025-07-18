from dataclasses import dataclass
from typing import Any, Mapping, Optional, Dict, List


@dataclass
class ReplicateResult:
    """Holds the complete results from a single replicate execution."""

    baseline_metrics: Optional[Mapping[str, Any]]
    baseline_seed: Optional[int]
    treatment_metrics: Dict[str, Mapping[str, Any]]
    treatment_seeds: Dict[str, int]
    errors: Dict[str, Exception]
    provenance: Dict[str, List[Mapping[str, Any]]]
