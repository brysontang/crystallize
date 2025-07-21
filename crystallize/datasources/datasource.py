from abc import ABC, abstractmethod
from typing import Any

from crystallize.utils.context import FrozenContext


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


class MultiArtifactDataSource(DataSource):
    """Aggregate multiple artifact datasources into one."""

    def __init__(self, **kwargs: DataSource) -> None:
        if not kwargs:
            raise ValueError("At least one datasource must be provided")
        self._sources = kwargs
        first = next(iter(kwargs.values()))
        self._replicates = getattr(first, "replicates", None)
        self.required_outputs = []
        for src in kwargs.values():
            self.required_outputs.extend(getattr(src, "required_outputs", []))

    def fetch(self, ctx: FrozenContext) -> dict[str, Any]:
        return {name: src.fetch(ctx) for name, src in self._sources.items()}

    @property
    def replicates(self) -> int | None:
        return self._replicates
