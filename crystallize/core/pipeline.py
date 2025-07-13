from types import MappingProxyType
from typing import Any, List, Mapping

from crystallize.core.cache import compute_hash, load_cache, store_cache
from crystallize.core.context import FrozenContext
from crystallize.core.exceptions import PipelineExecutionError
from crystallize.core.pipeline_step import PipelineStep


class Pipeline:
    """Linear sequence of :class:`PipelineStep` objects."""

    def __init__(self, steps: List[PipelineStep]) -> None:
        if not steps:
            raise ValueError("Pipeline must contain at least one step.")
        self.steps = steps

    # ------------------------------------------------------------------ #

    def run(self, data: Any, ctx: FrozenContext) -> Any:
        """
        Execute the pipeline in order.

        Args:
            data: Raw data from a DataSource.
            ctx:  Immutable execution context.

        Returns:
            Any: Output from the last step in the pipeline.
        """
        provenance = []
        for i, step in enumerate(self.steps):
            step_hash = step.step_hash
            input_hash = compute_hash(data)
            if step.cacheable:
                try:
                    data = load_cache(step_hash, input_hash)
                    cache_hit = True
                except (FileNotFoundError, IOError):
                    try:
                        data = step(data, ctx)
                    except Exception as exc:
                        raise PipelineExecutionError(
                            step.__class__.__name__, exc
                        ) from exc
                    store_cache(step_hash, input_hash, data)
                    cache_hit = False
            else:
                try:
                    data = step(data, ctx)
                except Exception as exc:
                    raise PipelineExecutionError(step.__class__.__name__, exc) from exc
                cache_hit = False
            provenance.append(
                {
                    "step": step.__class__.__name__,
                    "params": step.params,
                    "step_hash": step_hash,
                    "input_hash": input_hash,
                    "output_hash": compute_hash(data),
                    "cache_hit": cache_hit,
                }
            )

            if cache_hit and i == len(self.steps) - 1 and isinstance(data, Mapping):
                for key, value in data.items():
                    ctx.metrics.add(key, value)

        self._provenance = tuple(MappingProxyType(p) for p in provenance)

        return data

    # ------------------------------------------------------------------ #

    def signature(self) -> str:
        """Hash‐friendly signature for caching/provenance."""
        parts = [step.__class__.__name__ + repr(step.params) for step in self.steps]
        return "|".join(parts)

    # ------------------------------------------------------------------ #
    def get_provenance(self) -> List[Mapping[str, Any]]:
        """Return immutable provenance from the last run."""

        return list(getattr(self, "_provenance", ()))
