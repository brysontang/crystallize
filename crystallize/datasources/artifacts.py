from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, TYPE_CHECKING

from crystallize.utils.exceptions import ContextMutationError

if TYPE_CHECKING:  # pragma: no cover - for type hints only
    from crystallize.utils.context import FrozenContext


@dataclass
class Artifact:
    """Container representing a file-like artifact produced by a step."""

    name: str
    data: bytes
    step_name: str


class ArtifactLog:
    """Collect artifacts produced during a pipeline step."""

    def __init__(self) -> None:
        self._items: List[Artifact] = []
        self._names: set[str] = set()

    def add(self, name: str, data: bytes) -> None:
        """Append a new artifact to the log.

        Args:
            name: Filename for the artifact.
            data: Raw bytes to be written to disk by ``ArtifactPlugin``.
        """
        if name in self._names:
            raise ContextMutationError(
                f"Artifact '{name}' already written in this run"
            )
        self._names.add(name)
        self._items.append(Artifact(name=name, data=data, step_name=""))

    def clear(self) -> None:
        """Remove all logged artifacts."""
        self._items.clear()
        self._names.clear()

    def __iter__(self):
        """Iterate over collected artifacts."""
        return iter(self._items)

    def __len__(self) -> int:
        """Return the number of stored artifacts."""
        return len(self._items)


class Output:
    """Declarative handle for a file artifact."""

    def __init__(self, name: str) -> None:
        self.name = name
        self._ctx: Optional["FrozenContext"] = None

    def _clone_with_context(self, ctx: "FrozenContext") -> "Output":
        clone = Output(self.name)
        clone._ctx = ctx
        return clone

    def write(self, data: bytes) -> None:
        if self._ctx is None:
            raise RuntimeError("Output not bound to context")
        self._ctx.artifacts.add(self.name, data)
