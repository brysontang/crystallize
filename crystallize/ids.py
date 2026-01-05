"""ID generation for Crystallize.

Generates deterministic and random IDs for runs, lineages, configs, and replicates.
"""

from __future__ import annotations

import hashlib
import json
import secrets
from typing import Any, Dict, Literal


def generate_run_id(run_type: Literal["explore", "confirm"] = "explore") -> str:
    """Generate a unique run ID.

    Parameters
    ----------
    run_type : str
        Either "explore" or "confirm"

    Returns
    -------
    str
        ID like "exp_a1b2c3d4" or "conf_e5f6g7h8"
    """
    prefix = "exp" if run_type == "explore" else "conf"
    suffix = secrets.token_hex(4)
    return f"{prefix}_{suffix}"


def generate_lineage_id() -> str:
    """Generate a unique lineage ID.

    A lineage groups related explore and confirm runs together.

    Returns
    -------
    str
        ID like "lin_a1b2c3d4e5f6"
    """
    return f"lin_{secrets.token_hex(6)}"


def config_fingerprint(config: Dict[str, Any]) -> str:
    """Generate a deterministic fingerprint for a config dict.

    Uses canonical JSON (sorted keys, no whitespace) then SHA256.

    Parameters
    ----------
    config : dict
        Configuration dictionary

    Returns
    -------
    str
        SHA256 hash (first 16 chars)
    """
    canonical = json.dumps(config, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()[:16]


def replicate_id(lineage_id: str, config_fp: str, index: int) -> str:
    """Generate a deterministic replicate ID.

    Parameters
    ----------
    lineage_id : str
        The lineage this replicate belongs to
    config_fp : str
        Config fingerprint
    index : int
        Replicate index (0-based)

    Returns
    -------
    str
        ID like "rep_lin_abc123_cfg_def456_0042"
    """
    return f"rep_{lineage_id}_{config_fp[:8]}_{index:04d}"


def manifest_hash(manifest: Dict[str, Any]) -> str:
    """Generate a SHA256 hash of a manifest for integrity verification.

    Parameters
    ----------
    manifest : dict
        The manifest dictionary to hash

    Returns
    -------
    str
        Full SHA256 hash
    """
    canonical = json.dumps(manifest, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode()).hexdigest()
