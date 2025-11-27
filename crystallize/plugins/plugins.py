from __future__ import annotations

import importlib
import json
import os
from abc import ABC
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, List, Optional, Mapping

from crystallize.utils.constants import (
    REPLICATE_KEY,
    CONDITION_KEY,
    BASELINE_CONDITION,
    METADATA_FILENAME,
    SEED_USED_KEY,
)

if TYPE_CHECKING:
    from crystallize.utils.context import FrozenContext
    from crystallize.experiments.experiment import Experiment
    from crystallize.pipelines.pipeline_step import PipelineStep
    from crystallize.experiments.result import Result


def default_seed_function(seed: int) -> None:
    """Set deterministic seeds for common libraries if available."""
    try:
        random_mod = importlib.import_module("random")
        random_mod.seed(seed)
    except ModuleNotFoundError:  # pragma: no cover - stdlib always there in tests
        pass
    try:
        numpy_mod = importlib.import_module("numpy")
        numpy_mod.random.seed(seed % (2**32 - 1))
    except ModuleNotFoundError:  # pragma: no cover - optional dependency
        pass


class BasePlugin(ABC):
    """Interface for extending the :class:`~crystallize.experiments.experiment.Experiment` lifecycle.

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

    def before_step(self, experiment: Experiment, step: PipelineStep) -> None:
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
        if self.seed is None:
            import random

            self.seed = random.randint(0, 2**32 - 1)

    def before_replicate(self, experiment: Experiment, ctx: FrozenContext) -> None:
        rep = ctx.get(REPLICATE_KEY, 0)
        if self.seed is None:
            import random

            self.seed = random.randint(0, 2**32 - 1)

        if self.auto_seed:
            replicate_seed = (self.seed + rep * 31337) % (2**32)
        else:
            replicate_seed = self.seed

        ctx.add(SEED_USED_KEY, replicate_seed)

        seed_fn = self.seed_fn or default_seed_function
        seed_fn(replicate_seed)


@dataclass
class LoggingPlugin(BasePlugin):
    """Configure experiment logging using the ``crystallize`` logger."""

    verbose: bool = False
    log_level: str = "INFO"

    def init_hook(self, experiment: Experiment) -> None:  # pragma: no cover - simple
        pass

    def before_run(self, experiment: Experiment) -> None:
        import logging
        import time

        logger = logging.getLogger("crystallize")
        level = getattr(logging, self.log_level.upper(), logging.INFO)
        logger.setLevel(level)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
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

    root_dir: str = "./data"
    versioned: bool = False
    artifact_retention: int = 3
    big_file_threshold_mb: int = 10

    def __post_init__(self) -> None:
        self._manifest: dict[str, str] = {}
        self._artifact_paths: dict[str, dict[str, Path]] = {}
        if self.artifact_retention == 3:
            val = os.getenv("CRYSTALLIZE_ARTIFACT_RETENTION")
            if val is not None:
                try:
                    self.artifact_retention = int(val)
                except ValueError:
                    self.artifact_retention = 3
        if self.big_file_threshold_mb == 10:
            val = os.getenv("CRYSTALLIZE_BIG_FILE_THRESHOLD_MB")
            if val is not None:
                try:
                    self.big_file_threshold_mb = int(val)
                except ValueError:
                    self.big_file_threshold_mb = 10

    def before_run(self, experiment: Experiment) -> None:
        self.experiment_id = experiment.name or experiment.id
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
        self._manifest.clear()
        self._artifact_paths.clear()

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
        rep = ctx.get(REPLICATE_KEY, 0)
        condition = ctx.get(CONDITION_KEY, BASELINE_CONDITION)
        for artifact in ctx.artifacts:
            artifact.step_name = step.__class__.__name__
            self._manifest[artifact.name] = artifact.step_name
            dest = (
                Path(self.root_dir)
                / self.experiment_id
                / f"v{self.version}"
                / f"replicate_{rep}"
                / condition
                / artifact.step_name
            )
            os.makedirs(dest, exist_ok=True)
            path = (dest / artifact.name).resolve()
            with open(path, "wb") as f:
                f.write(artifact.data)
            by_artifact = self._artifact_paths.setdefault(artifact.name, {})
            by_artifact.setdefault(condition, path)
        ctx.artifacts.clear()

    def after_run(self, experiment: Experiment, result: Result) -> None:
        meta = {
            "replicates": experiment.replicates,
            "id": experiment.id,
            "name": experiment.name,
        }
        base = Path(self.root_dir) / self.experiment_id / f"v{self.version}"
        os.makedirs(base, exist_ok=True)
        with open(base / METADATA_FILENAME, "w") as f:
            json.dump(meta, f)

        def dump_condition(name: str, metrics: Mapping[str, Any]) -> None:
            dest = base / name
            os.makedirs(dest, exist_ok=True)

            def _default(o: Any) -> Any:
                try:
                    import numpy as np

                    if isinstance(o, np.ndarray):
                        return o.tolist()
                    if isinstance(o, np.generic):
                        return o.item()
                except Exception:  # pragma: no cover - numpy optional
                    pass
                raise TypeError(
                    f"Object of type {o.__class__.__name__} is not JSON serializable"
                )

            with open(dest / "results.json", "w") as f:
                json.dump({"metrics": metrics}, f, default=_default)
            open(dest / ".crystallize_complete", "a").close()

        dump_condition(BASELINE_CONDITION, result.metrics.baseline.metrics)
        for t_name, m in result.metrics.treatments.items():
            dump_condition(t_name, m.metrics)

        with open(base / "_manifest.json", "w") as f:
            json.dump(self._manifest, f)
        result.artifacts = {k: v.copy() for k, v in self._artifact_paths.items()}
        self._manifest.clear()
        self._artifact_paths.clear()
        if not self.versioned:
            return
        base_parent = Path(self.root_dir) / self.experiment_id
        self._prune_old_versions(base_parent)

    def _prune_old_versions(self, base_parent: Path) -> None:
        versions = sorted(
            [
                int(p.name[1:])
                for p in base_parent.glob("v*")
                if p.name.startswith("v") and p.name[1:].isdigit()
            ]
        )
        if not versions:
            return
        ret = self.artifact_retention
        keep = versions if ret <= 0 else versions[-ret:]
        if not keep:
            return
        threshold = self.big_file_threshold_mb * 1024 * 1024
        for v in keep[:-1]:
            self._prune_large_files(base_parent / f"v{v}", threshold)
        for v in versions:
            if v not in keep:
                self._prune_to_metrics(base_parent / f"v{v}")

    def _prune_large_files(self, version_dir: Path, threshold: int) -> None:
        for f in version_dir.rglob("*"):
            if not f.is_file():
                continue
            if f.name in {"results.json", "_manifest.json", METADATA_FILENAME}:
                continue
            if f.stat().st_size > threshold:
                f.unlink()

    def _prune_to_metrics(self, version_dir: Path) -> None:
        for f in version_dir.rglob("*"):
            if f.is_file() and f.name != "results.json":
                f.unlink()
        for d in sorted(version_dir.glob("**/*"), reverse=True):
            if d.is_dir():
                try:
                    d.rmdir()
                except OSError:
                    pass
