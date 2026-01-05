"""Public convenience API for Crystallize."""

from __future__ import annotations

import logging
import random
from typing import Any, Callable, Dict, List, Mapping, Optional

from crystallize.experiments.experiment_graph import ExperimentGraph
from crystallize.experiments.experiment import Experiment
from crystallize.experiments.experiment_builder import ExperimentBuilder
from crystallize.datasources.datasource import DataSource, ExperimentInput
from crystallize.datasources import Artifact
from crystallize.datasources.registry import (
    get_datasource,
    list_datasources,
    register_datasource,
)
from crystallize.experiments.treatment import Treatment
from crystallize.utils.context import FrozenContext
from crystallize.pipelines.pipeline import PipelineStep
from crystallize.pipelines.pipeline import Pipeline
from crystallize.experiments.hypothesis import Hypothesis
from crystallize.utils.decorators import (
    data_source,
    hypothesis,
    inject_from_ctx,
    pipeline,
    pipeline_step,
    resource_factory,
    treatment,
    verifier,
)
from crystallize.plugins.execution import (
    AsyncExecution,
    ParallelExecution,
    SerialExecution,
)
from crystallize.plugins.plugins import (
    ArtifactPlugin,
    BasePlugin,
    LoggingPlugin,
    SeedPlugin,
)


def standalone_context(
    initial: Optional[Mapping[str, Any]] = None,
    *,
    logger: Optional[logging.Logger] = None,
) -> FrozenContext:
    """Create a standalone context for running pipeline steps outside experiments.

    This is useful for testing individual steps, debugging, or running quick
    one-off computations without setting up a full experiment.

    Parameters
    ----------
    initial:
        Initial key-value pairs to populate the context. Defaults to empty.
    logger:
        Logger instance for the context. Defaults to the "crystallize" logger.

    Returns
    -------
    FrozenContext
        A ready-to-use context instance.

    Example
    -------
    >>> from crystallize import standalone_context
    >>> ctx = standalone_context({"input_data": [1, 2, 3]})
    >>> # Now you can pass ctx to any pipeline step
    >>> result = my_step(ctx)
    >>> ctx.record("accuracy", 0.95, tags={"model": "v1"})
    """
    return FrozenContext(initial or {}, logger=logger)


def quick_experiment(
    fn: Callable[..., Any],
    configs: Optional[Dict[str, Any]] = None,
    replicates: int = 1,
    *,
    seed: Optional[int] = None,
    verbose: bool = False,
) -> Dict[str, List[Any]]:
    """Run a quick experiment without full Crystallize setup.

    This is the on-ramp to Crystallize. Use it when you want:
    - Multiple replicates with seeding
    - Easy comparison across configs
    - No YAML, no classes, just results

    Graduate to full Experiment class when you need plugins/hypotheses/artifacts.

    Parameters
    ----------
    fn:
        The function to run. Can accept (config) or (config, ctx) signature.
    configs:
        Dict mapping config names to config objects. If None, runs with no config.
    replicates:
        Number of times to run each config. Default is 1.
    seed:
        Base random seed for reproducibility. Each replicate gets seed + i.
    verbose:
        If True, print progress. Default is False.

    Returns
    -------
    Dict[str, List[Any]]
        Results keyed by config name. Each value is a list of results per replicate.

    Example
    -------
    >>> from crystallize import quick_experiment
    >>>
    >>> def run_game(config):
    ...     return {"score": random.random() * config["difficulty"]}
    >>>
    >>> results = quick_experiment(
    ...     fn=run_game,
    ...     configs={
    ...         "easy": {"difficulty": 1},
    ...         "hard": {"difficulty": 10},
    ...     },
    ...     replicates=5,
    ...     seed=42,
    ... )
    >>> # results["easy"] = [{"score": 0.3}, {"score": 0.7}, ...]
    >>> # results["hard"] = [{"score": 4.2}, {"score": 8.1}, ...]
    """
    import inspect

    # Determine if fn accepts ctx parameter
    sig = inspect.signature(fn)
    params = list(sig.parameters.keys())
    accepts_ctx = "ctx" in params or len(params) >= 2

    # Default to single "baseline" config if none provided
    if configs is None:
        configs = {"baseline": None}

    results: Dict[str, List[Any]] = {}

    for config_name, config in configs.items():
        results[config_name] = []

        for i in range(replicates):
            # Set seed for this replicate
            if seed is not None:
                replicate_seed = seed + i * 31337
                random.seed(replicate_seed)
                try:
                    import numpy as np
                    np.random.seed(replicate_seed)
                except ImportError:
                    pass

            if verbose:
                print(f"Running {config_name} replicate {i + 1}/{replicates}...")

            # Create context for this run
            ctx = FrozenContext(
                {"replicate": i, "condition": config_name, "seed": seed}
            )

            # Call function with appropriate signature
            if accepts_ctx:
                if config is not None:
                    result = fn(config, ctx)
                else:
                    result = fn(ctx)
            else:
                if config is not None:
                    result = fn(config)
                else:
                    result = fn()

            results[config_name].append(result)

    if verbose:
        print("Done!")

    return results


__all__ = [
    # Helpers
    "standalone_context",
    "quick_experiment",
    "get_datasource",
    "list_datasources",
    "register_datasource",
    # Decorators
    "pipeline_step",
    "inject_from_ctx",
    "treatment",
    "hypothesis",
    "data_source",
    "verifier",
    "pipeline",
    "resource_factory",
    # Classes
    "PipelineStep",
    "Pipeline",
    "Hypothesis",
    "Experiment",
    "DataSource",
    "FrozenContext",
    "Treatment",
    "BasePlugin",
    "SerialExecution",
    "ParallelExecution",
    "AsyncExecution",
    "SeedPlugin",
    "LoggingPlugin",
    "ArtifactPlugin",
    "ExperimentGraph",
    "Artifact",
    "ExperimentInput",
    "ExperimentBuilder",
]
