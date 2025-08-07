import logging
from typing import Any, Dict, List, Mapping, Optional, Tuple, TYPE_CHECKING
import inspect

if TYPE_CHECKING:
    from crystallize.experiments.experiment import Experiment

from crystallize.utils.cache import compute_hash, load_cache, store_cache
from crystallize.utils.context import FrozenContext, LoggingContext
from crystallize.utils.exceptions import PipelineExecutionError
from crystallize.pipelines.pipeline_step import PipelineStep


class Pipeline:
    """Linear sequence of :class:`PipelineStep` objects forming an experiment workflow."""

    def __init__(self, steps: List[PipelineStep]) -> None:
        if not steps:
            raise ValueError("Pipeline must contain at least one step.")
        self.steps = steps

    # ------------------------------------------------------------------ #

    async def arun(
        self,
        data: Any,
        ctx: FrozenContext,
        *,
        verbose: bool = False,
        progress: bool = False,
        rep: Optional[int] = None,
        condition: Optional[str] = None,
        logger: Optional[logging.Logger] = None,
        return_provenance: bool = False,
        experiment: Optional["Experiment"] = None,
    ) -> Any | Tuple[Any, List[Mapping[str, Any]]]:
        """Run the sequence of steps on ``data`` using ``ctx``.

        Steps may read from or write to the context and record metrics. When a
        step is marked as cacheable its outputs are stored on disk keyed by its
        input hash and parameters.  Subsequent runs will reuse cached results if
        available.

        Args:
            data: Raw input from a :class:`DataSource`.
            ctx: Immutable execution context shared across steps.

        Returns:
            Either the pipeline output or ``(output, provenance)`` when
            ``return_provenance`` is ``True``. The provenance list contains a
            record per step detailing cache hits and context mutations.
        """
        logger = logger or logging.getLogger("crystallize")

        target_ctx: FrozenContext | LoggingContext
        target_ctx = LoggingContext(ctx, logger) if verbose else ctx

        provenance: List[Dict[str, Any]] = []
        step_iter = enumerate(self.steps)
        if progress and len(self.steps) > 1:
            from tqdm import tqdm  # type: ignore

            step_iter = tqdm(step_iter, total=len(self.steps), desc="Steps")

        for i, step in step_iter:
            try:
                del target_ctx._data["step_name"]
            except KeyError:
                pass
            target_ctx.add("step_name", step.__class__.__name__)
            if verbose and isinstance(target_ctx, LoggingContext):
                target_ctx.reads.clear()

            pre_ctx = dict(ctx.as_dict())
            pre_metrics = {k: tuple(v) for k, v in ctx.metrics.as_dict().items()}
            try:
                step_hash = step.step_hash
            except Exception as exc:
                print(f"Error in step {step.__class__.__name__}: {exc}")
                raise exc

            input_hash = compute_hash(data)

            if experiment is not None:
                for plugin in experiment.plugins:
                    plugin.before_step(experiment, step)

            if step.cacheable:
                try:
                    result = load_cache(step_hash, input_hash)
                    cache_hit = True
                except (FileNotFoundError, IOError):
                    try:
                        result = step(data, target_ctx)
                        if inspect.isawaitable(result):
                            result = await result
                    except Exception as exc:
                        raise PipelineExecutionError(
                            step.__class__.__name__, exc
                        ) from exc
                    store_cache(step_hash, input_hash, result)
                    cache_hit = False
            else:
                try:
                    result = step(data, target_ctx)
                    if inspect.isawaitable(result):
                        result = await result
                except Exception as exc:
                    raise PipelineExecutionError(step.__class__.__name__, exc) from exc
                cache_hit = False

            data, step_metrics = self._unpack_result(result)
            if step_metrics is not None:
                for key, value in step_metrics.items():
                    ctx.metrics.add(key, value)

            if experiment is not None:
                for plugin in experiment.plugins:
                    plugin.after_step(experiment, step, data, ctx)
            if (
                cache_hit
                and i == len(self.steps) - 1
                and step_metrics is None
                and isinstance(data, Mapping)
            ):
                for key, value in data.items():
                    ctx.metrics.add(key, value)

            reads = (
                target_ctx.reads.copy()
                if verbose and isinstance(target_ctx, LoggingContext)
                else {}
            )
            try:
                self._record_provenance(
                    provenance,
                    step,
                    data,
                    ctx,
                    pre_ctx,
                    pre_metrics,
                    cache_hit,
                    step_hash,
                    input_hash,
                    reads,
                )
            except Exception as exc:
                raise exc

        final_provenance = tuple(provenance)
        self._provenance = final_provenance
        total_steps = len(self.steps) or 1
        logger.info(
            "Cache hit rate: %.0f%% (%d/%d steps)",
            (hit_count := sum(1 for p in provenance if p["cache_hit"]))
            / total_steps
            * 100,
            hit_count,
            len(self.steps),
        )

        if return_provenance:
            return data, [dict(p) for p in final_provenance]
        return data

    # ------------------------------------------------------------------ #

    def run(
        self,
        data: Any,
        ctx: FrozenContext,
        *,
        verbose: bool = False,
        progress: bool = False,
        rep: Optional[int] = None,
        condition: Optional[str] = None,
        logger: Optional[logging.Logger] = None,
        return_provenance: bool = False,
        experiment: Optional["Experiment"] = None,
    ) -> Any | Tuple[Any, List[Mapping[str, Any]]]:
        """Synchronous wrapper around :meth:`arun`."""

        import asyncio

        return asyncio.run(
            self.arun(
                data,
                ctx,
                verbose=verbose,
                progress=progress,
                rep=rep,
                condition=condition,
                logger=logger,
                return_provenance=return_provenance,
                experiment=experiment,
            )
        )

    def _record_provenance(
        self,
        provenance: List[Dict[str, Any]],
        step: PipelineStep,
        data: Any,
        ctx: FrozenContext,
        pre_ctx: Mapping[str, Any],
        pre_metrics: Mapping[str, Tuple[Any, ...]],
        cache_hit: bool,
        step_hash: str,
        input_hash: str,
        reads: Mapping[str, Any],
    ) -> None:
        post_ctx_items = ctx.as_dict()
        post_metrics_items = ctx.metrics.as_dict()
        wrote = {
            k: {"before": pre_ctx.get(k), "after": v}
            for k, v in post_ctx_items.items()
            if k not in pre_ctx or pre_ctx[k] != v
        }
        metrics_diff: Dict[str, Dict[str, Tuple[Any, ...]]] = {}
        for k, vals in post_metrics_items.items():
            prev = pre_metrics.get(k, ())
            if vals != prev:
                metrics_diff[k] = {"before": prev, "after": vals}

        provenance.append(
            {
                "step": step.__class__.__name__,
                "params": step.params,
                "step_hash": step_hash,
                "input_hash": input_hash,
                "output_hash": compute_hash(data),
                "cache_hit": cache_hit,
                "ctx_changes": {
                    "reads": reads,
                    "wrote": wrote,
                    "metrics": metrics_diff,
                },
            }
        )

    def _unpack_result(self, result: Any) -> Tuple[Any, Optional[Mapping[str, Any]]]:
        """Separate step output into data and metrics if present."""
        if (
            isinstance(result, tuple)
            and len(result) == 2
            and isinstance(result[1], Mapping)
        ):
            return result[0], result[1]
        return result, None

    def signature(self) -> str:
        """Hash‐friendly signature for caching/provenance."""
        parts = [step.__class__.__name__ + repr(step.params) for step in self.steps]
        return "|".join(parts)

    # ------------------------------------------------------------------ #
    def get_provenance(self) -> List[Mapping[str, Any]]:
        """Return immutable provenance from the last run."""

        return list(getattr(self, "_provenance", ()))
