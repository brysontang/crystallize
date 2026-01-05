"""Convenience factories and decorators for core classes."""

from __future__ import annotations

import inspect
import types
import hashlib
import threading
import textwrap
from functools import update_wrapper
from typing import Any, Callable, Mapping, Optional, Sequence, Union

from crystallize.utils.constants import (
    BASELINE_CONDITION,
    CONDITION_KEY,
    METADATA_FILENAME,
    REPLICATE_KEY,
    SEED_USED_KEY,
)
from crystallize.utils.context import FrozenContext
from crystallize.datasources.datasource import DataSource, ExperimentInput
from crystallize.plugins.execution import ParallelExecution, SerialExecution
from crystallize.experiments.experiment import Experiment
from crystallize.experiments.experiment_graph import ExperimentGraph
from crystallize.experiments.hypothesis import Hypothesis
from crystallize.utils.injection import inject_from_ctx
from crystallize.experiments.optimizers import BaseOptimizer, Objective
from crystallize.pipelines.pipeline import Pipeline
from crystallize.pipelines.pipeline_step import PipelineStep
from crystallize.plugins.plugins import (
    ArtifactPlugin,
    BasePlugin,
    LoggingPlugin,
    SeedPlugin,
)
from crystallize.experiments.result import Result
from crystallize.experiments.run_results import ReplicateResult
from crystallize.experiments.treatment import Treatment
from crystallize.utils.cache import compute_hash

_resource_cache = threading.local()


def _reconstruct_from_factory(
    factory: Callable[..., Any], params: Mapping[str, Any]
) -> Any:
    """Helper for pickling dynamically created objects."""

    return factory(**params)


class ResourceFactoryWrapper:
    """A picklable, callable class that wraps a resource-creating function."""

    def __init__(self, fn: Callable[[FrozenContext], Any], key: str | None = None):
        self.fn = fn
        self.key = key
        # Make this object look like the function it's wrapping
        update_wrapper(self, fn)

    def __call__(self, ctx: FrozenContext) -> Any:
        # The logic from the old 'wrapper' function is now here.
        if not hasattr(_resource_cache, "cache"):
            _resource_cache.cache = {}
        cache = _resource_cache.cache

        cache_key = self.key if self.key is not None else hash(self.fn.__code__)
        if cache_key not in cache:
            cache[cache_key] = self.fn(ctx)
        return cache[cache_key]


def resource_factory(
    fn: Callable[[FrozenContext], Any], *, key: str | None = None
) -> Callable[[FrozenContext], Any]:
    """Wrap a factory so the created resource is reused per thread/process."""
    return ResourceFactoryWrapper(fn, key)


def _code_digest(obj: types.FunctionType) -> str:
    # Robust: fall back if source missing (e.g., in REPL)
    try:
        src = textwrap.dedent(inspect.getsource(obj))
    except (OSError, TypeError):
        src = obj.__code__.co_code  # bytes as fallback
    return hashlib.sha256(src.encode() if isinstance(src, str) else src).hexdigest()


