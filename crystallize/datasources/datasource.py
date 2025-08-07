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
            replicates_map: dict[str, int] = {
                name: art.replicates
                for name, art in inputs.items()
                if isinstance(art, Artifact) and art.replicates is not None
            }
            distinct = set(replicates_map.values())
            if len(distinct) > 1:
                mismatches = ", ".join(
                    f"{n}={r}" for n, r in sorted(replicates_map.items())
                )
                raise ValueError(
                    "Conflicting replicates across artifacts: " + mismatches
                )
            if distinct:
                self._replicates = distinct.pop()

    def fetch(self, ctx: "FrozenContext") -> dict[str, Any]:
        """Fetches data from all contained datasources."""
        return {name: ds.fetch(ctx) for name, ds in self._inputs.items()}

    @property
    def replicates(self) -> int | None:
        """The number of replicates, inferred from Artifact inputs."""
        return self._replicates


# Backwards compatibility
MultiArtifactDataSource = ExperimentInput
