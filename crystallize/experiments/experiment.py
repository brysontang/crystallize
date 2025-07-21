from __future__ import annotations

import json
from collections import defaultdict
from contextlib import contextmanager
import logging
from pathlib import Path
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

from crystallize.utils.context import FrozenContext
from crystallize.datasources import Artifact
from crystallize.datasources.datasource import DataSource
from crystallize.plugins.execution import VALID_EXECUTOR_TYPES, SerialExecution
from crystallize.experiments.hypothesis import Hypothesis
from crystallize.experiments.optimizers import BaseOptimizer, Objective
from crystallize.pipelines.pipeline import Pipeline
from crystallize.plugins.plugins import (
    ArtifactPlugin,
    BasePlugin,
    LoggingPlugin,
    SeedPlugin,
    default_seed_function,
)
from crystallize.experiments.result import Result
from crystallize.experiments.result_structs import (
    ExperimentMetrics,
    HypothesisResult,
    TreatmentMetrics,
    AggregateData,
)
from crystallize.experiments.run_results import ReplicateResult
from crystallize.experiments.treatment import Treatment
from crystallize.utils.constants import (
    METADATA_FILENAME,
    BASELINE_CONDITION,
    REPLICATE_KEY,
    CONDITION_KEY,
    SEED_USED_KEY,
)


def _run_replicate_remote(
    args: Tuple["Experiment", int, List[Treatment]],
) -> ReplicateResult:
    """Wrapper for parallel executor to run a single replicate."""

    exp, rep, treatments = args
    return exp._execute_replicate(rep, treatments)


