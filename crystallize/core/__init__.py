"""Convenience factories and decorators for core classes."""

from __future__ import annotations

import inspect
from functools import update_wrapper
from typing import Any, Callable, Mapping, Optional, Union

from .context import FrozenContext
from .datasource import DataSource
from .hypothesis import Hypothesis
from .pipeline import Pipeline
from .pipeline_step import PipelineStep, exit_step
from .stat_test import StatisticalTest
from .treatment import Treatment


def pipeline_step(cacheable: bool = True) -> Callable[..., PipelineStep]:
    """Decorate a function and convert it into a :class:`PipelineStep` factory."""

    def decorator(fn: Callable[..., Any]) -> Callable[..., PipelineStep]:
        sig = inspect.signature(fn)
        param_names = [
            p.name for p in sig.parameters.values() if p.name not in {"data", "ctx"}
        ]
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


def treatment(
    name: str,
    apply: Union[Callable[[FrozenContext], Any], Mapping[str, Any], None] = None,
) -> Union[Callable[[Callable[[FrozenContext], Any]], Callable[..., Treatment]], Treatment]:
    """Create a :class:`Treatment` from a callable or mapping.

    When called with ``name`` only, returns a decorator for functions of
    ``(ctx)``. Providing ``apply`` directly returns a ``Treatment`` instance.
    """

    if apply is None:
        def decorator(fn: Callable[[FrozenContext], Any]) -> Callable[..., Treatment]:
            def factory() -> Treatment:
                return Treatment(name, fn)

            return update_wrapper(factory, fn)

        return decorator

    return Treatment(name, apply)


def hypothesis(
    *,
    metric: str,
    statistical_test: StatisticalTest,
    alpha: float = 0.05,
    direction: Optional[str] = None,
    name: Optional[str] = None,
) -> Hypothesis:
    """Create a :class:`Hypothesis` instance."""

    return Hypothesis(
        metric=metric,
        statistical_test=statistical_test,
        alpha=alpha,
        direction=direction,
        name=name,
    )


def data_source(fn: Callable[..., Any]) -> Callable[..., DataSource]:
    """Decorate a function to produce a :class:`DataSource` factory."""

    sig = inspect.signature(fn)
    param_names = [p.name for p in sig.parameters.values() if p.name != "ctx"]
    defaults = {
        name: p.default
        for name, p in sig.parameters.items()
        if name != "ctx" and p.default is not inspect.Signature.empty
    }

    def factory(**overrides: Any) -> DataSource:
        params = {**defaults, **overrides}
        missing = [n for n in param_names if n not in params]
        if missing:
            raise TypeError(f"Missing parameters: {', '.join(missing)}")

        class FunctionSource(DataSource):
            def fetch(self, ctx: FrozenContext) -> Any:
                kwargs = {n: params[n] for n in param_names}
                return fn(ctx, **kwargs)

            @property
            def params(self) -> dict:
                return {n: params[n] for n in param_names}

        FunctionSource.__name__ = f"{fn.__name__.title()}Source"
        return FunctionSource()

    return update_wrapper(factory, fn)


def statistical_test(fn: Callable[..., Any]) -> Callable[..., StatisticalTest]:
    """Decorate a function to produce a :class:`StatisticalTest` factory."""

    sig = inspect.signature(fn)
    param_names = [
        p.name
        for p in sig.parameters.values()
        if p.name not in {"baseline", "treatment", "alpha"}
    ]
    defaults = {
        name: p.default
        for name, p in sig.parameters.items()
        if name not in {"baseline", "treatment", "alpha"}
        and p.default is not inspect.Signature.empty
    }

    def factory(**overrides: Any) -> StatisticalTest:
        params = {**defaults, **overrides}
        missing = [n for n in param_names if n not in params]
        if missing:
            raise TypeError(f"Missing parameters: {', '.join(missing)}")

        class FunctionTest(StatisticalTest):
            def run(
                self,
                baseline: Any,
                treatment: Any,
                *,
                alpha: float = 0.05,
            ) -> Any:
                kwargs = {n: params[n] for n in param_names}
                return fn(baseline, treatment, alpha=alpha, **kwargs)

            @property
            def params(self) -> dict:
                return {n: params[n] for n in param_names}

        FunctionTest.__name__ = f"{fn.__name__.title()}Test"
        return FunctionTest()

    return update_wrapper(factory, fn)


def pipeline(*steps: PipelineStep) -> Pipeline:
    """Instantiate a :class:`Pipeline` from the given steps."""

    return Pipeline(list(steps))


__all__ = [
    "pipeline_step",
    "exit_step",
    "treatment",
    "hypothesis",
    "data_source",
    "statistical_test",
    "pipeline",
]
