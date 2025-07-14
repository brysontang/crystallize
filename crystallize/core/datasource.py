from abc import ABC, abstractmethod
from typing import Any
from crystallize.core.context import FrozenContext

class DataSource(ABC):
    """Abstract provider of input data for an experiment."""
    @abstractmethod
    def fetch(self, ctx: FrozenContext) -> Any:
        """Return raw data for a single pipeline run.

        Implementations may load data from disk, generate synthetic samples or
        access remote sources.  They should be deterministic with respect to the
        provided context.

        Args:
            ctx: Immutable execution context for the current run.

        Returns:
            The produced data object.
        """
        raise NotImplementedError()
