import pytest
from crystallize.utils.context import FrozenContext
from crystallize.utils.injection import inject_from_ctx
from crystallize import pipeline_step
import random


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

def test_inject_missing_ctx():
    @inject_from_ctx
    def fn(data: int, ctx: FrozenContext, *, val: int = 0) -> int:
        return data + val

    with pytest.raises(TypeError):
        fn(1)


def test_inject_bad_ctx_type():
    @inject_from_ctx
    def fn(data: int, ctx: FrozenContext, *, val: int = 0) -> int:
        return data + val

    with pytest.raises(TypeError):
        fn(1, ctx={})


def test_inject_factory_callable():
    @inject_from_ctx
    def compute(data: int, ctx: FrozenContext, *, rng) -> int:
        return data + rng.randint(0, 1)

    ctx = FrozenContext({"rng": lambda ctx: random.Random(0)})
    assert compute(1, ctx) in {1, 2}
