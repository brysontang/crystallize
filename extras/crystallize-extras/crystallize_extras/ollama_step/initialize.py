from typing import Any

from crystallize.core.context import FrozenContext
from crystallize.core.pipeline_step import PipelineStep

try:
    from ollama import Client
except ImportError:  # pragma: no cover - optional dependency
    Client = None


class InitializeOllamaClient(PipelineStep):
    """Pipeline step that initializes an Ollama client during setup."""

    cacheable = False

    def __init__(self, *, base_url: str, context_key: str = "ollama_client") -> None:
        self.base_url = base_url
        self.context_key = context_key

    def __call__(self, data: Any, ctx: FrozenContext) -> Any:
        return data

    @property
    def params(self) -> dict:
        return {"base_url": self.base_url, "context_key": self.context_key}

    def setup(self, ctx: FrozenContext) -> None:
        if Client is None:
            raise ImportError(
                "The 'ollama' package is required. Please install with: pip install crystallize-extras[ollama]"
            )
        self.client = Client(base_url=self.base_url)
        ctx.add(self.context_key, self.client)

    def teardown(self, ctx: FrozenContext) -> None:
        if hasattr(self, "client"):
            del self.client


def initialize_ollama_client(
    *, base_url: str, context_key: str = "ollama_client"
) -> InitializeOllamaClient:
    """Factory function returning :class:`InitializeOllamaClient`."""
    return InitializeOllamaClient(base_url=base_url, context_key=context_key)
