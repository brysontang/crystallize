from crystallize.core.context import FrozenContext
from crystallize.core.injection import inject_from_ctx
from crystallize.core import pipeline_step


def test_inject_from_ctx_direct():
    @inject_from_ctx
    def add(data: int, ctx: FrozenContext, *, delta: int = 0) -> int:
        return data + delta

    ctx = FrozenContext({"delta": 5})
    assert add(1, ctx) == 6


def test_pipeline_step_inject():
    @pipeline_step()
    def add_delta(data: int, ctx: FrozenContext, *, delta: int = 0) -> int:
        return data + delta

    step = add_delta()
    ctx = FrozenContext({"delta": 3})
    assert step(2, ctx) == 5
