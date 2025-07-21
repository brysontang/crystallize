from dataclasses import dataclass
from typing import Any, Callable, List

from crystallize.plugins.plugins import BasePlugin
from crystallize.experiments.experiment import Experiment

try:
    import ray
except ImportError:  # pragma: no cover - optional dependency
    ray = None


@dataclass
class RayExecution(BasePlugin):
    """Runs experiment replicates in parallel on a Ray cluster."""

    address: str = "auto"
    num_cpus: float = 1
    num_gpus: float = 0

    def init_hook(self, experiment: Experiment) -> None:
        if ray is None:
            raise ImportError(
                "The 'ray' package is required. Please install with: pip install crystallize-extras[ray]"
            )
        if not ray.is_initialized():
            ray.init(address=self.address)

    def run_experiment_loop(
        self, experiment: Experiment, replicate_fn: Callable[[int], Any]
    ) -> List[Any]:
        @ray.remote(num_cpus=self.num_cpus, num_gpus=self.num_gpus)
        def remote_replicate(rep: int):
            return replicate_fn(rep)

        futures = [remote_replicate.remote(rep) for rep in range(experiment.replicates)]
        return ray.get(futures)

    def after_run(self, experiment: Experiment, result: Any) -> None:
        if ray and ray.is_initialized():
            ray.shutdown()
