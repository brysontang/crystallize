from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Callable, List, Optional, TYPE_CHECKING
import dill

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
            raise ContextMutationError(f"Artifact '{name}' already written in this run")
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


def default_loader(p: Path) -> Any:
    return p.read_bytes()


def default_writer(data: Any) -> bytes:
    if isinstance(data, bytes):
        return data
    if isinstance(data, str):
        return data.encode()
    raise TypeError("default_writer expects bytes or str")


class _PickleableCallable:
    """Wrapper enabling pickling of arbitrary callables."""

    def __init__(self, fn: Callable[..., Any]) -> None:
        self.fn = fn

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return self.fn(*args, **kwargs)

    def __getstate__(self) -> bytes:
        return dill.dumps(self.fn)

    def __setstate__(self, state: bytes) -> None:
        self.fn = dill.loads(state)


class Artifact(DataSource):
    """Declarative handle for reading and writing artifacts."""

    def __init__(
        self,
        name: str,
        loader: Callable[[Path], Any] | None = None,
        writer: Callable[[Any], bytes] | None = None,
    ) -> None:
        self.name = name
        self.loader = _PickleableCallable(loader or default_loader)
        self.writer = _PickleableCallable(writer or default_writer)
        self._ctx: Optional["FrozenContext"] = None
        self._producer: Optional["Experiment"] = None
        self._manifest: Optional[dict[str, str]] = None
        self.replicates: int | None = None

    def __getstate__(self):
        """
        Customize the pickling process to exclude unpicklable attributes
        like weak references to the producer experiment.
        """
        # Copy the object's state dictionary
        state = self.__dict__.copy()

        # Remove the unpicklable weak reference before serialization
        if "_producer" in state:
            del state["_producer"]

        return state

    def _clone_with_context(self, ctx: "FrozenContext") -> "Artifact":
        clone = Artifact(self.name, loader=self.loader, writer=self.writer)
        clone._ctx = ctx
        clone._producer = self._producer
        clone._manifest = self._manifest
        clone.replicates = self.replicates
        return clone

    def write(self, data: Any) -> None:
        if self._ctx is None:
            raise RuntimeError("Artifact not bound to context")
        if self.writer is None:
            raise RuntimeError("Artifact not bound to a writer")
        data = self.writer(data)
        self._ctx.artifacts.add(self.name, data)

    def _base_dir(self) -> Path:
        if self._producer is None:
            raise RuntimeError("Artifact not attached to an Experiment")
        plugin = self._producer.get_plugin(ArtifactPlugin)
        if plugin is None:
            raise RuntimeError("ArtifactPlugin required to load artifacts")
        # This logic is now self-sufficient and doesn't rely on plugin.version
        exp_dir = Path(plugin.root_dir) / (self._producer.name or self._producer.id)

        # Find the latest version by looking at the directories on disk
        if plugin.versioned:
            versions = [
                int(p.name[1:])
                for p in exp_dir.glob("v*")
                if p.name.startswith("v") and p.name[1:].isdigit()
            ]
            latest_version = max(versions, default=0)
        else:
            latest_version = 0

        return exp_dir / f"v{latest_version}"

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

        consumer_rep = ctx.get("replicate", 0)
        rep_to_load = consumer_rep

        if self.replicates and self.replicates > 0:
            rep_to_load = consumer_rep % self.replicates

        cond = ctx.get("condition")
        path = base / f"replicate_{rep_to_load}" / cond / step_name / self.name

        if not path.exists() and cond != BASELINE_CONDITION:
            ctx_logger = getattr(ctx, "logger", None)
            if ctx_logger:
                ctx_logger.warning(
                    "Artifact %s for condition '%s' not found at %s; falling back to '%s'.",
                    self.name,
                    cond,
                    str(path),
                    BASELINE_CONDITION,
                )
            path = (
                base
                / f"replicate_{rep_to_load}"
                / BASELINE_CONDITION
                / step_name
                / self.name
            )
        if not path.exists():
            raise FileNotFoundError(f"Artifact {path} not found")
        return self.loader(path)
