"""Backward compatibility layer for the CLI."""
from crystallize.cli.app import run
from crystallize.cli.discovery import _import_module, _run_object, discover_objects
from crystallize.cli.utils import (
    _build_experiment_table,
    _write_experiment_summary,
    _write_summary,
)

__all__ = [
    "run",
    "_import_module",
    "_run_object",
    "discover_objects",
    "_build_experiment_table",
    "_write_experiment_summary",
    "_write_summary",
]

if __name__ == "__main__":  # pragma: no cover - manual run
    run()
