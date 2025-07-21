from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Callable, List, Optional, TYPE_CHECKING

from crystallize.utils.exceptions import ContextMutationError
from crystallize.utils.constants import (
    METADATA_FILENAME,
    BASELINE_CONDITION,
)
from crystallize.plugins.plugins import ArtifactPlugin
from crystallize.datasources.datasource import DataSource

if TYPE_CHECKING:  # pragma: no cover - for type hints only
    from crystallize.utils.context import FrozenContext
    from crystallize.experiments.experiment import Experiment


@dataclass
class ArtifactRecord:
    """Container representing a file-like artifact produced by a step."""

    name: str
    data: bytes
    step_name: str


class ArtifactLog:
    """Collect artifacts produced during a pipeline step."""

    def __init__(self) -> None:
        self._items: List[ArtifactRecord] = []
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
        self._items.append(ArtifactRecord(name=name, data=data, step_name=""))

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


class Artifact(DataSource):
    """Declarative handle for reading and writing artifacts."""

    def __init__(self, name: str, loader: Callable[[Path], Any] | None = None) -> None:
        self.name = name
        self.loader = loader or (lambda p: p.read_bytes())
        self._ctx: Optional["FrozenContext"] = None
        self._producer: Optional["Experiment"] = None
        self._manifest: Optional[dict[str, str]] = None
        self.replicates: int | None = None

    def _clone_with_context(self, ctx: "FrozenContext") -> "Artifact":
        clone = Artifact(self.name, loader=self.loader)
        clone._ctx = ctx
        clone._producer = self._producer
        clone._manifest = self._manifest
        clone.replicates = self.replicates
        return clone

    def write(self, data: bytes) -> None:
        if self._ctx is None:
            raise RuntimeError("Artifact not bound to context")
        self._ctx.artifacts.add(self.name, data)

    def _base_dir(self) -> Path:
        if self._producer is None:
            raise RuntimeError("Artifact not attached to an Experiment")
        plugin = self._producer.get_plugin(ArtifactPlugin)
        if plugin is None:
            raise RuntimeError("ArtifactPlugin required to load artifacts")
        return Path(plugin.root_dir) / (self._producer.name or self._producer.id) / f"v{plugin.version}"

    def _load_manifest(self) -> None:
        if self._manifest is not None:
            return
        base = self._base_dir()
        path = base / "_manifest.json"
        if path.exists():
            with open(path) as f:
                self._manifest = json.load(f)
        else:
            self._manifest = {}

    def fetch(self, ctx: "FrozenContext") -> Any:
        self._load_manifest()
        base = self._base_dir()
        if self.replicates is None:
            meta_path = base / METADATA_FILENAME
            if meta_path.exists():
                with open(meta_path) as f:
                    meta = json.load(f)
                self.replicates = meta.get("replicates")
        step_name = self._manifest.get(self.name)
        if step_name is None:
            raise FileNotFoundError(f"Manifest missing entry for {self.name}")
        rep = ctx.get("replicate", 0)
        cond = ctx.get("condition", BASELINE_CONDITION)
        path = base / f"replicate_{rep}" / cond / step_name / self.name
        if not path.exists():
            raise FileNotFoundError(f"Artifact {path} not found")
        return self.loader(path)
