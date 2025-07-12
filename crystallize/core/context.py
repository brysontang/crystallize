from collections import defaultdict
from types import MappingProxyType
from typing import Any, DefaultDict, List, Mapping, Optional, Tuple
import copy


class ContextMutationError(Exception):
    """Raised when attempting to mutate an existing key in FrozenContext."""

    pass


class FrozenMetrics:
    """Immutable mapping of metric lists with safe append."""

    def __init__(self) -> None:
        self._metrics: DefaultDict[str, List[Any]] = defaultdict(list)

    def __getitem__(self, key: str) -> Tuple[Any, ...]:
        return tuple(self._metrics[key])

    def add(self, key: str, value: Any) -> None:
        self._metrics[key].append(value)

    def as_dict(self) -> Mapping[str, Tuple[Any, ...]]:
        return MappingProxyType({k: tuple(v) for k, v in self._metrics.items()})


class FrozenContext:
    """Immutable execution context with safe mutation helpers."""

    def __init__(self, initial: Mapping[str, Any]) -> None:
        self._data = copy.deepcopy(dict(initial))
        self.metrics = FrozenMetrics()

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
