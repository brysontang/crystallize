from crystallize import (
    data_source,
    hypothesis,
    pipeline,
    pipeline_step,
    statistical_test,
    treatment,
)
import pytest
from crystallize.core.context import ContextMutationError, FrozenContext


@pipeline_step()
def add(data, ctx, value=1):
    return data + value


@pipeline_step()
def metrics(data, ctx):
    return {"result": data}


@data_source
def dummy_source(ctx, value=1):
    return value


@statistical_test
def always_significant(baseline, treatment, *, alpha: float = 0.05):
    return {"p_value": 0.01, "significant": True}


@treatment("inc")
def inc_treatment(ctx):
    ctx.add("increment", 1)


h = hypothesis(
    metric="result", statistical_test=always_significant(), direction="increase"
)


def test_pipeline_factory_and_decorators():
    src = dummy_source(value=3)
    pl = pipeline(add(value=2), metrics())
    ctx = FrozenContext({})
    data = src.fetch(ctx)
    result = pl.run(data, ctx)
    assert result == {"result": 5}


def test_treatment_decorator():
    t = inc_treatment()
    ctx = FrozenContext({})
    t.apply(ctx)
    assert ctx.get("increment") == 1


def test_treatment_factory_with_mapping():
    t = treatment("inc_map", {"increment": 2})
    ctx = FrozenContext({})
    t.apply(ctx)
    assert ctx.get("increment") == 2


def test_treatment_multi_key_mapping():
    t = treatment("multi", {"key1": 1, "key2": 2})
    ctx = FrozenContext({})
    t.apply(ctx)
    assert ctx.get("key1") == 1 and ctx.get("key2") == 2


def test_treatment_mapping_existing_key_raises():
    t = treatment("conflict", {"key1": 1})
    ctx = FrozenContext({"key1": 0})
    with pytest.raises(ContextMutationError):
        t.apply(ctx)


def test_hypothesis_factory():
    res = h.verify({"result": [1, 2]}, {"result": [3, 4]})
    assert res["accepted"] is True


@data_source
def required_source(ctx, value):
    return value


@statistical_test
def dummy_test(baseline, treatment, *, threshold):
    return {"p_value": 0.5, "significant": True}


def test_factories_missing_params():
    with pytest.raises(TypeError):
        required_source()
    with pytest.raises(TypeError):
        dummy_test()
