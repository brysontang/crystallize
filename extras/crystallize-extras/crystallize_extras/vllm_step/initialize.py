from typing import Any, Dict

from crystallize.core.context import FrozenContext
from crystallize.core.pipeline_step import PipelineStep

try:
    from vllm import LLM
except ImportError:  # pragma: no cover - optional dependency
    LLM = None


class InitializeLlmEngine(PipelineStep):
    """Pipeline step that initializes a vLLM engine during setup."""

    cacheable = False

    def __init__(
        self, *, engine_options: Dict[str, Any], context_key: str = "llm_engine"
    ) -> None:
        self.engine_options = engine_options
        self.context_key = context_key

    def __call__(self, data: Any, ctx: FrozenContext) -> Any:
        return data

    @property
    def params(self) -> dict:
        return {"engine_options": self.engine_options, "context_key": self.context_key}

    def setup(self, ctx: FrozenContext) -> None:
        if LLM is None:
            raise ImportError(
                "The 'vllm' package is required. Please install with: pip install crystallize-extras[vllm]"
            )
        self.engine = LLM(**self.engine_options)
        ctx.add(self.context_key, self.engine)

    def teardown(self, ctx: FrozenContext) -> None:
        if hasattr(self, "engine"):
            del self.engine


def initialize_llm_engine(
    *, engine_options: Dict[str, Any], context_key: str = "llm_engine"
) -> InitializeLlmEngine:
    """Factory function returning :class:`InitializeLlmEngine`."""
    return InitializeLlmEngine(engine_options=engine_options, context_key=context_key)
