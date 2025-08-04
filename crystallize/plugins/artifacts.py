from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from crystallize.utils.constants import BASELINE_CONDITION


def load_metrics(exp_dir: Path, version: int) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    """Load metrics from ``results.json`` files for ``version``.

    Parameters
    ----------
    exp_dir:
        Base directory of the experiment.
    version:
        Version number to load from.
    Returns
    -------
    Tuple of baseline metrics and a mapping of treatment name to metrics.
    """
    base = exp_dir / f"v{version}"
    baseline: Dict[str, Any] = {}
    baseline_file = base / BASELINE_CONDITION / "results.json"
    if baseline_file.exists():
        with open(baseline_file) as f:
            baseline = json.load(f).get("metrics", {})

    treatments: Dict[str, Dict[str, Any]] = {}
    if base.exists():
        for t_dir in base.iterdir():
            if not t_dir.is_dir() or t_dir.name == BASELINE_CONDITION:
                continue
            res = t_dir / "results.json"
            if not res.exists():
                continue
            with open(res) as f:
                treatments[t_dir.name] = json.load(f).get("metrics", {})
    return baseline, treatments
