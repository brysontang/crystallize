"""Verifiers to validate bounded synthesis outputs."""

from __future__ import annotations

from typing import Any, Dict, Mapping, Sequence

from crystallize import verifier


@verifier
def metamorphic(
    baseline_samples: Mapping[str, Sequence[Any]],
    treatment_samples: Mapping[str, Sequence[Any]],
    *,
    tolerance: float = 1e-6,
) -> Dict[str, Any]:
    keys = [key for key in treatment_samples if key.endswith("_pass")]
    passes = {key: all(bool(value) for value in treatment_samples[key]) for key in keys}
    ok = all(passes.values()) if passes else True
    return {"metamorphic_ok": ok, **passes}


@verifier
def meets_claim(
    baseline_samples: Mapping[str, Sequence[Any]],
    treatment_samples: Mapping[str, Sequence[Any]],
    *,
    min_pct: float = 5.0,
) -> Dict[str, Any]:
    baseline_values = list(baseline_samples.get("rmse", ()))
    treatment_values = list(treatment_samples.get("rmse", ()))
    if not baseline_values:
        return {"pct_improvement": 0.0, "meets_claim": False, "p_value": 1.0}
    baseline_mean = sum(baseline_values) / len(baseline_values)
    treatment_mean = (
        sum(treatment_values) / len(treatment_values)
        if treatment_values
        else baseline_mean
    )
    improvement = 100.0 * (baseline_mean - treatment_mean) / baseline_mean
    p_value = max(0.0, 1.0 - min(max(improvement, 0.0) / 100.0, 1.0))
    return {
        "pct_improvement": improvement,
        "meets_claim": improvement >= min_pct,
        "p_value": p_value,
    }
