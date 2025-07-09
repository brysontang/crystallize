from abc import ABC, abstractmethod
from typing import Any
from crystallize.core.context import FrozenContext

class PipelineStep(ABC):
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
