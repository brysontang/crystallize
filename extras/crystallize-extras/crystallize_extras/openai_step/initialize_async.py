# crystallize/extras/crystallize-extras/crystallize_extras/openai_step/initialize_async.py
from __future__ import annotations
from typing import Any, Dict

from crystallize import resource_factory, FrozenContext, PipelineStep

try:
    from openai import AsyncOpenAI
except ImportError:  # pragma: no cover - optional dependency
    AsyncOpenAI = None


def _create_async_openai_client(client_options: Dict[str, Any]) -> AsyncOpenAI:
    """Top-level factory function for pickling."""
    if AsyncOpenAI is None:
        raise ImportError(
            "The 'openai' package is required. Please install with: pip install --upgrade --pre crystallize-extras[openai]"
        )
    return AsyncOpenAI(**client_options)


class AsyncOpenAiClientFactory:
    """A picklable callable that creates an AsyncOpenAI client."""

    def __init__(self, client_options: Dict[str, Any]):
        self.client_options = client_options

    def __call__(self, ctx: FrozenContext) -> AsyncOpenAI:
        return _create_async_openai_client(self.client_options)


class InitializeAsyncOpenaiClient(PipelineStep):
    """Pipeline step that initializes an AsyncOpenAI client during setup."""

    cacheable = False

    def __init__(
        self,
        *,
        client_options: Dict[str, Any],
        context_key: str = "async_openai_client",
    ) -> None:
        self.client_options = client_options
        self.context_key = context_key

    def __call__(self, data: Any, ctx: FrozenContext) -> Any:
        return data

    @property
    def params(self) -> dict:
        return {"client_options": self.client_options, "context_key": self.context_key}

    def setup(self, ctx: FrozenContext) -> None:
        client_factory_instance = AsyncOpenAiClientFactory(self.client_options)
        factory = resource_factory(
            client_factory_instance,
            key=self.step_hash,
        )
        ctx.add(self.context_key, factory)


def initialize_async_openai_client(
    *, client_options: Dict[str, Any], context_key: str = "async_openai_client"
) -> InitializeAsyncOpenaiClient:
    """Factory function returning :class:`InitializeAsyncOpenaiClient`."""
    return InitializeAsyncOpenaiClient(
        client_options=client_options, context_key=context_key
    )
