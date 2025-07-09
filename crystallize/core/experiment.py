from __future__ import annotations

from typing import List, Dict, Any, Optional, Mapping
import statistics as _stats
from copy import deepcopy

from crystallize.core.datasource import DataSource
from crystallize.core.pipeline import Pipeline
from crystallize.core.treatment import Treatment
from crystallize.core.hypothesis import Hypothesis
from crystallize.core.result import Result
from crystallize.core.context import FrozenContext


def _aggregate(samples: List[Mapping[str, Any]]) -> Mapping[str, Any]:
    """
    Aggregate replicate metric dicts by computing their mean.

    Args:
        samples: List of metric dictionaries from each replicate.

    Returns:
        Dict[str, float]: mean value per metric key.
    """
    if not samples:
        return {}

    keys = samples[0].keys()
    agg: Dict[str, float] = {}
    for k in keys:
        agg[k] = _stats.mean(sample[k] for sample in samples)
    return agg


class Experiment:
    """
    Orchestrates baseline + treatment pipelines across replicates, then
    verifies the hypothesis using aggregated metrics.
    """

    def __init__(
        self,
        datasource: DataSource,
        pipeline: Pipeline,
        treatments: List[Treatment],
        hypothesis: Hypothesis,
        replicates: int = 1,
    ):
        self.datasource = datasource
        self.pipeline = pipeline
        self.treatments = treatments
        self.hypothesis = hypothesis
        self.replicates = max(1, replicates)

    # ------------------------------------------------------------------ #

    def _run_condition(
        self, ctx: FrozenContext, treatment: Optional[Treatment] = None
    ) -> Mapping[str, Any]:
        """
        Execute one pipeline run for either the baseline (treatment is None)
        or a specific treatment.
        """
        # Clone ctx to avoid cross‐run contamination
        run_ctx = deepcopy(ctx)

        # Apply treatment if present
        if treatment:
            treatment.apply(run_ctx)

        data = self.datasource.fetch(run_ctx)
        metrics = self.pipeline.run(data, run_ctx)
        return metrics

    # ------------------------------------------------------------------ #

    def run(self) -> Result:
        baseline_samples: List[Mapping[str, Any]] = []
        treatment_samples: Dict[str, List[Mapping[str, Any]]] = {
            t.name: [] for t in self.treatments
        }

        errors: Dict[str, Exception] = {}

        # ---------- replicate loop ------------------------------------- #
        for rep in range(self.replicates):
            base_ctx = FrozenContext({"replicate": rep, "condition": "baseline"})
            try:
                baseline_samples.append(self._run_condition(base_ctx))
            except Exception as exc:  # pragma: no cover
                errors[f"baseline_rep_{rep}"] = exc
                continue

            for t in self.treatments:
                ctx = FrozenContext({"replicate": rep, "condition": t.name})
                try:
                    treatment_samples[t.name].append(self._run_condition(ctx, t))
                except Exception as exc:  # pragma: no cover
                    errors[f"{t.name}_rep_{rep}"] = exc

        # ---------- aggregation ---------------------------------------- #
        baseline_metrics = _aggregate(baseline_samples)
        # For now verify against the FIRST treatment (extend later)
        primary_treatment = self.treatments[0]
        treat_metrics = _aggregate(treatment_samples[primary_treatment.name])

        hypothesis_result = self.hypothesis.verify(
            baseline_metrics=baseline_metrics, treatment_metrics=treat_metrics
        )

        metrics = {
            "baseline": baseline_metrics,
            primary_treatment.name: treat_metrics,
            "hypothesis": hypothesis_result,
        }

        return Result(metrics=metrics, errors=errors)
