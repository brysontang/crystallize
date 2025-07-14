from __future__ import annotations

from dataclasses import dataclass
from typing import List


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

    def add(self, name: str, data: bytes) -> None:
        """Append a new artifact to the log.

        Args:
            name: Filename for the artifact.
            data: Raw bytes to be written to disk by ``ArtifactPlugin``.
        """
        self._items.append(Artifact(name=name, data=data, step_name=""))

    def clear(self) -> None:
        """Remove all logged artifacts."""
        self._items.clear()

    def __iter__(self):
        """Iterate over collected artifacts."""
        return iter(self._items)

    def __len__(self) -> int:
        """Return the number of stored artifacts."""
        return len(self._items)
