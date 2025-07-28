from abc import ABC, abstractmethod
from typing import Any

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - for type hints only
    from crystallize.utils.context import FrozenContext


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
    """Bundles multiple named datasources for an experiment.

    This can include both raw datasources (like functions decorated with
    @data_source) and Artifacts that link to the output of other experiments.
    """

    def __init__(self, **inputs: "DataSource") -> None:
        """
        Args:
            **inputs: A keyword mapping of names to DataSource objects.
        """
        if not inputs:
            raise ValueError("At least one input must be provided")

        self._inputs = inputs

        from .artifacts import Artifact  # Local import to avoid circular dependencies

        self.required_outputs: list[Artifact] = [
            v for v in inputs.values() if isinstance(v, Artifact)
        ]

        self._replicates: int | None = None
        if self.required_outputs:
            first_artifact = self.required_outputs[0]
            self._replicates = getattr(first_artifact, "replicates", None)

    def fetch(self, ctx: "FrozenContext") -> dict[str, Any]:
        """Fetches data from all contained datasources."""
        return {name: ds.fetch(ctx) for name, ds in self._inputs.items()}

    @property
    def replicates(self) -> int | None:
        """The number of replicates, inferred from the first Artifact input."""
        return self._replicates


# Backwards compatibility
MultiArtifactDataSource = ExperimentInput
