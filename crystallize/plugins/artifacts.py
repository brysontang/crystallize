from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Tuple

from crystallize.utils.constants import BASELINE_CONDITION


def load_metrics(exp_dir: Path, version: int | None = None) -> Tuple[int, dict[str, Any], dict[str, dict[str, Any]]]:
    """Load metrics from ``results.json`` files for ``version``.

    Parameters
    ----------
    exp_dir:
        Base directory of the experiment.
    version:
        Version number to load from. If ``None``, the latest version is used.
    Returns
    -------
    Tuple of the loaded version number, baseline metrics and a mapping of
    treatment name to metrics in stable order.
    """
    if version is None:
        versions = sorted(
            int(p.name[1:])
            for p in exp_dir.glob("v*")
            if p.name.startswith("v") and p.name[1:].isdigit()
        )
        if not versions:
            return -1, {}, {}
        version = max(versions)

    base = exp_dir / f"v{version}"
    baseline: Dict[str, Any] = {}
    baseline_file = base / BASELINE_CONDITION / "results.json"
    if baseline_file.exists():
        with open(baseline_file) as f:
            baseline = json.load(f).get("metrics", {})

    treatments: Dict[str, Dict[str, Any]] = {}
    if base.exists():
        for t_dir in sorted(base.iterdir(), key=lambda p: p.name):
            if not t_dir.is_dir() or t_dir.name == BASELINE_CONDITION:
                continue
            res = t_dir / "results.json"
            if not res.exists():
                continue
            with open(res) as f:
                treatments[t_dir.name] = json.load(f).get("metrics", {})
    return version, baseline, treatments


def load_all_metrics(
    exp_dir: Path, version: int | None = None
) -> Tuple[int, dict[str, Any], dict[str, Tuple[int, dict[str, Any]]]]:
    """Load metrics for all treatments across versions.

    Parameters
    ----------
    exp_dir:
        Base directory of the experiment.
    version:
        Latest version to consider. If ``None`` the newest version on disk is
        used.

    Returns
    -------
    Tuple of the latest version number, baseline metrics from that version and a
    mapping of treatment name to a tuple of ``(version, metrics)`` where
    ``version`` indicates which artifact version the metrics were loaded from.
    """

    versions = sorted(
        int(p.name[1:])
        for p in exp_dir.glob("v*")
        if p.name.startswith("v") and p.name[1:].isdigit()
    )
    if not versions:
        return -1, {}, {}

    latest = max(versions) if version is None else version
    base = exp_dir / f"v{latest}"
    baseline: Dict[str, Any] = {}
    baseline_file = base / BASELINE_CONDITION / "results.json"
    if baseline_file.exists():
        with open(baseline_file) as f:
            baseline = json.load(f).get("metrics", {})

    treatments: Dict[str, Tuple[int, Dict[str, Any]]] = {}
    seen: set[str] = set()
    for ver in sorted((v for v in versions if v <= latest), reverse=True):
        base = exp_dir / f"v{ver}"
        if not base.exists():
            continue
        for t_dir in sorted(base.iterdir(), key=lambda p: p.name):
            name = t_dir.name
            if (
                not t_dir.is_dir()
                or name == BASELINE_CONDITION
                or name in seen
            ):
                continue
            res = t_dir / "results.json"
            if not res.exists():
                continue
            with open(res) as f:
                treatments[name] = (ver, json.load(f).get("metrics", {}))
            seen.add(name)
    return latest, baseline, treatments
