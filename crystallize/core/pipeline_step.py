from abc import ABC, abstractmethod
from typing import Any

from crystallize.core.cache import compute_hash
from crystallize.core.context import FrozenContext


class PipelineStep(ABC):
    cacheable = True

    @abstractmethod
    def __call__(self, data: Any, ctx: FrozenContext) -> Any:
        """
        Execute the pipeline step.

        Args:
            data (Any): Input data to the step.
            ctx (FrozenContext): Immutable execution context.

        Returns:
            Any: Transformed or computed data.
        """
        raise NotImplementedError()

    @property
    @abstractmethod
    def params(self) -> dict:
        """
        Parameters of this step for hashing and caching.

        Returns:
            dict: Parameters dictionary.
        """
        raise NotImplementedError()

    # ------------------------------------------------------------------ #
    @property
    def step_hash(self) -> str:
        """Unique hash identifying this step based on its parameters."""

        payload = {"class": self.__class__.__name__, "params": self.params}
        return compute_hash(payload)


def exit_step(step: PipelineStep) -> PipelineStep:
    """Mark a :class:`PipelineStep` instance as an exit point."""

    setattr(step, "is_exit_step", True)
    return step
