"""Public convenience API."""

from __future__ import annotations

from .core import (
    data_source,
    hypothesis,
    pipeline,
    pipeline_step,
    inject_from_ctx,
    treatment,
    verifier,
)
from .core.execution import ParallelExecution, SerialExecution
from .core.plugins import ArtifactPlugin, BasePlugin, LoggingPlugin, SeedPlugin

__all__ = [
    "pipeline_step",
    "inject_from_ctx",
    "treatment",
    "hypothesis",
    "data_source",
    "verifier",
    "pipeline",
    "BasePlugin",
    "SerialExecution",
    "ParallelExecution",
    "SeedPlugin",
    "LoggingPlugin",
    "ArtifactPlugin",
]
