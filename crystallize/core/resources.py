from __future__ import annotations

import threading
from typing import Any, Callable, Dict


_local_storage = threading.local()


class ResourceHandle:
    """A picklable handle for a resource that should be instantiated once per process."""

    def __init__(self, factory: Callable[[], Any], resource_id: str) -> None:
        self._factory = factory
        self._resource_id = resource_id

    @property
    def resource(self) -> Any:
        """Get or create the resource instance for the current thread/process."""
        if not hasattr(_local_storage, "resource_cache"):
            _local_storage.resource_cache = {}

        if self._resource_id not in _local_storage.resource_cache:
            _local_storage.resource_cache[self._resource_id] = self._factory()

        return _local_storage.resource_cache[self._resource_id]

    def __getstate__(self) -> Dict[str, Any]:
        """Prepare the handle for pickling by storing the factory and ID."""
        return {"factory": self._factory, "resource_id": self._resource_id}

    def __setstate__(self, state: Dict[str, Any]) -> None:
        """Restore the handle after unpickling."""
        self._factory = state["factory"]
        self._resource_id = state["resource_id"]
