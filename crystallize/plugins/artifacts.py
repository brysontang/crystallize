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
