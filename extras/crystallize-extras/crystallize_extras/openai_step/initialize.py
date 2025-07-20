from __future__ import annotations

from typing import Any, Dict

from crystallize.core.context import FrozenContext
from crystallize.core.pipeline_step import PipelineStep
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


class InitializeOpenaiClient(PipelineStep):
    """Pipeline step that initializes an OpenAI client during setup."""

    cacheable = False

    def __init__(
        self, *, client_options: Dict[str, Any], context_key: str = "openai_client"
    ) -> None:
        self.client_options = client_options
        self.context_key = context_key

    def __call__(
        self, data: Any, ctx: FrozenContext
    ) -> Any:  # pragma: no cover - passthrough
        return data

    @property
    def params(self) -> dict:
        return {"client_options": self.client_options, "context_key": self.context_key}

    def setup(self, ctx: FrozenContext) -> None:
        factory = resource_factory(
            lambda ctx, opts=self.client_options: _create_openai_client(opts),
            key=self.step_hash,
        )
        ctx.add(self.context_key, factory)

    def teardown(
        self, ctx: FrozenContext
    ) -> None:  # pragma: no cover - handled by exit
        pass


def initialize_openai_client(
    *, client_options: Dict[str, Any], context_key: str = "openai_client"
) -> InitializeOpenaiClient:
    """Factory function returning :class:`InitializeOpenaiClient`."""
    return InitializeOpenaiClient(
        client_options=client_options, context_key=context_key
    )
