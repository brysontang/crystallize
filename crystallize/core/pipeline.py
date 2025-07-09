from typing import List, Any, Mapping
import inspect

from crystallize.core.pipeline_step import PipelineStep
from crystallize.core.context import FrozenContext


class InvalidPipelineOutput(Exception):
    """Raised when the final step does not yield a metrics‐dict."""


class Pipeline:
    """
    Linear sequence of PipelineStep objects.

    Guarantee: the **last** step must return a Mapping[str, Any] that represents
    the _metrics_ produced by the pipeline.  All preceding steps may return any
    intermediate representation.
    """

    def __init__(self, steps: List[PipelineStep]):
        if not steps:
            raise ValueError("Pipeline must contain at least one step.")
        self.steps = steps

    # ------------------------------------------------------------------ #

    def run(self, data: Any, ctx: FrozenContext) -> Mapping[str, Any]:
        """
        Execute the pipeline in order.

        Args:
            data: Raw data from a DataSource.
            ctx:  Immutable execution context.

        Returns:
            Mapping[str, Any]: metrics dict emitted by final step.

        Raises:
            InvalidPipelineOutput: if the last step does not return Mapping.
        """
        for step in self.steps:
            data = step(data, ctx)

        if not isinstance(data, Mapping):
            raise InvalidPipelineOutput(
                f"Last step `{self.steps[-1].__class__.__name__}` returned "
                f"{type(data).__name__}, expected Mapping[str, Any]."
            )
        return data

    # ------------------------------------------------------------------ #

    def signature(self) -> str:
        """Hash‐friendly signature for caching/provenance."""
        parts = [step.__class__.__name__ + repr(step.params) for step in self.steps]
        return "|".join(parts)
