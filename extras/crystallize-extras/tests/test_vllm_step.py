import pytest
from crystallize_extras.vllm_step.initialize import initialize_llm_engine

from crystallize.utils.context import FrozenContext


class DummyLLM:
    def __init__(self, **kwargs) -> None:
        self.options = kwargs


def test_initialize_llm_engine_adds_engine(monkeypatch) -> None:
    monkeypatch.setattr(
        "crystallize_extras.vllm_step.initialize.LLM",
        DummyLLM,
    )
    ctx = FrozenContext({})
    step = initialize_llm_engine(engine_options={"model": "llama"})
    step.setup(ctx)
    assert "llm_engine" in ctx.as_dict()
    handle = ctx.as_dict()["llm_engine"]
    assert callable(handle)
    engine = handle(ctx)
    assert isinstance(engine, DummyLLM)
    assert engine.options == {"model": "llama"}
    result = step(None, ctx)
    assert result is None
    step.teardown(ctx)


def test_initialize_llm_engine_missing_dependency(monkeypatch) -> None:
    from crystallize_extras import vllm_step

    monkeypatch.setattr(vllm_step.initialize, "LLM", None)
    ctx = FrozenContext({})
    step = vllm_step.initialize.initialize_llm_engine(engine_options={})
    step.setup(ctx)
    handle = ctx.as_dict()["llm_engine"]
    with pytest.raises(ImportError):
        _ = handle(ctx)
