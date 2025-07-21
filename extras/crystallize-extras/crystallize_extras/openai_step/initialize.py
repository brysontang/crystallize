from __future__ import annotations
from typing import Any, Dict

from crystallize.utils.context import FrozenContext
from crystallize.pipelines.pipeline_step import PipelineStep
from crystallize import resource_factory

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - optional dependency
    OpenAI = None


def _create_openai_client(client_options: Dict[str, Any]) -> OpenAI:
    """Top-level factory function for pickling."""
    if OpenAI is None:
        raise ImportError(
            "The 'openai' package is required. Please install with: pip install crystallize-extras[openai]"
        )
    return OpenAI(**client_options)


# FIX 1: Create a top-level, picklable class to hold the options
class OpenAiClientFactory:
    """A picklable callable that creates an OpenAI client."""

    def __init__(self, client_options: Dict[str, Any]):
        self.client_options = client_options

    def __call__(self, ctx: FrozenContext) -> OpenAI:
        # The logic from the lambda now lives here
        return _create_openai_client(self.client_options)


class InitializeOpenaiClient(PipelineStep):
    """Pipeline step that initializes an OpenAI client during setup."""

    cacheable = False

    def __init__(
        self, *, client_options: Dict[str, Any], context_key: str = "openai_client"
    ) -> None:
        self.client_options = client_options
        self.context_key = context_key

    def __call__(self, data: Any, ctx: FrozenContext) -> Any:
        return data

    @property
    def params(self) -> dict:
        return {"client_options": self.client_options, "context_key": self.context_key}

    def setup(self, ctx: FrozenContext) -> None:
        # FIX 2: Instantiate our new picklable factory class
        client_factory_instance = OpenAiClientFactory(self.client_options)

        # Pass the picklable instance to resource_factory
        factory = resource_factory(
            client_factory_instance,
            key=self.step_hash,
        )
        ctx.add(self.context_key, factory)


def initialize_openai_client(
    *, client_options: Dict[str, Any], context_key: str = "openai_client"
) -> InitializeOpenaiClient:
    """Factory function returning :class:`InitializeOpenaiClient`."""
    return InitializeOpenaiClient(
        client_options=client_options, context_key=context_key
    )
