from __future__ import annotations

from abc import ABC
from dataclasses import dataclass
import importlib
from typing import Any, Callable, Optional, TYPE_CHECKING, List

if TYPE_CHECKING:
    from crystallize.core.experiment import Experiment
    from crystallize.core.context import FrozenContext
    from crystallize.core.pipeline_step import PipelineStep
    from crystallize.core.result import Result


def default_seed_function(seed: int) -> None:
    """Set deterministic seeds for common libraries if available."""
    try:
        random_mod = importlib.import_module("random")
        random_mod.seed(seed)
    except ModuleNotFoundError:  # pragma: no cover - stdlib always there in tests
        pass


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

    def run_experiment_loop(
        self,
        experiment: "Experiment",
        replicate_fn: Callable[[int], Any],
    ) -> List[Any]:
        """Run replicates and return results or ``NotImplemented``."""
        return NotImplemented


@dataclass
class SeedPlugin(BasePlugin):
    """Plugin handling deterministic seeding."""

    seed: Optional[int] = None
    auto_seed: bool = True
    seed_fn: Optional[Callable[[int], None]] = None

    def init_hook(self, experiment: Experiment) -> None:  # pragma: no cover - simple
        pass

    def before_replicate(self, experiment: Experiment, ctx: FrozenContext) -> None:
        if not self.auto_seed:
            return
        local_seed = hash((self.seed or 0) + ctx.get("replicate", 0))
        seed_fn = self.seed_fn or default_seed_function
        seed_fn(local_seed)
        ctx.add("seed_used", local_seed)


@dataclass
class LoggingPlugin(BasePlugin):
    """Plugin configuring logging verbosity and output."""

    verbose: bool = False
    log_level: str = "INFO"

    def init_hook(self, experiment: Experiment) -> None:  # pragma: no cover - simple
        pass

    def before_run(self, experiment: Experiment) -> None:
        import logging
        import time

        logging.basicConfig(level=getattr(logging, self.log_level.upper(), logging.INFO))
        logger = logging.getLogger("crystallize")
        seed_plugin = experiment.get_plugin(SeedPlugin)
        seed_val = seed_plugin.seed if seed_plugin else None
        logger.info(
            "Experiment: %d replicates, %d treatments, %d hypotheses (seed=%s)",
            experiment.replicates,
            len(experiment.treatments),
            len(experiment.hypotheses),
            seed_val,
        )
        if seed_plugin and seed_plugin.auto_seed and seed_plugin.seed_fn is None:
            logger.warning("No seed_fn provided—randomness may not be reproducible")
        experiment._start_time = time.perf_counter()

    def after_step(
        self,
        experiment: Experiment,
        step: PipelineStep,
        data: Any,
        ctx: FrozenContext,
    ) -> None:
        if not self.verbose:
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