def pipeline_step(cacheable: bool = False) -> Callable[..., PipelineStep]:
    """Decorate a function and convert it into a :class:`PipelineStep` factory."""

    def decorator(fn: Callable[..., Any]) -> Callable[..., PipelineStep]:
        code_digest = _code_digest(fn)

        sig = inspect.signature(fn)
        param_names = [
            p.name for p in sig.parameters.values() if p.name not in {"data", "ctx"}
        ]
        defaults = {
            name: p.default
            for name, p in sig.parameters.items()
            if name not in {"data", "ctx"} and p.default is not inspect.Signature.empty
        }

        injected_fn = inject_from_ctx(fn)

        is_cacheable = cacheable

        def factory(**overrides: Any) -> PipelineStep:
            unknown = set(overrides) - set(param_names)
            if unknown:
                raise TypeError(f"Unknown parameters: {', '.join(sorted(unknown))}")
            params = dict(overrides)
            missing = [n for n in param_names if n not in params and n not in defaults]
            if missing:
                raise TypeError(f"Missing parameters: {', '.join(missing)}")

            explicit_params = set(overrides)

            class FunctionStep(PipelineStep):
                cacheable = is_cacheable

                def __call__(self, data: Any, ctx: FrozenContext) -> Any:
                    kwargs = {n: params[n] for n in explicit_params}
                    return injected_fn(data, ctx, **kwargs)

                async def __acall__(self, data: Any, ctx: FrozenContext) -> Any:
                    kwargs = {n: params[n] for n in explicit_params}
                    return await injected_fn(data, ctx, **kwargs)

                @property
                def params(self) -> dict:
                    return {n: params[n] for n in explicit_params}

                def __reduce__(self):
                    return _reconstruct_from_factory, (factory, params)

                @property
                def step_hash(self) -> str:
                    payload = {
                        "class": self.__class__.__name__,
                        "params": self.params,
                        "code": code_digest,
                    }
                    return compute_hash(payload)

            FunctionStep.__name__ = f"{fn.__name__.title()}Step"
            step = FunctionStep()  # ← create instance
            step.__orig_source__ = inspect.getsourcefile(fn)
            step.__orig_lineno__ = inspect.getsourcelines(fn)[1]
            return step

        return update_wrapper(factory, fn)

    return decorator


def treatment(
    name: str,
    apply: Union[Callable[[FrozenContext], Any], Mapping[str, Any], None] = None,
) -> Union[
    Callable[[Callable[[FrozenContext], Any]], Callable[..., Treatment]], Treatment
]:
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
    verifier: Callable[
        [Mapping[str, Sequence[Any]], Mapping[str, Sequence[Any]]], Mapping[str, Any]
    ],
    metrics: str | Sequence[str] | Sequence[Sequence[str]] | None = None,
    name: Optional[str] = None,
) -> Callable[[Callable[[Mapping[str, Any]], float]], Hypothesis]:
    """Decorate a ranker function and produce a :class:`Hypothesis`."""

    def decorator(fn: Callable[[Mapping[str, Any]], float]) -> Hypothesis:
        return Hypothesis(
            verifier=verifier, metrics=metrics, ranker=fn, name=name or fn.__name__
        )

    return decorator


def data_source(
    fn_or_name: Union[Callable[..., Any], str, None] = None,
    *,
    register: bool = False,
) -> Union[Callable[..., DataSource], Callable[[Callable[..., Any]], Callable[..., DataSource]]]:
    """Decorate a function to produce a :class:`DataSource` factory.

    Can be used in several ways:

    1. Simple decorator (no registration):
       >>> @data_source
       ... def my_source(ctx):
       ...     return [1, 2, 3]

    2. Named decorator with auto-registration:
       >>> @data_source("training_data", register=True)
       ... def my_source(ctx):
       ...     return [1, 2, 3]
       >>> # Now accessible via get_datasource("training_data")

    3. Register with function name:
       >>> @data_source(register=True)
       ... def training_data(ctx):
       ...     return [1, 2, 3]
       >>> # Now accessible via get_datasource("training_data")

    Parameters
    ----------
    fn_or_name:
        Either the function to decorate, or a string name for registration.
    register:
        If True, register the datasource with the given name (or function name).
    """
    from crystallize.datasources.registry import register_datasource

    def _make_factory(fn: Callable[..., Any], reg_name: Optional[str] = None) -> Callable[..., DataSource]:
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

                def __reduce__(self):
                    return _reconstruct_from_factory, (factory, params)

            FunctionSource.__name__ = f"{fn.__name__.title()}Source"
            return FunctionSource()

        result = update_wrapper(factory, fn)

        # Register if requested
        if reg_name is not None:
            # Create a default instance for registration
            try:
                default_ds = factory()
                register_datasource(reg_name, default_ds)
            except TypeError:
                # Can't create default instance (missing required params)
                # User will need to register manually after calling factory
                pass

        return result

    # Handle different calling patterns
    if fn_or_name is None:
        # @data_source() or @data_source(register=True)
        def decorator(fn: Callable[..., Any]) -> Callable[..., DataSource]:
            name = fn.__name__ if register else None
            return _make_factory(fn, name)
        return decorator
    elif isinstance(fn_or_name, str):
        # @data_source("name") or @data_source("name", register=True)
        def decorator(fn: Callable[..., Any]) -> Callable[..., DataSource]:
            name = fn_or_name if register else None
            return _make_factory(fn, name)
        return decorator
    else:
        # @data_source (no parens)
        return _make_factory(fn_or_name, fn_or_name.__name__ if register else None)


