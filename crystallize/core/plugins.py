from __future__ import annotations

import importlib
import os
from abc import ABC
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, List, Optional

if TYPE_CHECKING:
    from crystallize.core.context import FrozenContext
    from crystallize.core.experiment import Experiment
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
    """Interface for extending the :class:`~crystallize.core.experiment.Experiment` lifecycle.

    Subclasses can override any of the hook methods to observe or modify the
    behaviour of an experiment.  Hooks are called in a well-defined order during
    :meth:`Experiment.run` allowing plugins to coordinate tasks such as
    seeding, logging, artifact storage or custom execution strategies.
    """

    def init_hook(self, experiment: Experiment) -> None:
        """Configure the experiment instance during initialization."""
        pass

    def before_run(self, experiment: Experiment) -> None:
        """Execute logic before :meth:`Experiment.run` begins."""
        pass

    def before_replicate(self, experiment: Experiment, ctx: FrozenContext) -> None:
        """Run prior to each pipeline execution for a replicate."""
        pass

    def after_step(
        self,
        experiment: Experiment,
        step: PipelineStep,
        data: Any,
        ctx: FrozenContext,
    ) -> None:
        """Observe results after every :class:`PipelineStep` execution."""
        pass

    def after_run(self, experiment: Experiment, result: Result) -> None:
        """Execute cleanup or reporting after :meth:`Experiment.run` completes."""
        pass

    def run_experiment_loop(
        self,
        experiment: "Experiment",
        replicate_fn: Callable[[int], Any],
    ) -> List[Any]:
        """Run all replicates and return their results.

        Returning ``NotImplemented`` signals that the plugin does not provide a
        custom execution strategy and the default should be used instead.
        """
        return NotImplemented


@dataclass
class SeedPlugin(BasePlugin):
    """Manage deterministic seeding for all random operations."""

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
    """Configure logging verbosity and experiment progress reporting."""

    verbose: bool = False
    log_level: str = "INFO"

    def init_hook(self, experiment: Experiment) -> None:  # pragma: no cover - simple
        pass

    def before_run(self, experiment: Experiment) -> None:
        import logging
        import time

        logging.basicConfig(
            level=getattr(logging, self.log_level.upper(), logging.INFO)
        )
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
            f"{h.name}: '{h.ranking.get('best')}'"
            for h in result.metrics.hypotheses
            if h.ranking.get("best") is not None
        ]
        best_summary = "; Best " + ", ".join(bests) if bests else ""
        logger.info(
            "Completed in %.1fs%s; %d errors",
            duration,
            best_summary,
            len(result.errors),
        )


@dataclass
class ArtifactPlugin(BasePlugin):
    """Persist artifacts produced during pipeline execution."""

    root_dir: str = "./crystallize_artifacts"
    versioned: bool = False

    def before_run(self, experiment: Experiment) -> None:
        from .cache import compute_hash

        self.experiment_id = compute_hash(experiment.pipeline.signature())
        base = Path(self.root_dir) / self.experiment_id
        base.mkdir(parents=True, exist_ok=True)
        if self.versioned:
            versions = [
                int(p.name[1:])
                for p in base.glob("v*")
                if p.name.startswith("v") and p.name[1:].isdigit()
            ]
            self.version = max(versions, default=-1) + 1
        else:
            self.version = 0

    def after_step(
        self,
        experiment: Experiment,
        step: PipelineStep,
        data: Any,
        ctx: FrozenContext,
    ) -> None:
        """Write any artifacts logged in ``ctx.artifacts`` to disk."""
        if len(ctx.artifacts) == 0:
            return
        rep = ctx.get("replicate", 0)
        condition = ctx.get("condition", "baseline")
        for artifact in ctx.artifacts:
            artifact.step_name = step.__class__.__name__
            dest = (
                Path(self.root_dir)
                / self.experiment_id
                / f"v{self.version}"
                / f"replicate_{rep}"
                / condition
                / artifact.step_name
            )
            os.makedirs(dest, exist_ok=True)
            with open(dest / artifact.name, "wb") as f:
                f.write(artifact.data)
        ctx.artifacts.clear()
