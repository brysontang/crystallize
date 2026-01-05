"""Crystallize: From Play to Proof.

Start exploring, then crystallize your findings with a hypothesis.

Example
-------
>>> from crystallize import explore
>>>
>>> # Exploratory - just play around
>>> exp = explore(
...     fn=my_function,
...     configs={"a": {"x": 1}, "b": {"x": 2}},
...     replicates=5,
... )
>>>
>>> # Check for hidden variables
>>> print(exp.hidden_variables().pretty())
>>>
>>> # Crystallize - prove something
>>> result = exp.crystallize(
...     hypothesis="b.metric > a.metric",
...     replicates=20,
... )
>>> print(result.report())
"""

import warnings
from typing import Any, Callable, Dict, Optional

# New API (a2)
from crystallize.core import (
    ConfirmRun,
    Experiment,
    HypothesisResult,
    explore,
)
from crystallize.context import Context
from crystallize.protocol import (
    HiddenVariable,
    HiddenVariablesReport,
    ProtocolDiff,
    ProtocolEvent,
    ProtocolSummary,
)
from crystallize.integrity import IntegrityStatus

# Legacy API (a1) - keep for backward compat
from crystallize.run import run as _legacy_run, RunResult

__version__ = "1.0.0a2"

__all__ = [
    # New API (a2)
    "explore",
    "Experiment",
    "ConfirmRun",
    "HypothesisResult",
    "Context",
    "IntegrityStatus",
    "HiddenVariable",
    "HiddenVariablesReport",
    "ProtocolEvent",
    "ProtocolSummary",
    "ProtocolDiff",
    # Legacy API (a1)
    "run",
    "RunResult",
]


def run(
    fn: Callable[..., Any],
    configs: Optional[Dict[str, Any]] = None,
    replicates: int = 1,
    *,
    seed: Optional[int] = None,
    hypothesis: Optional[str] = None,
    on_event: Optional[Callable[[Dict[str, Any]], None]] = None,
    progress: bool = True,
) -> RunResult:
    """Legacy run() function from v1.0.0a1.

    .. deprecated:: 1.0.0a2
        Use explore() and exp.crystallize() instead.

    This function is kept for backward compatibility. For new code, use:

    >>> exp = explore(fn, configs, replicates)
    >>> result = exp.crystallize(hypothesis, replicates)

    Parameters
    ----------
    fn : Callable
        Your function.
    configs : dict
        Configurations to compare.
    replicates : int
        Times to run each config.
    seed : int, optional
        Random seed.
    hypothesis : str, optional
        Hypothesis to test (triggers confirmatory mode).
    on_event : Callable, optional
        Callback for live updates.
    progress : bool
        Show progress bar.

    Returns
    -------
    RunResult
        Legacy result object.
    """
    warnings.warn(
        "run() is deprecated since v1.0.0a2. Use explore() and exp.crystallize() instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return _legacy_run(
        fn=fn,
        configs=configs,
        replicates=replicates,
        seed=seed,
        hypothesis=hypothesis,
        on_event=on_event,
        progress=progress,
    )
