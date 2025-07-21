import pytest
from crystallize_extras.openai_step.initialize import initialize_openai_client

from crystallize.utils.context import FrozenContext


class DummyClient:
    def __init__(self, *, base_url: str) -> None:
        self.base_url = base_url


def test_initialize_openai_client_adds_client(monkeypatch) -> None:
    monkeypatch.setattr(
        "crystallize_extras.openai_step.initialize.OpenAI",
        DummyClient,
    )
    ctx = FrozenContext({})
    step = initialize_openai_client(client_options={"base_url": "http://localhost"})
    step.setup(ctx)
    assert "openai_client" in ctx.as_dict()
    handle = ctx.as_dict()["openai_client"]
    assert callable(handle)
    client = handle(ctx)
    assert isinstance(client, DummyClient)
    assert client.base_url == "http://localhost"
    result = step(None, ctx)
    assert result is None
    step.teardown(ctx)
