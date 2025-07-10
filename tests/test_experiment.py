import pytest

from crystallize.core.context import FrozenContext
from crystallize.core.datasource import DataSource
from crystallize.core.experiment import Experiment
from crystallize.core.hypothesis import Hypothesis
from crystallize.core.pipeline import Pipeline
from crystallize.core.pipeline_step import PipelineStep, exit_step
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
    treatment = Treatment("treat", {"increment": 1})

    experiment = Experiment(
        datasource=datasource,
        pipeline=pipeline,
        treatments=[treatment],
        hypotheses=[hypothesis],
        replicates=2,
    )
    experiment.validate()
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
    treatment1 = Treatment("treat1", {"increment": 1})
    treatment2 = Treatment("treat2", {"increment": 2})
    experiment = Experiment(
        datasource=datasource,
        pipeline=pipeline,
        treatments=[treatment1, treatment2],
        hypotheses=[hypothesis],
        replicates=2,
    )
    experiment.validate()
    result = experiment.run()
    assert result.metrics["baseline"]["metric"] == [0, 1]
    assert result.metrics["treat1"]["metric"] == [1, 2]
    assert result.metrics["treat2"]["metric"] == [2, 3]
    assert result.metrics["hypotheses"][hypothesis.name]["treat1"]["accepted"] is True
    assert result.metrics["hypotheses"][hypothesis.name]["treat2"]["accepted"] is True


def test_experiment_run_baseline_only():
    pipeline = Pipeline([PassStep()])
    datasource = DummyDataSource()

    experiment = Experiment(
        datasource=datasource,
        pipeline=pipeline,
    )
    experiment.validate()
    result = experiment.run()
    assert result.metrics["baseline"]["metric"] == [0]
    assert result.metrics["hypotheses"] == {}


def test_experiment_run_treatments_no_hypotheses():
    pipeline = Pipeline([PassStep()])
    datasource = DummyDataSource()
    treatment = Treatment("treat", {"increment": 1})

    experiment = Experiment(
        datasource=datasource,
        pipeline=pipeline,
        treatments=[treatment],
    )
    experiment.validate()
    result = experiment.run()
    assert result.metrics["treat"]["metric"] == [1]


def test_experiment_run_hypothesis_without_treatments_raises():
    pipeline = Pipeline([PassStep()])
    datasource = DummyDataSource()
    hypothesis = Hypothesis(
        metric="metric",
        direction="increase",
        statistical_test=AlwaysSignificant(),
    )

    experiment = Experiment(
        datasource=datasource,
        pipeline=pipeline,
        hypotheses=[hypothesis],
    )
    with pytest.raises(ValueError):
        experiment.validate()


class IdentityStep(PipelineStep):
    def __call__(self, data, ctx):
        return data

    @property
    def params(self):
        return {}


def test_experiment_apply_with_exit_step():
    pipeline = Pipeline([exit_step(IdentityStep()), PassStep()])
    datasource = DummyDataSource()
    experiment = Experiment(datasource=datasource, pipeline=pipeline)
    experiment.validate()
    output = experiment.apply(data=5)
    assert output == 5


def test_experiment_requires_validation():
    pipeline = Pipeline([PassStep()])
    datasource = DummyDataSource()
    experiment = Experiment(datasource=datasource, pipeline=pipeline)
    with pytest.raises(RuntimeError):
        experiment.run()
    with pytest.raises(RuntimeError):
        experiment.apply(data=1)


def test_experiment_builder_chaining():
    experiment = (
        Experiment()
        .with_datasource(DummyDataSource())
        .with_pipeline(Pipeline([PassStep()]))
        .with_treatments([Treatment("t", {"increment": 1})])
        .with_hypotheses(
            [
                Hypothesis(
                    metric="metric",
                    direction="increase",
                    statistical_test=AlwaysSignificant(),
                )
            ]
        )
        .with_replicates(2)
    )
    experiment.validate()
    result = experiment.run()
    assert result.metrics["t"]["metric"] == [1, 2]


def test_run_zero_replicates():
    pipeline = Pipeline([PassStep()])
    datasource = DummyDataSource()
    experiment = Experiment(datasource=datasource, pipeline=pipeline, replicates=0)
    experiment.validate()
    result = experiment.run()
    assert len(result.metrics["baseline"]["metric"]) == 1


def test_validate_partial_config():
    experiment = Experiment().with_pipeline(Pipeline([PassStep()]))
    with pytest.raises(ValueError):
        experiment.validate()


def test_apply_without_exit_step():
    pipeline = Pipeline([IdentityStep(), PassStep()])
    datasource = DummyDataSource()
    experiment = Experiment(datasource=datasource, pipeline=pipeline)
    experiment.validate()
    output = experiment.apply(data=7)
    assert output == {"metric": 7}


class TrackStep(PipelineStep):
    def __init__(self):
        self.called = False

    def __call__(self, data, ctx):
        self.called = True
        return data

    @property
    def params(self):
        return {}


def test_apply_multiple_exit_steps():
    step1 = TrackStep()
    step2 = TrackStep()
    pipeline = Pipeline([exit_step(step1), exit_step(step2), PassStep()])
    datasource = DummyDataSource()
    experiment = Experiment(datasource=datasource, pipeline=pipeline)
    experiment.validate()
    output = experiment.apply(data=3)
    assert output == 3
    assert step1.called is True
    assert step2.called is False


class StringMetricsStep(PipelineStep):
    def __call__(self, data, ctx):
        return {"metric": "a"}

    @property
    def params(self):
        return {}


def test_run_with_non_numeric_metrics_raises():
    pipeline = Pipeline([StringMetricsStep()])
    datasource = DummyDataSource()
    hypothesis = Hypothesis(
        metric="metric", direction="increase", statistical_test=AlwaysSignificant()
    )
    treatment = Treatment("t", {"increment": 0})
    experiment = Experiment(
        datasource=datasource,
        pipeline=pipeline,
        treatments=[treatment],
        hypotheses=[hypothesis],
    )
    experiment.validate()
    with pytest.raises(TypeError):
        experiment.run()


def test_cache_provenance_reused_between_runs(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    step = PassStep()
    pipeline1 = Pipeline([step])
    ds = DummyDataSource()
    exp1 = Experiment(datasource=ds, pipeline=pipeline1)
    exp1.validate()
    exp1.run()

    pipeline2 = Pipeline([PassStep()])
    exp2 = Experiment(datasource=ds, pipeline=pipeline2)
    exp2.validate()
    exp2.run()
    assert pipeline2.get_provenance()[0]["cache_hit"] is True
