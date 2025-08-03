from __future__ import annotations

from typing import Any

from crystallize import resource_factory, FrozenContext, PipelineStep

try:
    from ollama import AsyncClient
except ImportError:  # pragma: no cover - optional dependency
    AsyncClient = None


def _create_async_ollama_client(host: str) -> AsyncClient:
    """Top-level factory function for pickling."""
    if AsyncClient is None:
        raise ImportError(
            "The 'ollama' package is required. Please install with: pip install --upgrade --pre crystallize-extras[ollama]"
        )
    return AsyncClient(host=host)


class AsyncOllamaClientFactory:
    """A picklable callable that creates an AsyncOllama client."""

    def __init__(self, host: str):
        self.host = host

    def __call__(self, ctx: FrozenContext) -> AsyncClient:
        return _create_async_ollama_client(self.host)


class InitializeAsyncOllamaClient(PipelineStep):
    """Pipeline step that initializes an AsyncOllama client during setup."""

    cacheable = False

    def __init__(self, *, host: str, context_key: str = "async_ollama_client") -> None:
        self.host = host
        self.context_key = context_key

    def __call__(
        self, data: Any, ctx: FrozenContext
    ) -> Any:  # pragma: no cover - passthrough
        return data

    @property
    def params(self) -> dict:
        return {"host": self.host, "context_key": self.context_key}

    def setup(self, ctx: FrozenContext) -> None:
        client_factory_instance = AsyncOllamaClientFactory(self.host)
        factory = resource_factory(
            client_factory_instance,
            key=self.step_hash,
        )
        ctx.add(self.context_key, factory)


def initialize_async_ollama_client(
    *, host: str, context_key: str = "async_ollama_client"
) -> InitializeAsyncOllamaClient:
    """Factory function returning :class:`InitializeAsyncOllamaClient`."""
    return InitializeAsyncOllamaClient(host=host, context_key=context_key)
