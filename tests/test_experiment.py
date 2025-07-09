from crystallize.core.datasource import DataSource
from crystallize.core.pipeline_step import PipelineStep
from crystallize.core.pipeline import Pipeline
from crystallize.core.hypothesis import Hypothesis
from crystallize.core.stat_test import StatisticalTest
from crystallize.core.treatment import Treatment
from crystallize.core.experiment import Experiment
from crystallize.core.context import FrozenContext


class DummyDataSource(DataSource):
    def fetch(self, ctx: FrozenContext):
        # return replicate id plus any increment in ctx
        return ctx['replicate'] + ctx.as_dict().get('increment', 0)


class PassStep(PipelineStep):
    def __call__(self, data, ctx):
        return {'metric': data}

    @property
    def params(self):
        return {}


class AlwaysSignificant(StatisticalTest):
    def run(self, baseline, treatment, *, alpha: float = 0.05):
        return {'p_value': 0.01, 'significant': True}


def test_experiment_run_basic():
    pipeline = Pipeline([PassStep()])
    datasource = DummyDataSource()
    hypothesis = Hypothesis(
        metric='metric', direction='increase', statistical_test=AlwaysSignificant()
    )
    treatment = Treatment('treat', lambda ctx: ctx.__setitem__('increment', 1))

    experiment = Experiment(
        datasource=datasource,
        pipeline=pipeline,
        treatments=[treatment],
        hypothesis=hypothesis,
        replicates=2,
    )
    result = experiment.run()
    assert result.metrics['baseline']['metric'] == [0, 1]
    assert result.metrics['treat']['metric'] == [1, 2]
    assert result.metrics['hypothesis']['accepted'] is True
    assert result.errors == {}
