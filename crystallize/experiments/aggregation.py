from __future__ import annotations

from collections import defaultdict
from typing import Any, DefaultDict, Dict, List, Mapping, Sequence

from crystallize.experiments.result import Result
from crystallize.experiments.result_structs import (
    AggregateData,
    ExperimentMetrics,
)
from crystallize.experiments.run_results import ReplicateResult
from crystallize.pipelines.pipeline import Pipeline
from crystallize.utils.constants import BASELINE_CONDITION


class ResultAggregator:
    """Helper for aggregating replicate outputs into a ``Result``."""

    def __init__(self, pipeline: Pipeline, replicates: int) -> None:
        self._pipeline = pipeline
        self._replicates = replicates

    def aggregate_results(self, results_list: List[ReplicateResult]) -> AggregateData:
        baseline_samples: List[Mapping[str, Any]] = []
        treatment_samples: Dict[str, List[Mapping[str, Any]]] = defaultdict(list)
        baseline_seeds: List[int] = []
        treatment_seeds_agg: Dict[str, List[int]] = defaultdict(list)

        provenance_runs: DefaultDict[str, Dict[int, List[Mapping[str, Any]]]] = (
            defaultdict(dict)
        )
        errors: Dict[str, Exception] = {}

        for rep, res in enumerate(results_list):
            base = res.baseline_metrics
            seed = res.baseline_seed
            treats = res.treatment_metrics
            seeds = res.treatment_seeds
            errs = res.errors
            prov = res.provenance

            if base is not None:
                baseline_samples.append(base)
            if seed is not None:
                baseline_seeds.append(seed)
            for name, sample in treats.items():
                treatment_samples[name].append(sample)
            for name, sd in seeds.items():
                treatment_seeds_agg[name].append(sd)
            for name, p in prov.items():
                provenance_runs[name][rep] = p
            errors.update(errs)

        def collect_all_samples(
            samples: List[Mapping[str, Sequence[Any]]]
        ) -> Dict[str, List[Any]]:
            metrics: DefaultDict[str, List[Any]] = defaultdict(list)
            for sample in samples:
                for metric, values in sample.items():
                    metrics[metric].extend(list(values))
            return dict(metrics)

        baseline_metrics = collect_all_samples(baseline_samples)

        treatment_metrics_dict: Dict[str, Dict[str, List[Any]]] = {}
        for name, samp in treatment_samples.items():
            treatment_metrics_dict[name] = collect_all_samples(samp)

        return AggregateData(
            baseline_metrics=baseline_metrics,
            treatment_metrics_dict=treatment_metrics_dict,
            baseline_seeds=baseline_seeds,
            treatment_seeds_agg=treatment_seeds_agg,
            provenance_runs=provenance_runs,
            errors=errors,
        )

    def build_result(self, metrics: ExperimentMetrics, aggregate: AggregateData) -> Result:
        provenance = {
            "pipeline_signature": self._pipeline.signature(),
            "replicates": self._replicates,
            "seeds": {
                BASELINE_CONDITION: aggregate.baseline_seeds,
                **aggregate.treatment_seeds_agg,
            },
            "ctx_changes": {k: v for k, v in aggregate.provenance_runs.items()},
        }
        return Result(metrics=metrics, errors=aggregate.errors, provenance=provenance)
