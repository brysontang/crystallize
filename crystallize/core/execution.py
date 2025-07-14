from __future__ import annotations

from dataclasses import dataclass
import os
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from typing import Callable, List, Any, Optional, TYPE_CHECKING

from .plugins import BasePlugin

if TYPE_CHECKING:  # pragma: no cover - for type hints
    from .experiment import Experiment

VALID_EXECUTOR_TYPES = {"thread", "process"}


@dataclass
class SerialExecution(BasePlugin):
    """Execute replicates one after another within the main process."""

    progress: bool = False

    def run_experiment_loop(
        self, experiment: "Experiment", replicate_fn: Callable[[int], Any]
    ) -> List[Any]:
        reps = range(experiment.replicates)
        if self.progress and experiment.replicates > 1:
            from tqdm import tqdm  # type: ignore

            reps = tqdm(reps, desc="Replicates")
        return [replicate_fn(rep) for rep in reps]


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
        if self.executor_type == "process":
            from .experiment import _run_replicate_remote

            default_workers = max(1, (os.cpu_count() or 2) - 1)
            exec_cls = ProcessPoolExecutor
            submit_target = _run_replicate_remote
            arg_list = [(experiment, rep) for rep in range(experiment.replicates)]
        else:
            default_workers = os.cpu_count() or 8
            exec_cls = ThreadPoolExecutor
            submit_target = replicate_fn
            arg_list = list(range(experiment.replicates))
        worker_count = self.max_workers or min(experiment.replicates, default_workers)
        results: List[Any] = [None] * experiment.replicates
        with exec_cls(max_workers=worker_count) as executor:
            future_map = {
                executor.submit(submit_target, arg): rep
                for rep, arg in enumerate(arg_list)
            }
            futures = as_completed(future_map)
            if self.progress and experiment.replicates > 1:
                from tqdm import tqdm  # type: ignore

                futures = tqdm(futures, total=len(future_map), desc="Replicates")
            for fut in futures:
                idx = future_map[fut]
                results[idx] = fut.result()
        return results
