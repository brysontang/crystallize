from crystallize import hypothesis, pipeline_step, treatment
from crystallize.core.context import FrozenContext
from crystallize.core.pipeline import Pipeline
from crystallize.core.stat_test import StatisticalTest


@pipeline_step()
def add(data, ctx, value=1):
    return data + value


@pipeline_step()
def metrics(data, ctx):
    return {"result": data}


class DummyStatTest(StatisticalTest):
    def run(self, baseline, treatment, *, alpha: float = 0.05):
        return {"p_value": 0.01, "significant": True}


@treatment("inc")
def inc_treatment(ctx):
    ctx["increment"] = 1


@hypothesis(metric="result", statistical_test=DummyStatTest(), direction="increase")
def result_hypo():
    pass


def test_pipeline_step_decorator():
    pipeline = Pipeline([add(value=2), metrics()])
    ctx = FrozenContext({})
    result = pipeline.run(3, ctx)
    assert result == {"result": 5}


def test_treatment_decorator():
    t = inc_treatment()
    ctx = FrozenContext({})
    t.apply(ctx)
    assert ctx["increment"] == 1


def test_hypothesis_decorator():
    h = result_hypo()
    res = h.verify({"result": [1, 2]}, {"result": [3, 4]})
    assert res["accepted"] is True
