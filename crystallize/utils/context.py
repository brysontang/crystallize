import copy
import logging
from collections import defaultdict
from types import MappingProxyType
from typing import Any, DefaultDict, Dict, List, Mapping, Optional, Tuple, cast  # noqa: F401

from crystallize.datasources.artifacts import ArtifactLog
from crystallize.utils.exceptions import ContextMutationError


class FrozenMetrics:
    """Immutable mapping of metric lists with safe append."""

    def __init__(self) -> None:
        self._metrics: DefaultDict[str, List[Any]] = defaultdict(list)
        self._tags: DefaultDict[str, List[Dict[str, Any]]] = defaultdict(list)

    def __getitem__(self, key: str) -> Tuple[Any, ...]:
        return tuple(self._metrics[key])

    def add(self, key: str, value: Any, tags: Optional[Dict[str, Any]] = None) -> None:
        """Append a value to the metric list, optionally with tags."""
        self._metrics[key].append(value)
        self._tags[key].append(tags or {})

    def get_tags(self, key: str) -> Tuple[Dict[str, Any], ...]:
        """Return the tags for each recorded value of a metric."""
        return tuple(self._tags[key])

    def as_dict(self) -> Mapping[str, Tuple[Any, ...]]:
        return MappingProxyType({k: tuple(v) for k, v in self._metrics.items()})


class FrozenContext:
    """Immutable execution context shared between pipeline steps.

    Once a key is set its value cannot be modified. Attempting to do so raises
    :class:`ContextMutationError`. This immutability guarantees deterministic
    provenance during pipeline execution.

        Attributes:
            metrics: :class:`FrozenMetrics` used to accumulate lists of metric
            values.
        artifacts: :class:`ArtifactLog` collecting binary artifacts to be saved
            by :class:`~crystallize.plugins.plugins.ArtifactPlugin`.
        logger: :class:`logging.Logger` used for debug and info messages.
    """

    def __init__(
        self, initial: Mapping[str, Any], logger: Optional[logging.Logger] = None
    ) -> None:
        self._data = copy.deepcopy(dict(initial))
        self.metrics = FrozenMetrics()
        self.artifacts = ArtifactLog()
        self.logger = logger or logging.getLogger("crystallize")

    def __getitem__(self, key: str) -> Any:
        return copy.deepcopy(self._data[key])

    def __setitem__(self, key: str, value: Any) -> None:
        if key in self._data:
            raise ContextMutationError(f"Cannot mutate existing key: '{key}'")
        self._data[key] = value

    def add(self, key: str, value: Any) -> None:
        """Alias for ``__setitem__`` providing a clearer API."""
        self.__setitem__(key, value)

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """Return the value for ``key`` if present else ``default``."""
        if key in self._data:
            return copy.deepcopy(self._data[key])
        return copy.deepcopy(default)

    def as_dict(self) -> Mapping[str, Any]:
        return MappingProxyType(copy.deepcopy(self._data))

    def record(
        self, metric_name: str, value: Any, tags: Optional[Dict[str, Any]] = None
    ) -> None:
        """Record a metric value with optional tags.

        This is a more explicit alternative to ``ctx.metrics.add()``.

        Parameters
        ----------
        metric_name:
            Name of the metric to record.
        value:
            The metric value.
        tags:
            Optional dictionary of tags for categorization and filtering.

        Example
        -------
        >>> ctx.record("loss", 0.5, tags={"epoch": 1, "split": "train"})
        """
        self.metrics.add(metric_name, value, tags)


class LoggingContext(FrozenContext):
    """
    A FrozenContext proxy that records every key read and emits DEBUG lines.

    Parameters
    ----------
    ctx:
        The original, immutable context created by the Experiment runner.
    logger:
        The logger to use for DEBUG instrumentation.
    """

    # We purposely do **not** call super().__init__ so we avoid copying data.
    def __init__(self, ctx: FrozenContext, logger: Optional[logging.Logger] = None):
        # Store a reference to the wrapped context
        object.__setattr__(self, "_inner", ctx)

        # Expose the same public attributes the pipeline expects
        object.__setattr__(self, "metrics", ctx.metrics)
        object.__setattr__(self, "artifacts", ctx.artifacts)
        object.__setattr__(self, "logger", logger or ctx.logger)

        # Read log
        object.__setattr__(self, "reads", cast(Dict[str, Any], {}))

    # --------------- proxy helpers --------------- #
    def _log_read(self, key: str, value: Any) -> None:  # noqa: D401
        self.reads[key] = value
        self.logger.debug("Read %s -> %s", key, value)

    # --------------- Mapping interface --------------- #
    def __getitem__(self, key: str) -> Any:
        value = self._inner[key]
        self._log_read(key, value)
        return value

    def __setitem__(self, key: str, value: Any) -> None:
        # Delegate mutation protection to the real context
        self._inner[key] = value

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        if key in self._inner.as_dict():
            value = self._inner.get(key)
            self._log_read(key, value)
            return value
        return default

    def add(self, key: str, value: Any) -> None:
        self._inner.add(key, value)

    # --------------- inspection helpers --------------- #
    def as_dict(self) -> Mapping[str, Any]:
        # Return a *read-only* view of current data, exactly like FrozenContext
        return self._inner.as_dict()

    # --------------- fallback for anything else --------------- #
    def __getattr__(self, name: str):
        # forward unknown attributes to the wrapped context
        return getattr(self._inner, name)
