from crystallize import (
    data_source,
    hypothesis,
    pipeline,
    pipeline_step,
    statistical_test,
    treatment,
)
from crystallize.core.context import FrozenContext


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
    ctx["increment"] = 1


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
    assert ctx["increment"] == 1


def test_hypothesis_factory():
    res = h.verify({"result": [1, 2]}, {"result": [3, 4]})
    assert res["accepted"] is True
