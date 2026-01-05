"""Crystallize: From Play to Proof.

Start exploring, then crystallize your findings with a hypothesis.

Example
-------
>>> from crystallize import run
>>>
>>> # Exploratory - just play around
>>> results = run(
...     fn=my_function,
...     configs={"a": {"x": 1}, "b": {"x": 2}},
...     replicates=5,
... )
>>>
>>> # Confirmatory - prove something
>>> results = run(
...     fn=my_function,
...     configs={"baseline": {...}, "treatment": {...}},
...     replicates=20,
...     hypothesis="treatment.win_rate > baseline.win_rate",
...     seed=42,
... )
"""

from crystallize.run import run, RunResult, HypothesisResult, Context

__version__ = "1.0.0a1"

__all__ = [
    "run",
    "RunResult",
    "HypothesisResult",
    "Context",
]
