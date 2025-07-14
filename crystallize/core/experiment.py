from __future__ import annotations

from collections import defaultdict
from typing import (
    Any,
    DefaultDict,
    Dict,
    List,
    Mapping,
    Optional,
    Sequence,
    Tuple,
)

from crystallize.core.plugins import (
    BasePlugin,
    LoggingPlugin,
    SeedPlugin,
    default_seed_function,
)
from crystallize.core.execution import SerialExecution, VALID_EXECUTOR_TYPES
from crystallize.core.context import FrozenContext
from crystallize.core.datasource import DataSource
from crystallize.core.hypothesis import Hypothesis
from crystallize.core.pipeline import Pipeline
from crystallize.core.result import Result
from crystallize.core.result_structs import (
    ExperimentMetrics,
    HypothesisResult,
    TreatmentMetrics,
)
from crystallize.core.treatment import Treatment
from crystallize.core.optimizers import BaseOptimizer, Objective


def _run_replicate_remote(args: Tuple["Experiment", int]) -> Tuple[
    Optional[Mapping[str, Any]],
    Optional[int],
    Dict[str, Mapping[str, Any]],
    Dict[str, int],
    Dict[str, Exception],
    Dict[str, List[Mapping[str, Any]]],
]:
    exp, rep = args
    return exp._execute_replicate(rep)


