from abc import ABC, abstractmethod
from typing import Any

from crystallize.utils.cache import compute_hash
from crystallize.utils.context import FrozenContext


class PipelineStep(ABC):
    cacheable = False

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

    def setup(self, ctx: FrozenContext) -> None:
        """Optional hook called once before any replicates run."""
        pass

    def teardown(self, ctx: FrozenContext) -> None:
        """Optional hook called once after all replicates finish."""
        pass

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
