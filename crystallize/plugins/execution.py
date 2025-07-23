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

    def run_experiment_loop(
        self, experiment: "Experiment", replicate_fn: Callable[[int], Any]
    ) -> List[Any] | asyncio.Future:
        reps = range(experiment.replicates)
        if self.progress and experiment.replicates > 1:
            from tqdm import tqdm  # type: ignore

            reps = tqdm(reps, desc="Replicates")

        if asyncio.iscoroutinefunction(replicate_fn):
            async def run_all() -> List[Any]:
                return [await replicate_fn(rep) for rep in reps]

            try:
                asyncio.get_running_loop()
                return run_all()
            except RuntimeError:  # no running loop
                return asyncio.run(run_all())

        results = []
        for rep in reps:
            res = replicate_fn(rep)
            if inspect.isawaitable(res):
                try:
                    asyncio.get_running_loop()
                    raise RuntimeError(
                        "Async replicate_fn must be awaited in running loop"
                    )
                except RuntimeError:
                    res = asyncio.run(res)
            results.append(res)
        return results


@dataclass
class ParallelExecution(BasePlugin):
    """Run replicates concurrently using ``ThreadPoolExecutor`` or ``ProcessPoolExecutor``."""

    max_workers: Optional[int] = None
    executor_type: str = "thread"
    progress: bool = False

    def run_experiment_loop(
        self, experiment: "Experiment", replicate_fn: Callable[[int], Any]
    ) -> List[Any]:
        if self.executor_type not in VALID_EXECUTOR_TYPES:
            raise ValueError(
                f"executor_type must be one of {VALID_EXECUTOR_TYPES}, got '{self.executor_type}'"
            )
        async_fn = asyncio.iscoroutinefunction(replicate_fn)
        if self.executor_type == "process":
            from crystallize.experiments.experiment import _run_replicate_remote

            default_workers = max(1, (os.cpu_count() or 2) - 1)
            exec_cls = ProcessPoolExecutor
            actual_process = exec_cls.__name__ == "ProcessPoolExecutor"
            if actual_process:
                submit_target = _run_replicate_remote
                treatments = getattr(experiment, "treatments", [])
                arg_list = [
                    (experiment, rep, treatments)
                    for rep in range(experiment.replicates)
                ]
            else:
                worker_count = self.max_workers or default_workers
                treatments = getattr(experiment, "treatments", [])
                with ProcessPoolExecutor(max_workers=worker_count) as executor:
                    future_map = {
                        executor.submit(
                            _run_replicate_remote,
                            (experiment, rep, treatments),
                        ): rep
                        for rep in range(experiment.replicates)
                    }
                    futures = as_completed(future_map)
                    if self.progress and experiment.replicates > 1:
                        from tqdm import tqdm  # type: ignore

                        futures = tqdm(futures, total=len(future_map), desc="Replicates")
                    results = [None] * experiment.replicates
                    for fut in futures:
                        idx = future_map[fut]
                        results[idx] = fut.result()
                return results
        else:
            default_workers = os.cpu_count() or 8
            exec_cls = ThreadPoolExecutor
            if async_fn:
                def submit_target(rep):
                    return asyncio.run(replicate_fn(rep))
            else:
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
                    raise RuntimeError(
                        "Failed to pickle experiment for multiprocessing. "
                        "Use 'resource_factory' for non-picklable dependencies."
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
