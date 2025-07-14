from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Tuple, Union

from crystallize.core.cache import compute_hash
from crystallize.core.context import FrozenContext


class PipelineStep(ABC):
    cacheable = False

    @abstractmethod
    def __call__(self, data: Any, ctx: FrozenContext) -> Any:
        """
        Execute the pipeline step.

        Args:
            data (Any): Input data to the step.
            ctx (FrozenContext): Immutable execution context.

        Returns:
            Any: Transformed or computed data.
        """
        raise NotImplementedError()

    @property
    @abstractmethod
    def params(self) -> dict:
        """
        Parameters of this step for hashing and caching.

        Returns:
            dict: Parameters dictionary.
        """
        raise NotImplementedError()

    # ------------------------------------------------------------------ #
    @property
    def step_hash(self) -> str:
        """Unique hash identifying this step based on its parameters."""

        payload = {"class": self.__class__.__name__, "params": self.params}
        return compute_hash(payload)


def exit_step(item: Union[PipelineStep, Callable[..., PipelineStep], Tuple[Callable[..., PipelineStep], Dict[str, Any]]]) -> Union[PipelineStep, Callable[..., PipelineStep]]:
    """Mark a :class:`PipelineStep` as the final step of a pipeline.

    This helper accepts an already constructed step, a factory callable or a
    ``(factory, params)`` tuple as produced by :func:`pipeline_step`.  The
    returned object behaves identically to the input but is annotated with the
    ``is_exit_step`` attribute so that :meth:`Experiment.apply` knows when to
    stop execution.
    """
    if isinstance(item, PipelineStep):
        setattr(item, "is_exit_step", True)
        return item
    elif isinstance(item, tuple):  # From param
        factory, fixed_kwargs = item
        def wrapped_factory(**extra_kwargs: Any) -> PipelineStep:
            inst = factory(**{**fixed_kwargs, **extra_kwargs})
            setattr(inst, "is_exit_step", True)
            return inst
        return wrapped_factory
    elif callable(item):  # Plain factory
        def wrapped_factory(**kwargs: Any) -> PipelineStep:
            inst = item(**kwargs)
            setattr(inst, "is_exit_step", True)
            return inst
        return wrapped_factory
    raise TypeError(f"Invalid item for exit_step: {type(item).__name__}")