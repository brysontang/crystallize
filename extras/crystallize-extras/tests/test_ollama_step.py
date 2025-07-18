import pytest
from crystallize_extras.ollama_step.initialize import initialize_ollama_client

from crystallize.core.context import FrozenContext


class DummyClient:
    def __init__(self, *, host: str):
        self.host = host


def test_initialize_ollama_client_adds_client(monkeypatch):
    monkeypatch.setattr(
        "crystallize_extras.ollama_step.initialize.Client",
        DummyClient,
    )
    ctx = FrozenContext({})
    step = initialize_ollama_client(host="http://localhost")
    step.setup(ctx)
    assert "ollama_client" in ctx.as_dict()
    assert isinstance(ctx.as_dict()["ollama_client"], DummyClient)
    assert ctx.as_dict()["ollama_client"].host == "http://localhost"
    result = step(None, ctx)
    assert result is None
    step.teardown(ctx)
    assert not hasattr(step, "client")


def test_initialize_ollama_client_missing_dependency(monkeypatch):
    from crystallize_extras import ollama_step

    monkeypatch.setattr(ollama_step.initialize, "Client", None)
    ctx = FrozenContext({})
    step = ollama_step.initialize.initialize_ollama_client(host="http://loc")
    with pytest.raises(ImportError):
        step.setup(ctx)
