from __future__ import annotations

import json
from collections import defaultdict
from contextlib import contextmanager
import traceback
import logging
import importlib
import sys
from pathlib import Path
from typing import (
    Any,
    Dict,
    List,
    Mapping,
    Optional,
    Tuple,
)
import inspect

from typing import TYPE_CHECKING

from crystallize.utils.context import FrozenContext
from crystallize.datasources import Artifact
from crystallize.datasources.datasource import DataSource, ExperimentInput
from crystallize.plugins.execution import (
    VALID_EXECUTOR_TYPES,
    SerialExecution,
    ParallelExecution,
)
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
from crystallize.experiments.aggregation import ResultAggregator
from crystallize.experiments.result import Result

if TYPE_CHECKING:  # pragma: no cover - imported for type checking only
    from .experiment_builder import ExperimentBuilder
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
    args: Tuple["Experiment", int, List[Treatment], Optional[Treatment]],
) -> ReplicateResult:
    """Wrapper for parallel executor to run a single replicate."""

    exp, rep, treatments, baseline_treatment = args
    import asyncio

    return asyncio.run(
        exp._execute_replicate(rep, treatments, baseline_treatment=baseline_treatment)
    )


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

    @classmethod
    def builder(cls, name: str | None = None) -> "ExperimentBuilder":
        """Return a fluent builder for constructing an ``Experiment``."""

        from .experiment_builder import ExperimentBuilder

        return ExperimentBuilder(name)

    def __init__(
        self,
        datasource: DataSource,
        pipeline: Pipeline,
        plugins: Optional[List[BasePlugin]] = None,
        *,
        description: str | None = None,
        name: str | None = None,
        initial_ctx: Dict[str, Any] | None = None,
        outputs: List[Artifact] | None = None,
        treatments: List[Treatment] | None = None,
        hypotheses: List[Hypothesis] | None = None,
        replicates: int = 1,
    ) -> None:
        """Instantiate an experiment configuration.

        Args:
            datasource: Object that provides the initial data for each run.
            pipeline: Pipeline executed for every replicate.
            plugins: Optional list of plugins controlling experiment behaviour.
            description: Optional text describing this experiment.
            name: Optional experiment name used for artifact storage.
        """
        self.datasource = datasource
        self.pipeline = pipeline
        self.name = name
        self.description = description
        self.treatments = treatments or []
        self.hypotheses = hypotheses or []
        self.replicates = replicates
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
        self.set_default_plugins()

        for plugin in self.plugins:
            plugin.init_hook(self)

        self._validated = False

        if not isinstance(self.replicates, int):
            raise TypeError(
                f"replicates must be an integer, but got {type(self.replicates).__name__}"
            )

    # ------------------------------------------------------------------ #

    def set_default_plugins(self) -> None:
        artifact_plugin = self.get_plugin(ArtifactPlugin)
        if artifact_plugin is None:
            self.plugins.append(ArtifactPlugin(root_dir="data"))

        seed_plugin = self.get_plugin(SeedPlugin)
        if seed_plugin is None:
            self.plugins.append(
                SeedPlugin(auto_seed=True, seed_fn=default_seed_function)
            )

        logging_plugin = self.get_plugin(LoggingPlugin)
        if logging_plugin is None:
            self.plugins.append(LoggingPlugin())

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
        baseline_treatment: Optional[Treatment] = None,
    ):
        old_treatments = getattr(self, "_treatments", None)
        old_hypotheses = getattr(self, "_hypotheses", None)
        old_replicates = getattr(self, "_replicates", None)
        old_baseline = getattr(self, "_baseline_treatment", None)
        self._treatments = treatments
        self._hypotheses = hypotheses
        self._replicates = replicates
        if baseline_treatment is not None:
            self._baseline_treatment = baseline_treatment
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
            if baseline_treatment is not None:
                if old_baseline is None:
                    delattr(self, "_baseline_treatment")
                else:
                    self._baseline_treatment = old_baseline

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

    async def _run_condition(
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
        _, prov = await self.pipeline.arun(
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

    async def _run_baseline_safely(
        self,
        rep: int,
        base_ctx: FrozenContext,
        baseline_treatment: Optional[Treatment],
    ) -> Tuple[
        Optional[Mapping[str, Any]],
        Optional[int],
        Optional[List[Mapping[str, Any]]],
        Optional[Exception],
    ]:
        """Run the baseline condition and capture errors for reporting."""
        try:
            metrics, seed, prov = await self._run_condition(base_ctx, baseline_treatment)
            return metrics, seed, prov, None
        except Exception as exc:
            tb_str = traceback.format_exc()
            setattr(exc, "traceback_str", tb_str)
            setattr(exc, "replicate", rep)
            setattr(exc, "condition", BASELINE_CONDITION)
            return None, None, None, exc

    async def _execute_replicate(
        self,
        rep: int,
        treatments: List[Treatment],
        *,
        run_baseline: bool = True,
        baseline_treatment: Optional[Treatment] = None,
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
            (
                baseline_result,
                baseline_seed,
                base_prov,
                base_err,
            ) = await self._run_baseline_safely(rep, base_ctx, baseline_treatment)
            if base_err:
                rep_errors[f"baseline_rep_{rep}"] = base_err
                return ReplicateResult(
                    baseline_metrics=baseline_result,
                    baseline_seed=baseline_seed,
                    treatment_metrics=treatment_result,
                    treatment_seeds=treatment_seeds,
                    errors=rep_errors,
                    provenance=provenance,
                )
            if base_prov is not None:
                provenance[BASELINE_CONDITION] = base_prov

        for t in treatments:
            ctx = FrozenContext(
                {
                    **self._setup_ctx.as_dict(),
                    "replicate": rep,
                    "condition": t.name,
                }
            )
            try:
                result, seed, prov = await self._run_condition(ctx, t)
                treatment_result[t.name] = result
                if seed is not None:
                    treatment_seeds[t.name] = seed
                provenance[t.name] = prov
            except Exception as exc:
                tb_str = traceback.format_exc()
                setattr(exc, "traceback_str", tb_str)
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

    def _verify_hypotheses(
        self,
        baseline_metrics: Dict[str, List[Any]],
        treatment_metrics_dict: Dict[str, Dict[str, List[Any]]],
        # Add this new parameter
        active_treatments: List[Treatment],
    ) -> List[HypothesisResult]:
        results: List[HypothesisResult] = []
        for hyp in self.hypotheses:
            per_treatment = {
                t.name: hyp.verify(
                    baseline_metrics=baseline_metrics,
                    treatment_metrics=treatment_metrics_dict[t.name],
                )
                # Use the new parameter here instead of self.treatments
                for t in active_treatments
                if t.name in treatment_metrics_dict
            }
            results.append(
                HypothesisResult(
                    name=hyp.name,
                    results=per_treatment,
                    ranking=hyp.rank_treatments(per_treatment),
                )
            )
        return results

    # ------------------------------------------------------------------ #

    strategy: str = "rerun"

    def run(
        self,
        *,
        treatments: List[Treatment] | None = None,
        hypotheses: List[Hypothesis] | None = None,
        replicates: int | None = None,
        strategy: str | None = None,
    ) -> Result:
        """Synchronous wrapper for the async run method. Convenient for tests and scripts."""
        import asyncio

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            raise RuntimeError(
                "An asyncio event loop is already running (likely Jupyter). "
                "Please use 'await experiment.arun(...)' instead of 'experiment.run(...)'."
            )

        return asyncio.run(
            self.arun(
                treatments=treatments,
                hypotheses=hypotheses,
                replicates=replicates,
                strategy=strategy,
            )
        )

    async def arun(
        self,
        *,
        treatments: List[Treatment] | None = None,
        hypotheses: List[Hypothesis] | None = None,
        replicates: int | None = None,
        strategy: str | None = None,
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
            try:
                self.validate()
            except Exception as exc:
                print(f"Experiment validation failed: {exc}")
                raise

        run_treatments = treatments if treatments is not None else self.treatments
        baseline_treatment = next(
            (t for t in run_treatments if t.name == BASELINE_CONDITION),
            None,
        )
        if baseline_treatment is not None:
            run_treatments = [t for t in run_treatments if t.name != BASELINE_CONDITION]
            self._baseline_treatment = baseline_treatment
        else:
            self._baseline_treatment = None
        run_hypotheses = hypotheses if hypotheses is not None else self.hypotheses

        datasource_reps = getattr(self.datasource, "replicates", None)
        if replicates is None:
            replicates = datasource_reps or self.replicates

        replicates = max(1, replicates)
        result_aggregator = ResultAggregator(self.pipeline, replicates)
        # TEST: When replicates > datasource_reps, the experiment should run with the datasource_reps % n

        from crystallize.utils.cache import compute_hash

        self.id = compute_hash(self.pipeline.signature())

        if run_hypotheses and not run_treatments:
            raise ValueError("Cannot verify hypotheses without treatments")

        strategy = strategy or self.strategy
        plugin = self.get_plugin(ArtifactPlugin)

        loaded_metrics: Dict[str, Dict[str, List[Any]]] = {}
        to_run = []
        base_dir: Optional[Path] = None
        if strategy == "resume" and plugin is not None:
            # Resuming a run: inspect previous version directories to see which
            # conditions already completed and load their metrics to avoid
            # re-executing them.
            exp_dir = Path(plugin.root_dir) / (self.name or self.id)
            versions = [
                int(p.name[1:])
                for p in exp_dir.glob("v*")
                if p.name.startswith("v") and p.name[1:].isdigit()
            ]
            if versions:
                # Use the latest version directory as the source for previously
                # completed condition metrics.
                base_dir = exp_dir / f"v{max(versions)}"
                conditions_to_check = [BASELINE_CONDITION] + [
                    t.name for t in run_treatments
                ]
                for cond in conditions_to_check:
                    res_file = base_dir / cond / "results.json"
                    marker = base_dir / cond / ".crystallize_complete"
                    # Only treat a condition as completed if both the results
                    # file and completion marker exist. Otherwise mark it to
                    # be re-run.
                    if res_file.exists() and marker.exists():
                        with open(res_file) as f:
                            loaded_metrics[cond] = json.load(f).get("metrics", {})
                    else:
                        to_run.append(cond)
            else:
                # No previous versions found; all conditions must run.
                to_run = [BASELINE_CONDITION] + [t.name for t in run_treatments]
        else:
            to_run = [BASELINE_CONDITION] + [t.name for t in run_treatments]

        run_baseline = BASELINE_CONDITION in to_run
        active_treatments = [t for t in run_treatments if t.name in to_run]
        baseline_treatment = getattr(self, "_baseline_treatment", None)

        if strategy == "resume" and not to_run:
            baseline_loaded = loaded_metrics.get(BASELINE_CONDITION, {})
            treatments_loaded = {
                k: v for k, v in loaded_metrics.items() if k != BASELINE_CONDITION
            }
            hypothesis_results = self._verify_hypotheses(
                baseline_loaded, treatments_loaded, active_treatments=run_treatments
            )
            metrics = ExperimentMetrics(
                baseline=TreatmentMetrics(baseline_loaded),
                treatments={
                    n: TreatmentMetrics(m) for n, m in treatments_loaded.items()
                },
                hypotheses=hypothesis_results,
            )
            empty_aggregate = AggregateData(
                baseline_metrics=baseline_loaded,
                treatment_metrics_dict=treatments_loaded,
                baseline_seeds=[],
                treatment_seeds_agg={t.name: [] for t in run_treatments},
                provenance_runs=defaultdict(lambda: defaultdict(list)),
                errors={},
            )
            return result_aggregator.build_result(metrics, empty_aggregate)

        with self._runtime_state(
            run_treatments,
            run_hypotheses,
            replicates,
            baseline_treatment=baseline_treatment,
        ):
            for plugin in self.plugins:
                plugin.before_run(self)

            try:
                for step in self.pipeline.steps:
                    step.setup(self._setup_ctx)

                execution_plugin = self._select_execution_plugin()
                results_list = []
                if run_baseline or active_treatments:
                    if isinstance(execution_plugin, ParallelExecution):

                        def replicate_fn(rep: int) -> ReplicateResult:
                            import asyncio

                            return asyncio.run(
                                self._execute_replicate(
                                    rep,
                                    active_treatments,
                                    run_baseline=run_baseline,
                                    baseline_treatment=baseline_treatment,
                                )
                            )

                    else:

                        async def replicate_fn(rep: int) -> ReplicateResult:
                            return await self._execute_replicate(
                                rep,
                                active_treatments,
                                run_baseline=run_baseline,
                                baseline_treatment=baseline_treatment,
                            )

                    loop_result = execution_plugin.run_experiment_loop(
                        self, replicate_fn
                    )
                    if inspect.isawaitable(loop_result):
                        results_list = await loop_result
                    else:
                        results_list = loop_result

                aggregate = result_aggregator.aggregate_results(results_list)

                # Merge metrics loaded from completed runs with newly produced
                # metrics from this execution.
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
                    active_treatments=active_treatments,
                )

                metrics = ExperimentMetrics(
                    baseline=TreatmentMetrics(aggregate.baseline_metrics),
                    treatments={
                        name: TreatmentMetrics(m)
                        for name, m in aggregate.treatment_metrics_dict.items()
                    },
                    hypotheses=hypothesis_results,
                )

                result = result_aggregator.build_result(metrics, aggregate)
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
            try:
                self.validate()
            except Exception as exc:
                print(f"Experiment validation failed: {exc}")
                raise

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
                    for plugin in self.plugins:
                        plugin.before_step(self, step)
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
        """Synchronous wrapper for :meth:`aoptimize`."""

        import asyncio

        return asyncio.run(
            self.aoptimize(
                optimizer,
                num_trials,
                replicates_per_trial,
            )
        )

    async def aoptimize(
        self,
        optimizer: "BaseOptimizer",
        num_trials: int,
        replicates_per_trial: int = 1,
    ) -> Treatment:
        self.validate()

        for _ in range(num_trials):
            treatments_for_trial = optimizer.ask()
            result = await self.arun(
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

    # ------------------------------------------------------------------ #

    @classmethod
    def from_yaml(cls, config_path: str | Path) -> "Experiment":
        """Instantiate an experiment from a folder-based YAML config."""

        import yaml

        path = Path(config_path)
        with path.open() as f:
            cfg = yaml.safe_load(f)

        base = path.parent.resolve()
        root = Path.cwd().resolve()

        def _load(mod: str, name: str):
            mod_path = base / f"{mod}.py"
            try:
                rel = mod_path.relative_to(root)
                module_name = ".".join(rel.with_suffix("").parts)
                if str(root) not in sys.path:
                    sys.path.insert(0, str(root))

                if module_name in sys.modules:
                    module = importlib.reload(sys.modules[module_name])
                else:
                    module = importlib.import_module(module_name)
            except ValueError:
                spec = importlib.util.spec_from_file_location(mod_path.stem, mod_path)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)  # type: ignore[arg-type]
                else:  # pragma: no cover - invalid path
                    raise ImportError(mod_path)
            return getattr(module, name)

        ds_mod = (base / "datasources.py").exists()
        steps_mod = (base / "steps.py").exists()
        outs_mod = (base / "outputs.py").exists()
        ver_mod = (base / "verifiers.py").exists()

        exp_name = cfg.get("name", base.name)

        if "datasource" not in cfg:
            raise ValueError("config.yaml must define a 'datasource' section.")

        ds_spec = cfg.get("datasource")
        if ds_spec in (None, {}, []):
            raise ValueError("config.yaml must declare at least one datasource.")
        if isinstance(ds_spec, list):
            tmp = {}
            for item in ds_spec:
                tmp.update(item)
            ds_spec = tmp
        elif not isinstance(ds_spec, dict):
            raise TypeError("datasource must be provided as a mapping or list of maps.")

        inputs: dict[str, DataSource | Artifact] = {}
        has_ref = False
        for alias, val in ds_spec.items():
            if isinstance(val, str) and "#" in val:
                src_exp_name, art_name = val.split("#", 1)
                art = Artifact(art_name)
                setattr(art, "_source_experiment", src_exp_name)
                inputs[alias] = art
                has_ref = True
            else:
                if not ds_mod:
                    raise FileNotFoundError(
                        "datasources.py not found"
                    )  # pragma: no cover - sanity check
                fn = _load("datasources", str(val))
                inputs[alias] = fn()

        if len(inputs) == 1 and not has_ref:
            datasource = next(iter(inputs.values()))
        else:
            datasource = ExperimentInput(**inputs)

        outputs_spec = cfg.get("outputs", {})
        outputs_map: Dict[str, Artifact] = {}
        for alias, spec in outputs_spec.items():
            loader_fn = None
            writer_fn = None
            file_name = alias  # Default file name to alias
            if isinstance(spec, dict):
                if spec.get("loader") and outs_mod:
                    loader_fn = _load("outputs", spec["loader"])
                if spec.get("writer") and outs_mod:
                    writer_fn = _load("outputs", spec["writer"])
                if spec.get("file_name"):
                    file_name = spec["file_name"]

            outputs_map[alias] = Artifact(
                name=file_name, loader=loader_fn, writer=writer_fn
            )
        outputs = list(outputs_map.values())
        used_outputs: set[str] = set()

        step_specs = cfg.get("steps", []) if steps_mod else []
        steps = []
        for s_spec in step_specs:
            step_name = s_spec
            kwargs = {}

            if isinstance(s_spec, dict):
                step_name = next(iter(s_spec.keys()))
                kwargs = s_spec[step_name]
            else:
                step_name = s_spec
                kwargs = {}
            step_factory = _load("steps", step_name)
            import inspect

            # Inspect the step factory's signature and map any Artifact parameters
            sig = inspect.signature(step_factory)
            for param_name, param in sig.parameters.items():
                if param.annotation == Artifact:
                    if param_name in kwargs and isinstance(kwargs[param_name], str):
                        alias = kwargs[param_name]
                        if alias in outputs_map:
                            kwargs[param_name] = outputs_map[alias]
                            used_outputs.add(alias)
                        else:
                            raise ValueError(
                                f"Output '{alias}' requested by step '{step_name}' is not in experiment outputs"
                            )
                    elif param_name in outputs_map and param_name not in kwargs:
                        kwargs[param_name] = outputs_map[param_name]
                        used_outputs.add(param_name)
            steps.append(step_factory(**kwargs))
        pipeline = Pipeline(steps)

        unused = set(outputs_map) - used_outputs
        if unused:
            raise ValueError(
                "Outputs not used in any step: " + ", ".join(sorted(unused))
            )

        treatments: list[Treatment] = []
        treatments_spec = cfg.get("treatments", {})
        if isinstance(treatments_spec, dict):
            for t_name, params in treatments_spec.items():
                if params is None:
                    params = {}
                elif not isinstance(params, dict):
                    raise ValueError(f"Treatment '{t_name}' must map to a dictionary")
                treatments.append(Treatment(t_name, params))
        else:
            raise TypeError("Treatments must be specified as a dictionary")

        hypotheses: list[Hypothesis] = []
        if ver_mod:
            for h in cfg.get("hypotheses", []):
                verifier_name = h.get("verifier")
                if verifier_name is None:
                    raise ValueError("Each hypothesis must specify a 'verifier'.")
                try:
                    verifier_factory = _load("verifiers", verifier_name)
                except AttributeError as exc:
                    raise ValueError(
                        f"Verifier '{verifier_name}' not found in verifiers.py"
                    ) from exc
                v_fn = verifier_factory()
                metrics = h.get("metrics")
                h_name = h.get("name")
                hypotheses.append(
                    Hypothesis(verifier=v_fn, metrics=metrics, name=h_name)
                )

        replicates = int(cfg.get("replicates", 1))

        exp = cls(
            datasource=datasource,
            pipeline=pipeline,
            plugins=None,
            description=cfg.get("description"),
            name=exp_name,
            initial_ctx=None,
            outputs=outputs,
            treatments=treatments,
            hypotheses=hypotheses,
            replicates=replicates,
        )

        exp.outputs = outputs_map
        for a in exp.outputs.values():
            a._producer = exp

        return exp
