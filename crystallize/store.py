"""Filesystem storage for Crystallize.

Manages the .crystallize/ directory structure with atomic writes and ledger tracking.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

# Default storage root
DEFAULT_ROOT = ".crystallize"


class Store:
    """Filesystem storage for experiment artifacts.

    Directory structure:
        .crystallize/
        ├── runs/           # Run manifests (explore and confirm)
        ├── prereg/         # Pre-registration artifacts
        └── ledger/         # Replicate index tracking per lineage/config
    """

    def __init__(self, root: Optional[str] = None):
        """Initialize the store.

        Parameters
        ----------
        root : str, optional
            Root directory for storage. Defaults to ".crystallize"
        """
        self.root = Path(root or DEFAULT_ROOT)
        self._ensure_structure()

    def _ensure_structure(self) -> None:
        """Create directory structure if it doesn't exist."""
        for subdir in ["runs", "prereg", "ledger"]:
            (self.root / subdir).mkdir(parents=True, exist_ok=True)

    def _atomic_write(self, path: Path, data: str) -> None:
        """Write data atomically using temp file + fsync + rename.

        Parameters
        ----------
        path : Path
            Target file path
        data : str
            Content to write
        """
        path.parent.mkdir(parents=True, exist_ok=True)

        # Write to temp file in same directory (for atomic rename)
        fd, temp_path = tempfile.mkstemp(
            dir=path.parent,
            prefix=".tmp_",
            suffix=".json",
        )
        try:
            with os.fdopen(fd, "w") as f:
                f.write(data)
                f.flush()
                os.fsync(f.fileno())
            os.rename(temp_path, path)
        except Exception:
            # Clean up temp file on failure
            try:
                os.unlink(temp_path)
            except OSError:
                pass
            raise

    def _ledger_path(self, lineage_id: str, config_fp: str) -> Path:
        """Get path to ledger file for a lineage/config pair."""
        return self.root / "ledger" / f"{lineage_id}_{config_fp}.json"

    def read_ledger(self, lineage_id: str, config_fp: str) -> int:
        """Read the next available replicate index.

        Parameters
        ----------
        lineage_id : str
            Lineage ID
        config_fp : str
            Config fingerprint

        Returns
        -------
        int
            Next available index (0 if ledger doesn't exist)
        """
        path = self._ledger_path(lineage_id, config_fp)
        if not path.exists():
            return 0
        try:
            with open(path) as f:
                data = json.load(f)
                return data.get("next_index", 0)
        except (json.JSONDecodeError, OSError):
            return 0

    def update_ledger(self, lineage_id: str, config_fp: str, new_index: int) -> None:
        """Update the next available replicate index.

        Parameters
        ----------
        lineage_id : str
            Lineage ID
        config_fp : str
            Config fingerprint
        new_index : int
            New next index value
        """
        path = self._ledger_path(lineage_id, config_fp)
        data = {"lineage_id": lineage_id, "config_fingerprint": config_fp, "next_index": new_index}
        self._atomic_write(path, json.dumps(data, indent=2))

    def allocate_replicates(
        self, lineage_id: str, config_fp: str, count: int
    ) -> tuple[int, int]:
        """Allocate a range of fresh replicate indices.

        Parameters
        ----------
        lineage_id : str
            Lineage ID
        config_fp : str
            Config fingerprint
        count : int
            Number of replicates to allocate

        Returns
        -------
        tuple[int, int]
            (start_index, end_index) - inclusive range
        """
        start = self.read_ledger(lineage_id, config_fp)
        end = start + count - 1
        self.update_ledger(lineage_id, config_fp, start + count)
        return start, end

    def write_prereg(self, run_id: str, prereg_data: Dict[str, Any]) -> Path:
        """Write pre-registration artifact.

        Parameters
        ----------
        run_id : str
            Run ID (should be a confirm run)
        prereg_data : dict
            Pre-registration data including hypothesis, config fingerprints, etc.

        Returns
        -------
        Path
            Path to the written file
        """
        path = self.root / "prereg" / f"{run_id}.json"
        self._atomic_write(path, json.dumps(prereg_data, indent=2, default=str))
        return path

    def write_run_manifest(self, run_id: str, manifest: Dict[str, Any]) -> Path:
        """Write run manifest.

        Parameters
        ----------
        run_id : str
            Run ID
        manifest : dict
            Run manifest data

        Returns
        -------
        Path
            Path to the written file
        """
        path = self.root / "runs" / f"{run_id}.json"
        self._atomic_write(path, json.dumps(manifest, indent=2, default=str))
        return path

    def read_run_manifest(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Read a run manifest.

        Parameters
        ----------
        run_id : str
            Run ID

        Returns
        -------
        dict or None
            Manifest data, or None if not found
        """
        path = self.root / "runs" / f"{run_id}.json"
        if not path.exists():
            return None
        try:
            with open(path) as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return None

    def read_prereg(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Read a pre-registration artifact.

        Parameters
        ----------
        run_id : str
            Run ID

        Returns
        -------
        dict or None
            Pre-registration data, or None if not found
        """
        path = self.root / "prereg" / f"{run_id}.json"
        if not path.exists():
            return None
        try:
            with open(path) as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return None

    @property
    def runs_dir(self) -> Path:
        """Get the runs directory path."""
        return self.root / "runs"

    @property
    def prereg_dir(self) -> Path:
        """Get the prereg directory path."""
        return self.root / "prereg"

    @property
    def ledger_dir(self) -> Path:
        """Get the ledger directory path."""
        return self.root / "ledger"


# Global store instance (created on first use)
_store: Optional[Store] = None


def get_store(root: Optional[str] = None) -> Store:
    """Get the global store instance.

    Parameters
    ----------
    root : str, optional
        Root directory. Only used on first call.

    Returns
    -------
    Store
        The global store instance
    """
    global _store
    if _store is None:
        _store = Store(root)
    return _store


def reset_store() -> None:
    """Reset the global store instance (for testing)."""
    global _store
    _store = None
