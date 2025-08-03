from __future__ import annotations

from pathlib import Path

import yaml


class ExperimentLoadError(Exception):
    """Raised when an experiment fails to load."""


def format_load_error(path: Path, error: BaseException) -> ExperimentLoadError:
    """Return a user-facing error for an experiment load failure.

    Args:
        path: Path to the experiment's ``config.yaml``.
        error: Original exception raised during loading.
    """
    if isinstance(error, yaml.YAMLError):
        msg = f"Invalid YAML in {path}: {error}"
    elif isinstance(error, FileNotFoundError):
        missing = error.filename or str(error)
        msg = f"File '{missing}' referenced in {path} was not found."
    elif isinstance(error, AttributeError):
        msg = (
            f"{path}: {error}. Verify your configuration references valid modules and attributes."
        )
    elif isinstance(error, KeyError):
        msg = f"Missing required configuration key {error} in {path}."
    else:
        msg = f"{path}: {error}"
    return ExperimentLoadError(msg)
