from crystallize.core.context import FrozenContext

from crystallize_extras.vllm_step.initialize import initialize_llm_engine


class DummyLLM:
    def __init__(self, **kwargs):
        self.options = kwargs


def test_initialize_llm_engine_adds_engine(monkeypatch):
    monkeypatch.setattr(
        'crystallize_extras.vllm_step.initialize.LLM',
        DummyLLM,
    )
    ctx = FrozenContext({})
    step = initialize_llm_engine(engine_options={'model': 'llama'})
    result = step(None, ctx)
    assert result is None
    assert 'llm_engine' in ctx.as_dict()
    assert isinstance(ctx.as_dict()['llm_engine'], DummyLLM)
    assert ctx.as_dict()['llm_engine'].options == {'model': 'llama'}

    # Calling again should not create a new engine
    step(None, ctx)
    assert ctx.as_dict()['llm_engine'].options == {'model': 'llama'}
