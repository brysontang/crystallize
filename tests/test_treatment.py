import pytest
from crystallize.core.context import FrozenContext, ContextMutationError
from crystallize.core.treatment import Treatment
from crystallize.core import treatment


def test_treatment_mapping_apply():
    t = Treatment("inc", {"val": 1})
    ctx = FrozenContext({})
    t.apply(ctx)
    assert ctx.get("val") == 1


def test_treatment_callable_apply():
    def add_two(ctx: FrozenContext) -> None:
        ctx.add("val", 2)

    t = Treatment("two", add_two)
    ctx = FrozenContext({})
    t.apply(ctx)
    assert ctx.get("val") == 2


def test_treatment_mutation_error():
    t = Treatment("err", {"x": 1})
    ctx = FrozenContext({"x": 0})
    with pytest.raises(ContextMutationError):
        t.apply(ctx)


@treatment("decor")
def dec(ctx: FrozenContext) -> None:
    ctx.add("flag", True)


def test_treatment_decorator_factory():
    tr = dec()
    ctx = FrozenContext({})
    tr.apply(ctx)
    assert ctx.get("flag") is True
