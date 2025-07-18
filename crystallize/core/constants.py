"""Common string constants used across the framework."""

METADATA_FILENAME = "metadata.json"
"""Default file name for experiment metadata."""

BASELINE_CONDITION = "baseline"
"""Name used to identify the baseline condition."""

REPLICATE_KEY = "replicate"
"""Context key for the current replicate index."""

CONDITION_KEY = "condition"
"""Context key for the current treatment condition."""

SEED_USED_KEY = "seed_used"
"""Context key storing the random seed applied to a run."""

__all__ = [
    "METADATA_FILENAME",
    "BASELINE_CONDITION",
    "REPLICATE_KEY",
    "CONDITION_KEY",
    "SEED_USED_KEY",
]
