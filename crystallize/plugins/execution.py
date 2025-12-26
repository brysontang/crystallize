from __future__ import annotations

import asyncio
import inspect
from dataclasses import dataclass
import os
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from typing import Callable, List, Any, Optional, TYPE_CHECKING

from .plugins import BasePlugin

if TYPE_CHECKING:  # pragma: no cover - for type hints
    from ..experiments.experiment import Experiment

VALID_EXECUTOR_TYPES = {"thread", "process"}


@dataclass
class SerialExecution(BasePlugin):
    """Execute replicates one after another within the main process."""

    progress: bool = False

    async def run_experiment_loop(
        self, experiment: "Experiment", replicate_fn: Callable[[int], Any]
    ) -> List[Any]:
        reps = range(experiment.replicates)
        if self.progress and experiment.replicates > 1:
            from tqdm import tqdm  # type: ignore

            reps = tqdm(reps, desc="Replicates")

        results = []
        for rep in reps:
            results.append(await replicate_fn(rep))
        return results


@dataclass
class ParallelExecution(BasePlugin):
    """Run SYNC replicates concurrently using ThreadPoolExecutor or ProcessPoolExecutor."""

    max_workers: Optional[int] = None
    executor_type: str = "thread"
    progress: bool = False

    def run_experiment_loop(
        self, experiment: "Experiment", replicate_fn: Callable[[int], Any]
    ) -> List[Any]:
        # This plugin is for SYNC tasks. If given an ASYNC task, raise a clear error.
        if inspect.iscoroutinefunction(replicate_fn):
            raise TypeError(
                "ParallelExecution only supports synchronous tasks. "
                "Use the AsyncExecution plugin for async workloads."
            )

        if self.executor_type not in VALID_EXECUTOR_TYPES:
            raise ValueError(
                f"executor_type must be one of {VALID_EXECUTOR_TYPES}, got '{self.executor_type}'"
            )

        from .plugins import SeedPlugin

        get_plugin = getattr(experiment, "get_plugin", None)
        if (
            self.executor_type == "thread"
            and callable(get_plugin)
            and get_plugin(SeedPlugin)
        ):
            import logging

            logging.getLogger("crystallize").warning(
                "Using SeedPlugin with executor_type='thread' is not reproducible "
                "because 'random' state is shared. Use 'process' for determinism."
            )
        if self.executor_type == "process":
            from crystallize.experiments.experiment import _run_replicate_remote

            default_workers = max(1, (os.cpu_count() or 2) - 1)
            exec_cls = ProcessPoolExecutor
            submit_target = _run_replicate_remote
            treatments = getattr(experiment, "treatments", [])
            baseline_treatment = getattr(experiment, "_baseline_treatment", None)
            arg_list = [
                (experiment, rep, treatments, baseline_treatment)
                for rep in range(experiment.replicates)
            ]
        else:  # 'thread'
            default_workers = os.cpu_count() or 8
            exec_cls = ThreadPoolExecutor
            submit_target = replicate_fn
            arg_list = list(range(experiment.replicates))

        worker_count = self.max_workers or min(experiment.replicates, default_workers)
        results: List[Any] = [None] * experiment.replicates
        with exec_cls(max_workers=worker_count) as executor:
            try:
                future_map = {
                    executor.submit(submit_target, arg): rep
                    for rep, arg in enumerate(arg_list)
                }
            except Exception as exc:
                if self.executor_type == "process" and "pickle" in repr(exc).lower():
                    step_names = [
                        s.__class__.__name__
                        for s in getattr(getattr(experiment, "pipeline", None), "steps", [])
                    ]
                    exp_name = getattr(experiment, "name", None) or getattr(
                        experiment, "id", None
                    ) or "<unnamed>"
                    step_msg = (
                        f" Pipeline steps: {', '.join(step_names)}."
                        " Step factories must be picklable."
                        if step_names
                        else ""
                    )
                    raise RuntimeError(
                        "Failed to pickle experiment "
                        f"'{exp_name}' for multiprocessing. "
                        "Non-picklable closures or lambdas in steps, datasources, "
                        "or verifiers may be the cause. Wrap heavy resources with "
                        "resource_factory(...)."
                        + step_msg
                    ) from exc
                raise
            futures = as_completed(future_map)
            if self.progress and experiment.replicates > 1:
                from tqdm import tqdm  # type: ignore

                futures = tqdm(futures, total=len(future_map), desc="Replicates")
            for fut in futures:
                idx = future_map[fut]
                results[idx] = fut.result()
        return results


@dataclass
class AsyncExecution(BasePlugin):
    """Run async replicates concurrently using asyncio.gather."""

    progress: bool = False

    async def run_experiment_loop(
        self, experiment: "Experiment", replicate_fn: Callable[[int], Any]
    ) -> List[Any]:
        tasks = [replicate_fn(rep) for rep in range(experiment.replicates)]

        if self.progress and experiment.replicates > 1:
            from tqdm.asyncio import tqdm

            return await tqdm.gather(*tasks, desc="Replicates")
        return await asyncio.gather(*tasks)
