"""Statistical tests for Crystallize.

Provides permutation tests and bootstrap confidence intervals.
"""

from __future__ import annotations

import random
from typing import List, Literal, Optional, Tuple


def permutation_test(
    a: List[float],
    b: List[float],
    operator: Literal[">", "<", ">=", "<="],
    n_permutations: int = 5000,
    seed: Optional[int] = None,
) -> float:
    """Compute one-sided permutation test p-value.

    Tests whether the observed difference in means is significant.

    Parameters
    ----------
    a : list
        First sample (left side of hypothesis)
    b : list
        Second sample (right side of hypothesis)
    operator : str
        Comparison operator: ">", "<", ">=", or "<="
    n_permutations : int
        Number of permutations for the test
    seed : int, optional
        Random seed for reproducibility

    Returns
    -------
    float
        p-value (probability of seeing this extreme a difference by chance)
    """
    if not a or not b:
        return float("nan")

    if seed is not None:
        random.seed(seed)

    # Observed effect
    observed_diff = sum(a) / len(a) - sum(b) / len(b)

    # Pool all observations
    pooled = a + b
    n_a = len(a)

    # Count how many permutations are as or more extreme
    extreme_count = 0

    for _ in range(n_permutations):
        # Shuffle and split
        random.shuffle(pooled)
        perm_a = pooled[:n_a]
        perm_b = pooled[n_a:]

        perm_diff = sum(perm_a) / len(perm_a) - sum(perm_b) / len(perm_b)

        # Check if permutation is as extreme as observed
        if operator in (">", ">="):
            if perm_diff >= observed_diff:
                extreme_count += 1
        else:  # "<", "<="
            if perm_diff <= observed_diff:
                extreme_count += 1

    return extreme_count / n_permutations


def bootstrap_ci(
    a: List[float],
    b: List[float],
    n_resamples: int = 2000,
    alpha: float = 0.05,
    seed: Optional[int] = None,
) -> Tuple[float, float]:
    """Compute bootstrap confidence interval for the difference in means.

    Parameters
    ----------
    a : list
        First sample
    b : list
        Second sample
    n_resamples : int
        Number of bootstrap resamples
    alpha : float
        Significance level (default 0.05 for 95% CI)
    seed : int, optional
        Random seed for reproducibility

    Returns
    -------
    tuple
        (lower_bound, upper_bound) of confidence interval
    """
    if not a or not b:
        return (float("nan"), float("nan"))

    if seed is not None:
        random.seed(seed)

    diffs = []

    for _ in range(n_resamples):
        # Resample with replacement
        resample_a = random.choices(a, k=len(a))
        resample_b = random.choices(b, k=len(b))

        diff = sum(resample_a) / len(resample_a) - sum(resample_b) / len(resample_b)
        diffs.append(diff)

    # Sort and find percentiles
    diffs.sort()
    lower_idx = int(n_resamples * (alpha / 2))
    upper_idx = int(n_resamples * (1 - alpha / 2))

    return (diffs[lower_idx], diffs[upper_idx])


def effect_size(a: List[float], b: List[float]) -> float:
    """Compute effect size (difference in means).

    Parameters
    ----------
    a : list
        First sample
    b : list
        Second sample

    Returns
    -------
    float
        Difference: mean(a) - mean(b)
    """
    if not a or not b:
        return float("nan")
    return sum(a) / len(a) - sum(b) / len(b)


def cohens_d(a: List[float], b: List[float]) -> float:
    """Compute Cohen's d effect size.

    Parameters
    ----------
    a : list
        First sample
    b : list
        Second sample

    Returns
    -------
    float
        Cohen's d (standardized effect size)
    """
    if not a or not b:
        return float("nan")

    mean_a = sum(a) / len(a)
    mean_b = sum(b) / len(b)

    # Pooled standard deviation
    var_a = sum((x - mean_a) ** 2 for x in a) / len(a)
    var_b = sum((x - mean_b) ** 2 for x in b) / len(b)
    pooled_std = ((var_a + var_b) / 2) ** 0.5

    if pooled_std == 0:
        return float("inf") if mean_a != mean_b else 0.0

    return (mean_a - mean_b) / pooled_std


def check_hypothesis(
    left_vals: List[float],
    right_vals: List[float],
    operator: Literal[">", "<", ">=", "<="],
    alpha: float = 0.05,
    n_permutations: int = 5000,
    n_bootstrap: int = 2000,
    seed: Optional[int] = None,
) -> Tuple[bool, float, float, Tuple[float, float]]:
    """Check a hypothesis and return statistics.

    Parameters
    ----------
    left_vals : list
        Values for left side of hypothesis
    right_vals : list
        Values for right side of hypothesis
    operator : str
        Comparison operator
    alpha : float
        Significance level
    n_permutations : int
        Number of permutations for p-value
    n_bootstrap : int
        Number of bootstrap samples for CI
    seed : int, optional
        Random seed

    Returns
    -------
    tuple
        (supported, effect_size, p_value, ci)
    """
    if not left_vals or not right_vals:
        return (False, float("nan"), float("nan"), (float("nan"), float("nan")))

    eff = effect_size(left_vals, right_vals)
    p_val = permutation_test(left_vals, right_vals, operator, n_permutations, seed)
    ci = bootstrap_ci(left_vals, right_vals, n_bootstrap, alpha, seed)

    # Determine if hypothesis is supported
    left_mean = sum(left_vals) / len(left_vals)
    right_mean = sum(right_vals) / len(right_vals)

    direction_ok = False
    if operator == ">":
        direction_ok = left_mean > right_mean
    elif operator == "<":
        direction_ok = left_mean < right_mean
    elif operator == ">=":
        direction_ok = left_mean >= right_mean
    elif operator == "<=":
        direction_ok = left_mean <= right_mean

    supported = direction_ok and p_val < alpha

    return (supported, eff, p_val, ci)
