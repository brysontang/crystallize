from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class Artifact:
    """Simple container for artifact data."""

    name: str
    data: bytes
    step_name: str


class ArtifactLog:
    """In-memory log of artifacts for the current step."""

    def __init__(self) -> None:
        self._items: List[Artifact] = []

    def add(self, name: str, data: bytes) -> None:
        self._items.append(Artifact(name=name, data=data, step_name=""))

    def clear(self) -> None:
        self._items.clear()

    def __iter__(self):
        return iter(self._items)

    def __len__(self) -> int:
        return len(self._items)
