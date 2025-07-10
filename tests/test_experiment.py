from crystallize.core.context import FrozenContext
from crystallize.core.datasource import DataSource
from crystallize.core.experiment import Experiment
from crystallize.core.hypothesis import Hypothesis
from crystallize.core.pipeline import Pipeline
from crystallize.core.pipeline_step import PipelineStep
from crystallize.core.stat_test import StatisticalTest
from crystallize.core.treatment import Treatment


class DummyDataSource(DataSource):
    def fetch(self, ctx: FrozenContext):
        # return replicate id plus any increment in ctx
        return ctx["replicate"] + ctx.as_dict().get("increment", 0)


class PassStep(PipelineStep):
    def __call__(self, data, ctx):
        return {"metric": data}

    @property
    def params(self):
        return {}


class AlwaysSignificant(StatisticalTest):
    def run(self, baseline, treatment, *, alpha: float = 0.05):
        return {"p_value": 0.01, "significant": True}


def test_experiment_run_basic():
    pipeline = Pipeline([PassStep()])
    datasource = DummyDataSource()
    hypothesis = Hypothesis(
        metric="metric", direction="increase", statistical_test=AlwaysSignificant()
    )
    treatment = Treatment("treat", lambda ctx: ctx.__setitem__("increment", 1))

    experiment = Experiment(
        datasource=datasource,
        pipeline=pipeline,
        treatments=[treatment],
        hypotheses=[hypothesis],
        replicates=2,
    )
    result = experiment.run()
    assert result.metrics["baseline"]["metric"] == [0, 1]
    assert result.metrics["treat"]["metric"] == [1, 2]
    assert result.metrics["hypotheses"][hypothesis.name]["treat"]["accepted"] is True
    assert result.errors == {}


def test_experiment_run_multiple_treatments():
    pipeline = Pipeline([PassStep()])
    datasource = DummyDataSource()
    hypothesis = Hypothesis(
        metric="metric", direction="increase", statistical_test=AlwaysSignificant()
    )
    treatment1 = Treatment("treat1", lambda ctx: ctx.__setitem__("increment", 1))
    treatment2 = Treatment("treat2", lambda ctx: ctx.__setitem__("increment", 2))
    experiment = Experiment(
        datasource=datasource,
        pipeline=pipeline,
        treatments=[treatment1, treatment2],
        hypotheses=[hypothesis],
        replicates=2,
    )
    result = experiment.run()
    assert result.metrics["baseline"]["metric"] == [0, 1]
    assert result.metrics["treat1"]["metric"] == [1, 2]
    assert result.metrics["treat2"]["metric"] == [2, 3]
    assert result.metrics["hypotheses"][hypothesis.name]["treat1"]["accepted"] is True
    assert result.metrics["hypotheses"][hypothesis.name]["treat2"]["accepted"] is True