class VerifierCallable:
    """A picklable callable that wraps the verifier function with fixed parameters."""

    def __init__(
        self,
        fn: Callable[..., Any],
        params: dict,
        param_names: list[str],
        factory: Callable[..., Any],
    ):
        self.fn = fn
        self.params = params
        self.param_names = param_names
        self._factory = factory

    def __call__(
        self,
        baseline_samples: Mapping[str, Sequence[Any]],
        treatment_samples: Mapping[str, Sequence[Any]],
    ) -> Mapping[str, Any]:
        kwargs = {n: self.params[n] for n in self.param_names}
        return self.fn(baseline_samples, treatment_samples, **kwargs)

    def __reduce__(self):
        # Tell pickle to reconstruct via the factory and saved params
        return _reconstruct_from_factory, (self._factory, self.params)


def verifier(
    fn: Callable[..., Any],
) -> Callable[
    ...,
    Callable[
        [Mapping[str, Sequence[Any]], Mapping[str, Sequence[Any]]], Mapping[str, Any]
    ],
]:
    """Decorate a function to produce a parameterized, picklable verifier callable."""

    sig = inspect.signature(fn)
    param_names = [
        p.name
        for p in sig.parameters.values()
        if p.name
        not in {"baseline_samples", "treatment_samples", "baseline", "treatment"}
    ]
    defaults = {
        name: p.default
        for name, p in sig.parameters.items()
        if name
        not in {"baseline_samples", "treatment_samples", "baseline", "treatment"}
        and p.default is not inspect.Signature.empty
    }

    def factory(
        **overrides: Any,
    ) -> VerifierCallable:
        unknown = set(overrides) - set(param_names)
        if unknown:
            raise TypeError(f"Unknown parameters: {', '.join(sorted(unknown))}")
        params = {**defaults, **overrides}
        missing = [n for n in param_names if n not in params]
        if missing:
            raise TypeError(f"Missing parameters: {', '.join(missing)}")

        # Pass the factory itself so __reduce__ can reconstruct
        return VerifierCallable(fn, params, param_names, factory)

    # Preserve metadata from the original function (e.g. __name__, __doc__)
    return update_wrapper(factory, fn)


def pipeline(*steps: PipelineStep) -> Pipeline:
    """Instantiate a :class:`Pipeline` from the given steps."""

    return Pipeline(list(steps))


__all__ = [
    "ArtifactPlugin",
    "BasePlugin",
    "BaseOptimizer",
    "DataSource",
    "ExperimentInput",
    "Experiment",
    "ExperimentGraph",
    "FrozenContext",
    "Hypothesis",
    "LoggingPlugin",
    "Objective",
    "ParallelExecution",
    "Pipeline",
    "PipelineStep",
    "resource_factory",
    "Result",
    "ReplicateResult",
    "SeedPlugin",
    "SerialExecution",
    "Treatment",
    "pipeline_step",
    "treatment",
    "hypothesis",
    "data_source",
    "verifier",
    "pipeline",
    "inject_from_ctx",
    "METADATA_FILENAME",
    "BASELINE_CONDITION",
    "REPLICATE_KEY",
    "CONDITION_KEY",
    "SEED_USED_KEY",
]