class Experiment:
    VALID_EXECUTOR_TYPES = VALID_EXECUTOR_TYPES
    """Central orchestrator for running and evaluating experiments.

    An ``Experiment`` coordinates data loading, pipeline execution, treatment
    application and hypothesis verification.  Behavior during the run is
    extended through a list of :class:`~crystallize.plugins.plugins.BasePlugin`
    instances, allowing custom seeding strategies, logging, artifact handling
    or alternative execution loops.  All state is communicated via a
    :class:`~crystallize.utils.context.FrozenContext` instance passed through the
    pipeline steps.
    """

    def __init__(
        self,
        datasource: DataSource,
        pipeline: Pipeline,
        plugins: Optional[List[BasePlugin]] = None,
        *,
        name: str | None = None,
        initial_ctx: Dict[str, Any] | None = None,
        outputs: List[Artifact] | None = None,
    ) -> None:
        """Instantiate an experiment configuration.

        Args:
            datasource: Object that provides the initial data for each run.
            pipeline: Pipeline executed for every replicate.
            plugins: Optional list of plugins controlling experiment behaviour.
            name: Optional experiment name used for artifact storage.
        """
        self.datasource = datasource
        self.pipeline = pipeline
        self.name = name
        self.id: Optional[str] = None
        outputs = outputs or []
        self.outputs: Dict[str, Artifact] = {a.name: a for a in outputs}
        for a in outputs:
            a._producer = self

        self._setup_ctx = FrozenContext({})
        if initial_ctx:
            for key, val in initial_ctx.items():
                self._setup_ctx.add(key, val)

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

    @contextmanager
    def _runtime_state(
        self,
        treatments: List[Treatment],
        hypotheses: List[Hypothesis],
        replicates: int,
    ):
        old_treatments = getattr(self, "_treatments", None)
        old_hypotheses = getattr(self, "_hypotheses", None)
        old_replicates = getattr(self, "_replicates", None)
        self._treatments = treatments
        self._hypotheses = hypotheses
        self._replicates = replicates
        try:
            yield
        finally:
            if old_treatments is None:
                delattr(self, "_treatments")
            else:
                self._treatments = old_treatments
            if old_hypotheses is None:
                delattr(self, "_hypotheses")
            else:
                self._hypotheses = old_hypotheses
            if old_replicates is None:
                delattr(self, "_replicates")
            else:
                self._replicates = old_replicates

    # ------------------------------------------------------------------ #

    @property
    def treatments(self) -> List[Treatment]:
        return getattr(self, "_treatments", [])

    @treatments.setter
    def treatments(self, value: List[Treatment]) -> None:
        self._treatments = value

    @property
    def hypotheses(self) -> List[Hypothesis]:
        return getattr(self, "_hypotheses", [])

    @hypotheses.setter
    def hypotheses(self, value: List[Hypothesis]) -> None:
        self._hypotheses = value

    @property
    def replicates(self) -> int:
        return getattr(self, "_replicates", 1)

    @replicates.setter
    def replicates(self, value: int) -> None:
        self._replicates = value

    # ------------------------------------------------------------------ #

    def artifact_datasource(
        self,
        step: str,
        name: str = "data.json",
        condition: str = BASELINE_CONDITION,
        *,
        require_metadata: bool = False,
    ) -> DataSource:
        """Return a datasource providing :class:`pathlib.Path` objects to artifacts.

        Parameters
        ----------
        step:
            Pipeline step name that produced the artifact.
        name:
            Artifact file name.
        condition:
            Condition directory to load from. Defaults to ``"baseline"``.
        require_metadata:
            If ``True`` and ``metadata.json`` does not exist, raise a
            ``FileNotFoundError``. When ``False`` (default), missing metadata
            means replicates are inferred from the experiment instance.
        """

        plugin = self.get_plugin(ArtifactPlugin)
        if plugin is None:
            raise RuntimeError("ArtifactPlugin required to load artifacts")

        if self.id is None:
            from crystallize.utils.cache import compute_hash

            self.id = compute_hash(self.pipeline.signature())

        exp_dir = self.name or self.id

        version = getattr(plugin, "version", None)
        if version is None:
            base_dir = Path(plugin.root_dir) / exp_dir
            versions = [
                int(p.name[1:])
                for p in base_dir.glob("v*")
                if p.name.startswith("v") and p.name[1:].isdigit()
            ]
            version = max(versions, default=0)
        base = Path(plugin.root_dir) / exp_dir / f"v{version}"
        meta_path = base / METADATA_FILENAME
        replicates = self.replicates
        if meta_path.exists():
            with open(meta_path) as f:
                meta = json.load(f)
            replicates = meta.get("replicates", replicates)
        elif require_metadata:
            raise FileNotFoundError(
                f"Metadata missing: {meta_path}. Did the experiment run with ArtifactPlugin?"
            )

        class ArtifactDataSource(DataSource):
            def __init__(self) -> None:
                self.replicates = replicates
                self.required_outputs = [Artifact(name)]

            def fetch(self, ctx: FrozenContext) -> Any:
                rep = ctx.get("replicate", 0)
                path = base / f"replicate_{rep}" / condition / step / name
                if not path.exists():
                    raise FileNotFoundError(
                        f"Artifact {path} missing for rep {rep}. "
                        "Ensure previous experiment ran with ArtifactPlugin and matching replicates/step/name."
                    )
                return path

        return ArtifactDataSource()

    # ------------------------------------------------------------------ #

    def _run_condition(
        self, ctx: FrozenContext, treatment: Optional[Treatment] = None
    ) -> Tuple[Mapping[str, Any], Optional[int], List[Mapping[str, Any]]]:
        """
        Execute one pipeline run for either the baseline (treatment is None)
        or a specific treatment.
        """
        # Clone ctx to avoid cross-run contamination and attach logger
        log_plugin = self.get_plugin(LoggingPlugin)
        logger = logging.getLogger("crystallize") if log_plugin else logging.getLogger()
        run_ctx = FrozenContext(ctx.as_dict(), logger=logger)

        # Apply treatment if present
        if treatment:
            treatment.apply(run_ctx)

        for plugin in self.plugins:
            plugin.before_replicate(self, run_ctx)

        local_seed: Optional[int] = run_ctx.get(SEED_USED_KEY)

        data = self.datasource.fetch(run_ctx)
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
        self,
        rep: int,
        treatments: List[Treatment],
        *,
        run_baseline: bool = True,
    ) -> ReplicateResult:
        baseline_result: Optional[Mapping[str, Any]] = None
        baseline_seed: Optional[int] = None
        treatment_result: Dict[str, Mapping[str, Any]] = {}
        treatment_seeds: Dict[str, int] = {}
        rep_errors: Dict[str, Exception] = {}
        provenance: Dict[str, List[Mapping[str, Any]]] = {}

        base_ctx = FrozenContext(
            {
                **self._setup_ctx.as_dict(),
                REPLICATE_KEY: rep,
                CONDITION_KEY: BASELINE_CONDITION,
            }
        )
        if run_baseline:
            try:
                baseline_result, baseline_seed, base_prov = self._run_condition(base_ctx)
                provenance[BASELINE_CONDITION] = base_prov
            except Exception as exc:  # pragma: no cover
                rep_errors[f"baseline_rep_{rep}"] = exc
                return ReplicateResult(
                    baseline_metrics=baseline_result,
                    baseline_seed=baseline_seed,
                    treatment_metrics=treatment_result,
                    treatment_seeds=treatment_seeds,
                    errors=rep_errors,
                    provenance=provenance,
                )

        for t in treatments:
            ctx = FrozenContext(
                {
                    **self._setup_ctx.as_dict(),
                    "replicate": rep,
                    "condition": t.name,
                }
            )
            try:
                result, seed, prov = self._run_condition(ctx, t)
                treatment_result[t.name] = result
                if seed is not None:
                    treatment_seeds[t.name] = seed
                provenance[t.name] = prov
            except Exception as exc:  # pragma: no cover
                rep_errors[f"{t.name}_rep_{rep}"] = exc

        return ReplicateResult(
            baseline_metrics=baseline_result,
            baseline_seed=baseline_seed,
            treatment_metrics=treatment_result,
            treatment_seeds=treatment_seeds,
            errors=rep_errors,
            provenance=provenance,
        )

    def _select_execution_plugin(self) -> BasePlugin:
        for plugin in reversed(self.plugins):
            if (
                getattr(plugin.run_experiment_loop, "__func__", None)
                is not BasePlugin.run_experiment_loop
            ):
                return plugin
        return SerialExecution()

    def _aggregate_results(self, results_list: List[ReplicateResult]) -> AggregateData:
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

        return AggregateData(
            baseline_metrics=baseline_metrics,
            treatment_metrics_dict=treatment_metrics_dict,
            baseline_seeds=baseline_seeds,
            treatment_seeds_agg=treatment_seeds_agg,
            provenance_runs=provenance_runs,
            errors=errors,
        )

    def _verify_hypotheses(
        self,
        baseline_metrics: Dict[str, List[Any]],
        treatment_metrics_dict: Dict[str, Dict[str, List[Any]]],
    ) -> List[HypothesisResult]:
        results: List[HypothesisResult] = []
        for hyp in self.hypotheses:
            per_treatment = {
                t.name: hyp.verify(
                    baseline_metrics=baseline_metrics,
                    treatment_metrics=treatment_metrics_dict[t.name],
                )
                for t in self.treatments
            }
            results.append(
                HypothesisResult(
                    name=hyp.name,
                    results=per_treatment,
                    ranking=hyp.rank_treatments(per_treatment),
                )
            )
        return results

    def _build_result(
        self,
        metrics: ExperimentMetrics,
        errors: Dict[str, Exception],
        provenance_runs: DefaultDict[str, Dict[int, List[Mapping[str, Any]]]],
        baseline_seeds: List[int],
        treatment_seeds_agg: Dict[str, List[int]],
    ) -> Result:
        provenance = {
            "pipeline_signature": self.pipeline.signature(),
            "replicates": self.replicates,
            "seeds": {BASELINE_CONDITION: baseline_seeds, **treatment_seeds_agg},
            "ctx_changes": {k: v for k, v in provenance_runs.items()},
        }
        return Result(metrics=metrics, errors=errors, provenance=provenance)

    # ------------------------------------------------------------------ #

    def run(
        self,
        *,
        treatments: List[Treatment] | None = None,
        hypotheses: List[Hypothesis] | None = None,
        replicates: int | None = None,
        strategy: str = "rerun",
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

        The returned :class:`~crystallize.experiments.result.Result` contains aggregated
        metrics, any captured errors and a provenance record of context
        mutations for every pipeline step.
        """
        if not self._validated:
            raise RuntimeError("Experiment must be validated before execution")

        treatments = treatments or []
        hypotheses = hypotheses or []

        datasource_reps = getattr(self.datasource, "replicates", None)
        if replicates is None:
            replicates = datasource_reps or 1
        replicates = max(1, replicates)
        if datasource_reps is not None and datasource_reps != replicates:
            raise ValueError("Replicates mismatch with datasource metadata")

        from crystallize.utils.cache import compute_hash

        self.id = compute_hash(self.pipeline.signature())

        if hypotheses and not treatments:
            raise ValueError("Cannot verify hypotheses without treatments")

        plugin = self.get_plugin(ArtifactPlugin)

        loaded_metrics: Dict[str, Dict[str, List[Any]]] = {}
        to_run = []
        base_dir: Optional[Path] = None
        if strategy == "resume" and plugin is not None:
            base_dir = Path(plugin.root_dir) / (self.name or self.id) / "v0"
            if base_dir.exists():
                for cond in [BASELINE_CONDITION] + [t.name for t in treatments]:
                    res_file = base_dir / cond / "results.json"
                    marker = base_dir / cond / ".crystallize_complete"
                    if res_file.exists() and marker.exists():
                        with open(res_file) as f:
                            loaded_metrics[cond] = json.load(f).get("metrics", {})
                    else:
                        to_run.append(cond)
            else:
                to_run = [BASELINE_CONDITION] + [t.name for t in treatments]
        else:
            to_run = [BASELINE_CONDITION] + [t.name for t in treatments]

        run_baseline = BASELINE_CONDITION in to_run
        active_treatments = [t for t in treatments if t.name in to_run]

        with self._runtime_state(treatments, hypotheses, replicates):
            for plugin in self.plugins:
                plugin.before_run(self)

            try:
                for step in self.pipeline.steps:
                    step.setup(self._setup_ctx)

                execution_plugin = self._select_execution_plugin()
                results_list = []
                if run_baseline or active_treatments:
                    results_list = execution_plugin.run_experiment_loop(
                        self,
                        lambda rep: self._execute_replicate(
                            rep,
                            active_treatments,
                            run_baseline=run_baseline,
                        ),
                    )

                aggregate = self._aggregate_results(results_list)

                # merge loaded metrics
                for metric, vals in loaded_metrics.get(BASELINE_CONDITION, {}).items():
                    aggregate.baseline_metrics.setdefault(metric, []).extend(vals)
                for t_name, metrics_dict in loaded_metrics.items():
                    if t_name == BASELINE_CONDITION:
                        continue
                    dest = aggregate.treatment_metrics_dict.setdefault(t_name, {})
                    for m, vals in metrics_dict.items():
                        dest.setdefault(m, []).extend(vals)

                hypothesis_results = self._verify_hypotheses(
                    aggregate.baseline_metrics,
                    aggregate.treatment_metrics_dict,
                )

                metrics = ExperimentMetrics(
                    baseline=TreatmentMetrics(aggregate.baseline_metrics),
                    treatments={
                        name: TreatmentMetrics(m)
                        for name, m in aggregate.treatment_metrics_dict.items()
                    },
                    hypotheses=hypothesis_results,
                )

                result = self._build_result(
                    metrics,
                    aggregate.errors,
                    aggregate.provenance_runs,
                    aggregate.baseline_seeds,
                    aggregate.treatment_seeds_agg,
                )
            finally:
                for step in self.pipeline.steps:
                    step.teardown(self._setup_ctx)

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
        """Run the pipeline once and return the output.

        This method mirrors :meth:`run` for a single replicate. Plugin hooks
        are executed and all pipeline steps receive ``setup`` and ``teardown``
        calls.
        """
        if not self._validated:
            raise RuntimeError("Experiment must be validated before execution")

        from crystallize.utils.cache import compute_hash

        self.id = compute_hash(self.pipeline.signature())

        datasource_reps = getattr(self.datasource, "replicates", None)
        replicates = datasource_reps or 1

        ctx = FrozenContext(
            {CONDITION_KEY: treatment.name if treatment else BASELINE_CONDITION}
        )
        if treatment:
            treatment.apply(ctx)

        with self._runtime_state([treatment] if treatment else [], [], replicates):
            for plugin in self.plugins:
                if isinstance(plugin, SeedPlugin) and seed is not None:
                    continue
                plugin.before_run(self)

            try:
                for step in self.pipeline.steps:
                    step.setup(ctx)

                for plugin in self.plugins:
                    if isinstance(plugin, SeedPlugin) and seed is not None:
                        continue
                    plugin.before_replicate(self, ctx)

                if seed is not None:
                    seed_plugin = self.get_plugin(SeedPlugin)
                    if seed_plugin is not None:
                        fn = seed_plugin.seed_fn or default_seed_function
                        fn(seed)
                        ctx.add(SEED_USED_KEY, seed)

                if data is None:
                    data = self.datasource.fetch(ctx)

                for step in self.pipeline.steps:
                    data = step(data, ctx)
                    for plugin in self.plugins:
                        plugin.after_step(self, step, data, ctx)

                metrics = ExperimentMetrics(
                    baseline=TreatmentMetrics(
                        {k: list(v) for k, v in ctx.metrics.as_dict().items()}
                    ),
                    treatments={},
                    hypotheses=[],
                )
                provenance = {
                    "pipeline_signature": self.pipeline.signature(),
                    "replicates": 1,
                    "seeds": {BASELINE_CONDITION: [ctx.get(SEED_USED_KEY, None)]},
                    "ctx_changes": {
                        BASELINE_CONDITION: {0: self.pipeline.get_provenance()}
                    },
                }
                result = Result(metrics=metrics, provenance=provenance)
            finally:
                for step in self.pipeline.steps:
                    step.teardown(self._setup_ctx)

            for plugin in self.plugins:
                plugin.after_run(self, result)

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
