from __future__ import annotations

from abc import ABC
from dataclasses import dataclass
from typing import Any, Callable, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from crystallize.core.experiment import Experiment
    from crystallize.core.context import FrozenContext
    from crystallize.core.pipeline_step import PipelineStep
    from crystallize.core.result import Result


class BasePlugin(ABC):
    """Abstract base class for creating plugins that hook into the Experiment lifecycle."""

    def init_hook(self, experiment: Experiment) -> None:
        """Called during ``Experiment.__init__`` to configure the experiment instance."""
        pass

    def before_run(self, experiment: Experiment) -> None:
        """Called at the beginning of ``Experiment.run()``, before any replicates start."""
        pass

    def before_replicate(self, experiment: Experiment, ctx: FrozenContext) -> None:
        """Called before each replicate's pipeline is executed."""
        pass

    def after_step(
        self,
        experiment: Experiment,
        step: PipelineStep,
        data: Any,
        ctx: FrozenContext,
    ) -> None:
        """Called after each ``PipelineStep`` is executed."""
        pass

    def after_run(self, experiment: Experiment, result: Result) -> None:
        """Called at the end of ``Experiment.run()`` after the ``Result`` object is created."""
        pass


@dataclass
class ExecutionPlugin(BasePlugin):
    """Plugin controlling parallel execution settings."""

    parallel: bool = False
    max_workers: Optional[int] = None
    executor_type: str = "thread"

    def init_hook(self, experiment: Experiment) -> None:  # pragma: no cover - simple
        if self.executor_type not in experiment.VALID_EXECUTOR_TYPES:
            raise ValueError(
                f"executor_type must be one of {experiment.VALID_EXECUTOR_TYPES}, got '{self.executor_type}'"
            )
        experiment.parallel = self.parallel
        experiment.max_workers = self.max_workers
        experiment.executor_type = self.executor_type


@dataclass
class SeedPlugin(BasePlugin):
    """Plugin handling deterministic seeding."""

    seed: Optional[int] = None
    auto_seed: bool = True
    seed_fn: Optional[Callable[[int], None]] = None

    def init_hook(self, experiment: Experiment) -> None:  # pragma: no cover - simple
        experiment.seed = self.seed
        experiment.auto_seed = self.auto_seed
        if self.seed_fn is not None:
            experiment.seed_fn = self.seed_fn

    def before_replicate(self, experiment: Experiment, ctx: FrozenContext) -> None:
        if not experiment.auto_seed:
            return
        local_seed = hash((experiment.seed or 0) + ctx.get("replicate", 0))
        if experiment.seed_fn is not None:
            experiment.seed_fn(local_seed)
        ctx.add("seed_used", local_seed)


@dataclass
class LoggingPlugin(BasePlugin):
    """Plugin configuring logging verbosity and output."""

    verbose: bool = False
    log_level: str = "INFO"

    def init_hook(self, experiment: Experiment) -> None:  # pragma: no cover - simple
        experiment.verbose = self.verbose
        experiment.log_level = self.log_level

    def before_run(self, experiment: Experiment) -> None:
        import logging
        import time

        logging.basicConfig(
            level=getattr(logging, experiment.log_level.upper(), logging.INFO)
        )
        logger = logging.getLogger("crystallize")
        logger.info(
            "Experiment: %d replicates, %d treatments, %d hypotheses (seed=%s, parallel=%s/%s workers)",
            experiment.replicates,
            len(experiment.treatments),
            len(experiment.hypotheses),
            experiment.seed,
            experiment.executor_type,
            experiment.max_workers or "auto",
        )
        if experiment.auto_seed and experiment.seed_fn is None:
            logger.warning("No seed_fn provided—randomness may not be reproducible")
        experiment._start_time = time.perf_counter()

    def after_step(
        self,
        experiment: Experiment,
        step: PipelineStep,
        data: Any,
        ctx: FrozenContext,
    ) -> None:
        if not experiment.verbose:
            return
        import logging

        logger = logging.getLogger("crystallize")
        logger.info(
            "Rep %s/%s %s finished step %s",
            ctx.get("replicate"),
            experiment.replicates,
            ctx.get("condition"),
            step.__class__.__name__,
        )

    def after_run(self, experiment: Experiment, result: Result) -> None:
        import logging
        import time

        logger = logging.getLogger("crystallize")
        duration = time.perf_counter() - getattr(experiment, "_start_time", 0)
        bests = [
            f"{h.name}: '{h.ranking.get('best')}'" for h in result.metrics.hypotheses if h.ranking.get("best") is not None
        ]
        best_summary = "; Best " + ", ".join(bests) if bests else ""
        logger.info(
            "Completed in %.1fs%s; %d errors",
            duration,
            best_summary,
            len(result.errors),
        )
