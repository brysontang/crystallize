from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
from typing import Any, DefaultDict, Dict, List, Mapping, Optional

from crystallize.core.context import FrozenContext
from crystallize.core.datasource import DataSource
from crystallize.core.hypothesis import Hypothesis
from crystallize.core.pipeline import Pipeline
from crystallize.core.result import Result
from crystallize.core.treatment import Treatment


class Experiment:
    """
    Orchestrates baseline + treatment pipelines across replicates, then verifies
    one or more hypotheses using aggregated metrics.
    """

    def __init__(
        self,
        datasource: DataSource,
        pipeline: Pipeline,
        treatments: List[Treatment],
        hypotheses: List[Hypothesis],
        replicates: int = 1,
    ):
        self.datasource = datasource
        self.pipeline = pipeline
        self.treatments = treatments
        self.hypotheses = hypotheses
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
        def collect_all_samples(
            samples: List[Mapping[str, Any]],
        ) -> Dict[str, List[Any]]:
            metrics: DefaultDict[str, List[Any]] = defaultdict(list)
            for sample in samples:
                for metric, value in sample.items():
                    metrics[metric].append(value)
            return dict(metrics)

        baseline_metrics = collect_all_samples(baseline_samples)
        treatment_metrics_dict = {
            name: collect_all_samples(samp) for name, samp in treatment_samples.items()
        }

        hypothesis_results: Dict[str, Dict[str, Any]] = {}
        for hyp in self.hypotheses:
            per_treatment: Dict[str, Any] = {}
            for treatment in self.treatments:
                per_treatment[treatment.name] = hyp.verify(
                    baseline_metrics=baseline_metrics,
                    treatment_metrics=treatment_metrics_dict[treatment.name],
                )
            hypothesis_results[hyp.name] = per_treatment

        metrics = {
            "baseline": baseline_metrics,
            **treatment_metrics_dict,
            "hypotheses": hypothesis_results,
        }

        provenance = {
            "pipeline_signature": self.pipeline.signature(),
            "replicates": self.replicates,
        }

        return Result(metrics=metrics, errors=errors, provenance=provenance)
