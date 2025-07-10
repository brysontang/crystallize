"""Public API and helper decorators."""

from __future__ import annotations

import inspect
from functools import update_wrapper
from typing import Any, Callable, Optional

from crystallize.core.context import FrozenContext
from crystallize.core.hypothesis import Hypothesis
from crystallize.core.pipeline_step import PipelineStep
from crystallize.core.treatment import Treatment
from crystallize.core.stat_test import StatisticalTest


def pipeline_step(cacheable: bool = True) -> Callable[..., PipelineStep]:
    """Decorate a function and convert it into a :class:`PipelineStep` factory."""

    def decorator(fn: Callable[..., Any]) -> Callable[..., PipelineStep]:
        sig = inspect.signature(fn)
        param_names = [p.name for p in sig.parameters.values() if p.name not in {"data", "ctx"}]
        defaults = {
            name: p.default
            for name, p in sig.parameters.items()
            if name not in {"data", "ctx"} and p.default is not inspect.Signature.empty
        }

        is_cacheable = cacheable

        def factory(**overrides: Any) -> PipelineStep:
            params = {**defaults, **overrides}
            missing = [n for n in param_names if n not in params]
            if missing:
                raise TypeError(f"Missing parameters: {', '.join(missing)}")

            class FunctionStep(PipelineStep):
                cacheable = is_cacheable

                def __call__(self, data: Any, ctx: FrozenContext) -> Any:
                    kwargs = {n: params[n] for n in param_names}
                    return fn(data, ctx, **kwargs)

                @property
                def params(self) -> dict:
                    return {n: params[n] for n in param_names}

            FunctionStep.__name__ = f"{fn.__name__.title()}Step"
            return FunctionStep()

        return update_wrapper(factory, fn)

    return decorator


def treatment(name: str) -> Callable[..., Treatment]:
    """Decorate a function to quickly create a :class:`Treatment`."""

    def decorator(fn: Callable[[FrozenContext], Any]) -> Callable[..., Treatment]:
        def factory() -> Treatment:
            return Treatment(name, fn)

        return update_wrapper(factory, fn)

    return decorator


def hypothesis(
    *,
    metric: str,
    statistical_test: StatisticalTest,
    alpha: float = 0.05,
    direction: Optional[str] = None,
) -> Callable[..., Hypothesis]:
    """Decorator returning a :class:`Hypothesis` factory."""

    def decorator(fn: Optional[Callable[..., Any]] = None) -> Callable[..., Hypothesis]:
        def factory() -> Hypothesis:
            return Hypothesis(
                metric=metric,
                statistical_test=statistical_test,
                alpha=alpha,
                direction=direction,
            )

        if fn is not None:
            return update_wrapper(factory, fn)
        return factory

    return decorator

__all__ = ["pipeline_step", "treatment", "hypothesis"]
