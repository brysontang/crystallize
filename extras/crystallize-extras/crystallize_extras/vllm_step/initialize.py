from __future__ import annotations

from functools import partial
from typing import Any, Dict

from crystallize.utils.context import FrozenContext
from crystallize.pipelines.pipeline_step import PipelineStep
from crystallize import resource_factory

try:
    from vllm import LLM
except ImportError:  # pragma: no cover - optional dependency
    LLM = None


def _create_llm_engine(engine_options: Dict[str, Any]) -> LLM:
    """Top-level factory function for pickling."""
    if LLM is None:
        raise ImportError(
            "The 'vllm' package is required. Please install with: pip install crystallize-extras[vllm]"
        )
    return LLM(**engine_options)


class InitializeLlmEngine(PipelineStep):
    """Pipeline step that initializes a vLLM engine during setup."""

    cacheable = False

    def __init__(self, *, engine_options: Dict[str, Any], context_key: str = "llm_engine") -> None:
        self.engine_options = engine_options
        self.context_key = context_key

    def __call__(self, data: Any, ctx: FrozenContext) -> Any:  # pragma: no cover - passthrough
        return data

    @property
    def params(self) -> dict:
        return {"engine_options": self.engine_options, "context_key": self.context_key}

    def setup(self, ctx: FrozenContext) -> None:
        factory = resource_factory(
            lambda ctx, opts=self.engine_options: _create_llm_engine(opts),
            key=self.step_hash,
        )
        ctx.add(self.context_key, factory)

    def teardown(self, ctx: FrozenContext) -> None:  # pragma: no cover - handled by exit
        pass


def initialize_llm_engine(*, engine_options: Dict[str, Any], context_key: str = "llm_engine") -> InitializeLlmEngine:
    """Factory function returning :class:`InitializeLlmEngine`."""
    return InitializeLlmEngine(engine_options=engine_options, context_key=context_key)
