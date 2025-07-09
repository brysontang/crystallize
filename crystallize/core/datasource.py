from abc import ABC, abstractmethod
from typing import Any
from crystallize.core.context import FrozenContext

class DataSource(ABC):
    @abstractmethod
    def fetch(self, ctx: FrozenContext) -> Any:
        """
        Fetch or generate data.

        Args:
            ctx (FrozenContext): Immutable execution context.

        Returns:
            Any: The data produced by this DataSource.
        """
        raise NotImplementedError()
