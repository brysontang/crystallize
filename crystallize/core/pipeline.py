import logging
from typing import Any, Dict, List, Mapping, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from crystallize.core.experiment import Experiment

from crystallize.core.cache import compute_hash, load_cache, store_cache
from crystallize.core.context import FrozenContext, LoggingContext
from crystallize.core.exceptions import PipelineExecutionError
from crystallize.core.pipeline_step import PipelineStep


class Pipeline:
    """Linear sequence of :class:`PipelineStep` objects."""

    def __init__(self, steps: List[PipelineStep]) -> None:
        if not steps:
            raise ValueError("Pipeline must contain at least one step.")
        self.steps = steps

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
        """
        Execute the pipeline in order.

        Args:
            data: Raw data from a DataSource.
            ctx:  Immutable execution context.

        Returns:
            If ``return_provenance`` is ``False`` (default), returns the output
            from the last step. Otherwise returns a tuple ``(output,
            provenance)`` where ``provenance`` is a list of step records.
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
            if verbose and isinstance(target_ctx, LoggingContext):
                target_ctx.reads.clear()

            pre_ctx = dict(ctx.as_dict())
            pre_metrics = {k: tuple(v) for k, v in ctx.metrics.as_dict().items()}
            step_hash = step.step_hash
            input_hash = compute_hash(data)
            if step.cacheable:
                try:
                    data = load_cache(step_hash, input_hash)
                    cache_hit = True
                except (FileNotFoundError, IOError):
                    try:
                        data = step(data, target_ctx)
                    except Exception as exc:
                        raise PipelineExecutionError(
                            step.__class__.__name__, exc
                        ) from exc
                    store_cache(step_hash, input_hash, data)
                    cache_hit = False
            else:
                try:
                    data = step(data, target_ctx)
                except Exception as exc:
                    raise PipelineExecutionError(step.__class__.__name__, exc) from exc
                cache_hit = False

            if experiment is not None:
                for plugin in experiment.plugins:
                    plugin.after_step(experiment, step, data, ctx)
            if cache_hit and i == len(self.steps) - 1 and isinstance(data, Mapping):
                for key, value in data.items():
                    ctx.metrics.add(key, value)

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

            reads = {}
            if verbose and isinstance(target_ctx, LoggingContext):
                reads = target_ctx.reads.copy()

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

        final_provenance = tuple(provenance)
        self._provenance = final_provenance

        hit_count = sum(1 for p in provenance if p["cache_hit"])
        logger.info(
            "Cache hit rate: %.0f%% (%d/%d steps)",
            (hit_count / len(self.steps)) * 100,
            hit_count,
            len(self.steps),
        )

        if return_provenance:
            return data, [dict(p) for p in final_provenance]
        return data


    def signature(self) -> str:
        """Hash‐friendly signature for caching/provenance."""
        parts = [step.__class__.__name__ + repr(step.params) for step in self.steps]
        return "|".join(parts)

    # ------------------------------------------------------------------ #
    def get_provenance(self) -> List[Mapping[str, Any]]:
        """Return immutable provenance from the last run."""

        return list(getattr(self, "_provenance", ()))
