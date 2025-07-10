from typing import Any, Mapping, Optional
from types import MappingProxyType

class ContextMutationError(Exception):
    """Raised when attempting to mutate an existing key in FrozenContext."""
    pass

class FrozenContext:
    """Immutable execution context with safe mutation helpers."""

    def __init__(self, initial: Mapping[str, Any]):
        self._data = dict(initial)

    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def __setitem__(self, key: str, value: Any):
        if key in self._data:
            raise ContextMutationError(f"Cannot mutate existing key: '{key}'")
        self._data[key] = value

    def add(self, key: str, value: Any) -> None:
        """Alias for ``__setitem__`` providing a clearer API."""
        self.__setitem__(key, value)

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """Return the value for ``key`` if present else ``default``."""
        return self._data.get(key, default)

    def as_dict(self) -> Mapping[str, Any]:
        return MappingProxyType(self._data)
