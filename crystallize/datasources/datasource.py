from abc import ABC, abstractmethod
from typing import Any

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - for type hints only
    from crystallize.utils.context import FrozenContext
    from .artifacts import Artifact


class DataSource(ABC):
    """Abstract provider of input data for an experiment."""

    @abstractmethod
    def fetch(self, ctx: "FrozenContext") -> Any:
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


class ExperimentInput(DataSource):
    """Load multiple named artifacts for an experiment."""

    def __init__(self, **inputs: "Artifact") -> None:
        if not inputs:
            raise ValueError("At least one input must be provided")
        self._inputs = inputs
        first = next(iter(inputs.values()))
        self._replicates = getattr(first, "replicates", None)
        self.required_outputs = list(inputs.values())

    def fetch(self, ctx: "FrozenContext") -> dict[str, Any]:
        return {name: art.fetch(ctx) for name, art in self._inputs.items()}

    @property
    def replicates(self) -> int | None:
        return self._replicates


# Backwards compatibility
MultiArtifactDataSource = ExperimentInput
