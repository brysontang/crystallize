from __future__ import annotations

from functools import partial
from typing import Any

from crystallize.utils.context import FrozenContext
from crystallize.pipelines.pipeline_step import PipelineStep
from crystallize import resource_factory

try:
    from ollama import Client
except ImportError:  # pragma: no cover - optional dependency
    Client = None


def _create_ollama_client(host: str) -> Client:
    """Top-level factory function for pickling."""
    if Client is None:
        raise ImportError(
            "The 'ollama' package is required. Please install with: pip install crystallize-extras[ollama]"
        )
    return Client(host=host)


class OllamaClientFactory:
    """A picklable callable that creates an Ollama client."""

    def __init__(self, host: str):
        self.host = host

    def __call__(self, ctx: FrozenContext) -> Client:
        return _create_ollama_client(self.host)


class InitializeOllamaClient(PipelineStep):
    """Pipeline step that initializes an Ollama client during setup."""

    cacheable = False

    def __init__(self, *, host: str, context_key: str = "ollama_client") -> None:
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
        client_factory_instance = OllamaClientFactory(self.host)
        factory = resource_factory(
            client_factory_instance,
            key=self.step_hash,
        )
        ctx.add(self.context_key, factory)

    def teardown(
        self, ctx: FrozenContext
    ) -> None:  # pragma: no cover - handled by exit
        pass


def initialize_ollama_client(
    *, host: str, context_key: str = "ollama_client"
) -> InitializeOllamaClient:
    """Factory function returning :class:`InitializeOllamaClient`."""
    return InitializeOllamaClient(host=host, context_key=context_key)
