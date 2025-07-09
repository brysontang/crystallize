from typing import Any, Mapping
from types import MappingProxyType

class ContextMutationError(Exception):
    """Raised when attempting to mutate an existing key in FrozenContext."""
    pass

class FrozenContext:
    def __init__(self, initial: Mapping[str, Any]):
        self._data = dict(initial)

    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def __setitem__(self, key: str, value: Any):
        if key in self._data:
            raise ContextMutationError(f"Cannot mutate existing key: '{key}'")
        self._data[key] = value

    def as_dict(self) -> Mapping[str, Any]:
        return MappingProxyType(self._data)
