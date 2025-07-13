from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from .datasource import DataSource
from .experiment import Experiment
from .hypothesis import Hypothesis
from .pipeline import Pipeline
from .pipeline_step import PipelineStep
from .result import Result
from .treatment import Treatment

StepInput = Union[
    PipelineStep,
    Callable[..., PipelineStep],
    Tuple[Callable[..., PipelineStep], Dict[str, Any]],
]


class ExperimentBuilder:
    """Fluent helper for constructing :class:`Experiment` instances."""

    def __init__(self) -> None:
        self._datasource: Optional[DataSource] = None
        self._pipeline_steps: List[StepInput] = []
        self._treatments: List[Treatment] = []
        self._hypotheses: List[Hypothesis] = []
        self._replicates: int = 1
        self._parallel: bool = False
        self._seed: Optional[int] = None
        self._auto_seed: bool = True
        self._seed_fn: Optional[Callable[[int], None]] = None
        self._max_workers: Optional[int] = None
        self._executor_type: str = "thread"
        self._progress: bool = False
        self._verbose: bool = False
        self._log_level: str = "INFO"

    # ------------------------------------------------------------------ #
    def datasource(
        self,
        source: Union[
            DataSource,
            Callable[..., DataSource],
            Tuple[Callable[..., DataSource], Dict[str, Any]],
        ],
    ) -> "ExperimentBuilder":
        self._datasource = self._instantiate(source)
        return self

    def pipeline(self, steps: List[StepInput]) -> "ExperimentBuilder":
        self._pipeline_steps = steps
        return self

    def treatments(self, treatments: List[Treatment]) -> "ExperimentBuilder":
        self._treatments = treatments
        return self

    def hypotheses(self, hypotheses: List[Hypothesis]) -> "ExperimentBuilder":
        self._hypotheses = hypotheses
        return self

    def replicates(self, replicates: int) -> "ExperimentBuilder":
        self._replicates = max(1, replicates)
        return self

    def parallel(self, parallel: bool) -> "ExperimentBuilder":
        self._parallel = parallel
        return self

    def seed(self, seed: Optional[int]) -> "ExperimentBuilder":
        self._seed = seed
        return self

    def auto_seed(self, auto: bool) -> "ExperimentBuilder":
        self._auto_seed = auto
        return self

    def seed_fn(self, fn: Callable[[int], None]) -> "ExperimentBuilder":
        self._seed_fn = fn
        return self

    def max_workers(self, max_workers: Optional[int]) -> "ExperimentBuilder":
        self._max_workers = max_workers
        return self

    def executor_type(self, executor_type: str) -> "ExperimentBuilder":
        if executor_type not in Experiment.VALID_EXECUTOR_TYPES:
            raise ValueError(
                f"executor_type must be one of {Experiment.VALID_EXECUTOR_TYPES}, got '{executor_type}'"
            )
        self._executor_type = executor_type
        return self

    def progress(self, progress: bool) -> "ExperimentBuilder":
        self._progress = progress
        return self

    def verbose(self, verbose: bool) -> "ExperimentBuilder":
        self._verbose = verbose
        return self

    def log_level(self, log_level: str) -> "ExperimentBuilder":
        self._log_level = log_level
        return self

    # ------------------------------------------------------------------ #
    def _instantiate(self, item: Any) -> Any:
        if isinstance(item, PipelineStep):
            return item
        if isinstance(item, tuple):
            factory, kwargs = item
            return factory(**kwargs)
        if callable(item):
            return item()
        return item

    # ------------------------------------------------------------------ #
    def build(self) -> Experiment:
        normalized_steps = [self._instantiate(step) for step in self._pipeline_steps]
        pipeline_obj = Pipeline(normalized_steps)
        exp = Experiment(
            datasource=self._datasource,
            pipeline=pipeline_obj,
            treatments=self._treatments,
            hypotheses=self._hypotheses,
            replicates=self._replicates,
            parallel=self._parallel,
            seed=self._seed,
            auto_seed=self._auto_seed,
            progress=self._progress,
            verbose=self._verbose,
            log_level=self._log_level,
            seed_fn=self._seed_fn,
            max_workers=self._max_workers,
            executor_type=self._executor_type,
        )
        exp.validate()
        return exp

    def build_and_run(self) -> Result:
        return self.build().run()
