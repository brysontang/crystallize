from crystallize.experiments.experiment import Experiment
from crystallize.datasources.datasource import DataSource
from crystallize.experiments.treatment import Treatment
from crystallize.pipelines.pipeline import Pipeline
from crystallize.pipelines.pipeline_step import PipelineStep
from crystallize.utils.context import FrozenContext


class ParamDataSource(DataSource):
    def __init__(self, value: int) -> None:
        self.value = value
        self.params = {"value": value}

    def fetch(self, ctx: FrozenContext):
        return self.value


class RecordStep(PipelineStep):
    def __call__(self, data, ctx):
        ctx.metrics.add("metric", data)
        return {"metric": data}

    @property
    def params(self):
        return {}


def test_strong_ids_toggle(monkeypatch):
    pipeline = Pipeline([RecordStep()])
    treatment_a = Treatment("a", {"increment": 1})
    treatment_b = Treatment("b", {"increment": 2})

    exp1 = Experiment(
        datasource=ParamDataSource(1), pipeline=pipeline, treatments=[treatment_a]
    )
    exp2 = Experiment(
        datasource=ParamDataSource(2), pipeline=pipeline, treatments=[treatment_b]
    )
    exp1.validate()
    exp2.validate()
    exp1.run()
    exp2.run()
    assert exp1.id == exp2.id

    monkeypatch.setenv("CRYSTALLIZE_STRONG_IDS", "1")
    exp3 = Experiment(
        datasource=ParamDataSource(1), pipeline=pipeline, treatments=[treatment_a]
    )
    exp4 = Experiment(
        datasource=ParamDataSource(2), pipeline=pipeline, treatments=[treatment_b]
    )
    exp3.validate()
    exp4.validate()
    exp3.run()
    exp4.run()
    assert exp3.id != exp4.id

    exp5 = Experiment(
        datasource=ParamDataSource(1), pipeline=pipeline, treatments=[treatment_a]
    )
    exp6 = Experiment(
        datasource=ParamDataSource(1), pipeline=pipeline, treatments=[treatment_a]
    )
    exp5.validate()
    exp6.validate()
    exp5.run(replicates=1)
    exp6.run(replicates=2)
    assert exp5.id != exp6.id
