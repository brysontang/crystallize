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
        datasource: Optional[DataSource] = None,
        pipeline: Optional[Pipeline] = None,
        treatments: Optional[List[Treatment]] = None,
        hypotheses: Optional[List[Hypothesis]] = None,
        replicates: int = 1,
    ) -> None:
        self.datasource = datasource
        self.pipeline = pipeline
        self.treatments = treatments or []
        self.hypotheses = hypotheses or []
        self.replicates = max(1, replicates)
        self._validated = False

    # ------------------------------------------------------------------ #

    def with_datasource(self, datasource: DataSource) -> "Experiment":
        self.datasource = datasource
        return self

    def with_pipeline(self, pipeline: Pipeline) -> "Experiment":
        self.pipeline = pipeline
        return self

    def with_treatments(self, treatments: List[Treatment]) -> "Experiment":
        self.treatments = treatments
        return self

    def with_hypotheses(self, hypotheses: List[Hypothesis]) -> "Experiment":
        self.hypotheses = hypotheses
        return self

    def with_replicates(self, replicates: int) -> "Experiment":
        self.replicates = max(1, replicates)
        return self

    def validate(self) -> None:
        if self.datasource is None or self.pipeline is None:
            raise ValueError("Experiment requires datasource and pipeline")
        if self.hypotheses and not self.treatments:
            raise ValueError("Cannot verify hypotheses without treatments")
        self._validated = True

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
        if not self._validated:
            raise RuntimeError("Experiment must be validated before execution")

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

    # ------------------------------------------------------------------ #
    def apply(
        self,
        treatment_name: Optional[str] = None,
        *,
        data: Any | None = None,
    ) -> Any:
        """Run the pipeline once with optional treatment and return outputs."""
        if not self._validated:
            raise RuntimeError("Experiment must be validated before execution")

        treatment = None
        if treatment_name:
            for t in self.treatments:
                if t.name == treatment_name:
                    treatment = t
                    break
            if treatment is None:
                raise ValueError(f"Unknown treatment '{treatment_name}'")

        ctx = FrozenContext({"condition": treatment_name or "baseline"})
        if treatment:
            treatment.apply(ctx)

        if data is None:
            data = self.datasource.fetch(ctx)

        for step in self.pipeline.steps:
            data = step(data, ctx)
            if getattr(step, "is_exit_step", False):
                break

        return data
