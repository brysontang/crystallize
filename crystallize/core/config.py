from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional


@dataclass
class ExecutionConfig:
    """Execution-related settings."""

    parallel: bool = False
    max_workers: Optional[int] = None
    executor_type: str = "thread"


@dataclass
class SeedConfig:
    """Random seed configuration."""

    seed: Optional[int] = None
    auto_seed: bool = True
    seed_fn: Optional[Callable[[int], None]] = None


@dataclass
class LoggingConfig:
    """Logging verbosity configuration."""

    verbose: bool = False
    log_level: str = "INFO"