class Experiment:
    VALID_EXECUTOR_TYPES = VALID_EXECUTOR_TYPES
    """Central orchestrator for running and evaluating experiments.

    An ``Experiment`` coordinates data loading, pipeline execution, treatment
    application and hypothesis verification.  Behavior during the run is
    extended through a list of :class:`~crystallize.core.plugins.BasePlugin`
    instances, allowing custom seeding strategies, logging, artifact handling
    or alternative execution loops.  All state is communicated via a
    :class:`~crystallize.core.context.FrozenContext` instance passed through the
    pipeline steps.
    """

    def __init__(
        self,
        datasource: DataSource,
        pipeline: Pipeline,
        plugins: Optional[List[BasePlugin]] = None,
    ) -> None:
        """Instantiate an experiment configuration.

        Args:
            datasource: Object that provides the initial data for each run.
            pipeline: Pipeline executed for every replicate.
            plugins: Optional list of plugins controlling experiment behaviour.
        """
        self.datasource = datasource
        self.pipeline = pipeline
        self.treatments: List[Treatment] = []
        self.hypotheses: List[Hypothesis] = []
        self.replicates: int = 1

        self.plugins = plugins or []
        for plugin in self.plugins:
            plugin.init_hook(self)

        self._validated = False

    # ------------------------------------------------------------------ #


    def validate(self) -> None:
        if self.datasource is None or self.pipeline is None:
            raise ValueError("Experiment requires datasource and pipeline")
        self._validated = True

    # ------------------------------------------------------------------ #

    def get_plugin(self, plugin_class: type) -> Optional[BasePlugin]:
        """Return the first plugin instance matching ``plugin_class``."""
        for plugin in self.plugins:
            if isinstance(plugin, plugin_class):
                return plugin
        return None

    # ------------------------------------------------------------------ #

    def _run_condition(
        self, ctx: FrozenContext, treatment: Optional[Treatment] = None
    ) -> Tuple[Mapping[str, Any], Optional[int], List[Mapping[str, Any]]]:
        """
        Execute one pipeline run for either the baseline (treatment is None)
        or a specific treatment.
        """
        # Clone ctx to avoid cross‐run contamination
        run_ctx = FrozenContext(ctx.as_dict())

        # Apply treatment if present
        if treatment:
            treatment.apply(run_ctx)

        for plugin in self.plugins:
            plugin.before_replicate(self, run_ctx)

        local_seed: Optional[int] = run_ctx.get("seed_used")

        data = self.datasource.fetch(run_ctx)
        log_plugin = self.get_plugin(LoggingPlugin)
        verbose = log_plugin.verbose if log_plugin else False
        _, prov = self.pipeline.run(
            data,
            run_ctx,
            verbose=verbose,
            progress=False,
            rep=run_ctx.get("replicate"),
            condition=run_ctx.get("condition"),
            return_provenance=True,
            experiment=self,
        )
        return dict(run_ctx.metrics.as_dict()), local_seed, prov

    def _execute_replicate(
        self, rep: int
    ) -> Tuple[
        Optional[Mapping[str, Any]],
        Optional[int],
        Dict[str, Mapping[str, Any]],
        Dict[str, int],
        Dict[str, Exception],
        Dict[str, List[Mapping[str, Any]]],
    ]:
        baseline_result: Optional[Mapping[str, Any]] = None
        baseline_seed: Optional[int] = None
        treatment_result: Dict[str, Mapping[str, Any]] = {}
        treatment_seeds: Dict[str, int] = {}
        rep_errors: Dict[str, Exception] = {}
        provenance: Dict[str, List[Mapping[str, Any]]] = {}

        base_ctx = FrozenContext({"replicate": rep, "condition": "baseline"})
        try:
            baseline_result, baseline_seed, base_prov = self._run_condition(base_ctx)
            provenance["baseline"] = base_prov
        except Exception as exc:  # pragma: no cover
            rep_errors[f"baseline_rep_{rep}"] = exc
            return (
                baseline_result,
                baseline_seed,
                treatment_result,
                treatment_seeds,
                rep_errors,
                provenance,
            )

        for t in self.treatments:
            ctx = FrozenContext({"replicate": rep, "condition": t.name})
            try:
                result, seed, prov = self._run_condition(ctx, t)
                treatment_result[t.name] = result
                if seed is not None:
                    treatment_seeds[t.name] = seed
                provenance[t.name] = prov
            except Exception as exc:  # pragma: no cover
                rep_errors[f"{t.name}_rep_{rep}"] = exc

        return (
            baseline_result,
            baseline_seed,
            treatment_result,
            treatment_seeds,
            rep_errors,
            provenance,
        )

    # ------------------------------------------------------------------ #

    def run(
        self,
        *,
        treatments: List[Treatment] | None = None,
        hypotheses: List[Hypothesis] | None = None,
        replicates: int = 1,
    ) -> Result:
        """Execute the experiment and return a :class:`Result` instance.

        The lifecycle proceeds as follows:

        1. ``before_run`` hooks for all plugins are invoked.
        2. Each replicate is executed via ``run_experiment_loop``.  The default
           implementation runs serially, but plugins may provide parallel or
           distributed strategies.
        3. After all replicates complete, metrics are aggregated and
           hypotheses are verified.
        4. ``after_run`` hooks for all plugins are executed.

        The returned :class:`~crystallize.core.result.Result` contains aggregated
        metrics, any captured errors and a provenance record of context
        mutations for every pipeline step.
        """
        if not self._validated:
            raise RuntimeError("Experiment must be validated before execution")

        self.treatments = treatments or []
        self.hypotheses = hypotheses or []
        self.replicates = max(1, replicates)

        if self.hypotheses and not self.treatments:
            raise ValueError("Cannot verify hypotheses without treatments")

        for plugin in self.plugins:
            plugin.before_run(self)

        baseline_samples: List[Mapping[str, Any]] = []
        treatment_samples: Dict[str, List[Mapping[str, Any]]] = {
            t.name: [] for t in self.treatments
        }
        baseline_seeds: List[int] = []
        treatment_seeds_agg: Dict[str, List[int]] = {
            t.name: [] for t in self.treatments
        }
        provenance_runs: DefaultDict[str, Dict[int, List[Mapping[str, Any]]]] = (
            defaultdict(dict)
        )

        errors: Dict[str, Exception] = {}

        # ---------- replicate execution -------------------------------- #
        execution_plugin: Optional[BasePlugin] = None
        for plugin in reversed(self.plugins):
            if (
                getattr(plugin.run_experiment_loop, "__func__", None)
                is not BasePlugin.run_experiment_loop
            ):
                execution_plugin = plugin
                break

        if execution_plugin is None:
            execution_plugin = SerialExecution()

        results_list: List[
            Tuple[
                Optional[Mapping[str, Any]],
                Optional[int],
                Dict[str, Mapping[str, Any]],
                Dict[str, int],
                Dict[str, Exception],
                Dict[str, List[Mapping[str, Any]]],
            ]
        ] = execution_plugin.run_experiment_loop(
            self, self._execute_replicate
        )

        for rep, (base, seed, treats, seeds, errs, prov) in enumerate(results_list):
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

        # ---------- aggregation: preserve full sample arrays ------------ #
        def collect_all_samples(
            samples: List[Mapping[str, Sequence[Any]]],
        ) -> Dict[str, List[Any]]:
            metrics: DefaultDict[str, List[Any]] = defaultdict(list)
            for sample in samples:
                for metric, values in sample.items():
                    metrics[metric].extend(list(values))
            return dict(metrics)

        baseline_metrics = collect_all_samples(baseline_samples)
        treatment_metrics_dict = {
            name: collect_all_samples(samp) for name, samp in treatment_samples.items()
        }

        hypothesis_results: List[HypothesisResult] = []
        for hyp in self.hypotheses:
            per_treatment: Dict[str, Any] = {}
            for treatment in self.treatments:
                per_treatment[treatment.name] = hyp.verify(
                    baseline_metrics=baseline_metrics,
                    treatment_metrics=treatment_metrics_dict[treatment.name],
                )
            hypothesis_results.append(
                HypothesisResult(
                    name=hyp.name,
                    results=per_treatment,
                    ranking=hyp.rank_treatments(per_treatment),
                )
            )

        metrics = ExperimentMetrics(
            baseline=TreatmentMetrics(baseline_metrics),
            treatments={
                name: TreatmentMetrics(m) for name, m in treatment_metrics_dict.items()
            },
            hypotheses=hypothesis_results,
        )

        provenance = {
            "pipeline_signature": self.pipeline.signature(),
            "replicates": self.replicates,
            "seeds": {"baseline": baseline_seeds, **treatment_seeds_agg},
            "ctx_changes": {k: v for k, v in provenance_runs.items()},
        }

        result = Result(metrics=metrics, errors=errors, provenance=provenance)

        for plugin in self.plugins:
            plugin.after_run(self, result)

        return result

    # ------------------------------------------------------------------ #
    def apply(
        self,
        treatment: Treatment | None = None,
        *,
        data: Any | None = None,
        seed: Optional[int] = None,
    ) -> Any:
        """Run the pipeline once with optional treatment and return outputs."""
        if not self._validated:
            raise RuntimeError("Experiment must be validated before execution")

        ctx = FrozenContext({"condition": treatment.name if treatment else "baseline"})
        if treatment:
            treatment.apply(ctx)

        if seed is not None:
            seed_plugin = self.get_plugin(SeedPlugin)
            if seed_plugin is not None:
                fn = seed_plugin.seed_fn or default_seed_function
                fn(seed)
                ctx.add("seed_used", seed)

        if data is None:
            data = self.datasource.fetch(ctx)

        if not any(
            getattr(step, "is_exit_step", False) for step in self.pipeline.steps
        ):
            raise ValueError("Pipeline must contain an exit_step for apply()")

        for step in self.pipeline.steps:
            data = step(data, ctx)
            if getattr(step, "is_exit_step", False):
                break

        return data

    # ------------------------------------------------------------------ #

    def optimize(
        self,
        optimizer: "BaseOptimizer",
        num_trials: int,
        replicates_per_trial: int = 1,
    ) -> Treatment:
        self.validate()

        for _ in range(num_trials):
            treatments_for_trial = optimizer.ask()
            result = self.run(
                treatments=treatments_for_trial,
                hypotheses=[],
                replicates=replicates_per_trial,
            )
            objective_values = self._extract_objective_from_result(
                result, optimizer.objective
            )
            optimizer.tell(objective_values)

        return optimizer.get_best_treatment()

    def _extract_objective_from_result(
        self, result: Result, objective: "Objective"
    ) -> dict[str, float]:
        treatment_name = list(result.metrics.treatments.keys())[0]
        metric_values = result.metrics.treatments[treatment_name].metrics[
            objective.metric
        ]
        aggregated_value = sum(metric_values) / len(metric_values)
        return {objective.metric: aggregated_value}

