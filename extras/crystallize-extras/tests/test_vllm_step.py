import pytest
from crystallize_extras.vllm_step.initialize import initialize_llm_engine

from crystallize.core.context import FrozenContext


class DummyLLM:
    def __init__(self, **kwargs):
        self.options = kwargs


def test_initialize_llm_engine_adds_engine(monkeypatch):
    monkeypatch.setattr(
        "crystallize_extras.vllm_step.initialize.LLM",
        DummyLLM,
    )
    ctx = FrozenContext({})
    step = initialize_llm_engine(engine_options={"model": "llama"})
    step.setup(ctx)
    assert "llm_engine" in ctx.as_dict()
    assert isinstance(ctx.as_dict()["llm_engine"], DummyLLM)
    assert ctx.as_dict()["llm_engine"].options == {"model": "llama"}
    result = step(None, ctx)
    assert result is None
    step.teardown(ctx)
    assert not hasattr(step, "engine")

def test_initialize_llm_engine_missing_dependency(monkeypatch):
    from crystallize_extras import vllm_step

    monkeypatch.setattr(vllm_step.initialize, "LLM", None)
    ctx = FrozenContext({})
    step = vllm_step.initialize.initialize_llm_engine(engine_options={})
    with pytest.raises(ImportError):
        step.setup(ctx)
