import pytest
from crystallize_extras.ollama_step.initialize import initialize_ollama_client

from crystallize.utils.context import FrozenContext


class DummyClient:
    def __init__(self, *, host: str) -> None:
        self.host = host


def test_initialize_ollama_client_adds_client(monkeypatch) -> None:
    monkeypatch.setattr(
        "crystallize_extras.ollama_step.initialize.Client",
        DummyClient,
    )
    ctx = FrozenContext({})
    step = initialize_ollama_client(host="http://localhost")
    step.setup(ctx)
    assert "ollama_client" in ctx.as_dict()
    handle = ctx.as_dict()["ollama_client"]
    assert callable(handle)
    client = handle(ctx)
    assert isinstance(client, DummyClient)
    assert client.host == "http://localhost"
    result = step(None, ctx)
    assert result is None
    step.teardown(ctx)


def test_initialize_ollama_client_missing_dependency(monkeypatch) -> None:
    from crystallize_extras import ollama_step

    monkeypatch.setattr(ollama_step.initialize, "Client", None)
    ctx = FrozenContext({})
    step = ollama_step.initialize.initialize_ollama_client(host="http://loc")
    step.setup(ctx)
    handle = ctx.as_dict()["ollama_client"]
    with pytest.raises(ImportError):
        _ = handle(ctx)
