from __future__ import annotations

import statistics as _stats
from copy import deepcopy
from typing import Any, Dict, List, Mapping, Optional

from crystallize.core.context import FrozenContext
from crystallize.core.datasource import DataSource
from crystallize.core.hypothesis import Hypothesis
from crystallize.core.pipeline import Pipeline
from crystallize.core.result import Result
from crystallize.core.treatment import Treatment


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

        # ---------- aggregation: preserve full sample arrays ------------ #
        def collect_samples(samples: List[Mapping[str, Any]], metric: str) -> List[float]:
            return [sample[metric] for sample in samples if metric in sample]

        baseline_metric_samples = collect_samples(baseline_samples, self.hypothesis.metric)
        primary_treatment = self.treatments[0]
        treatment_metric_samples = collect_samples(
            treatment_samples[primary_treatment.name], self.hypothesis.metric
        )

        # hypothesis verification (pass arrays directly)
        hypothesis_result = self.hypothesis.verify(
            baseline_metrics={self.hypothesis.metric: baseline_metric_samples},
            treatment_metrics={self.hypothesis.metric: treatment_metric_samples},
        )

        metrics = {
            "baseline": {self.hypothesis.metric: baseline_metric_samples},
            primary_treatment.name: {self.hypothesis.metric: treatment_metric_samples},
            "hypothesis": hypothesis_result,
        }

        provenance = {
            "pipeline_signature": self.pipeline.signature(),
            "replicates": self.replicates,
        }

        return Result(metrics=metrics, errors=errors, provenance=provenance)