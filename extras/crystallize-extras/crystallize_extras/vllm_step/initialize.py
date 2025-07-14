from typing import Any, Dict

from crystallize import pipeline_step
from crystallize.core.context import FrozenContext

try:
    from vllm import LLM
except ImportError:  # pragma: no cover - optional dependency
    LLM = None


@pipeline_step(cacheable=False)  # Caching an engine object is not recommended
def initialize_llm_engine(
    data: Any,
    ctx: FrozenContext,
    *,
    engine_options: Dict[str, Any],
    context_key: str = "llm_engine",
):
    """Initializes a vLLM engine and places it in the context."""
    if LLM is None:
        raise ImportError(
            "The 'vllm' package is required. Please install with: pip install crystallize-extras[vllm]"
        )

    if context_key not in ctx.as_dict():
        engine = LLM(**engine_options)
        ctx.add(context_key, engine)

    return data
