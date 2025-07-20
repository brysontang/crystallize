from crystallize.core.context import FrozenContext
from crystallize.core.datasource import DataSource, MultiArtifactDataSource
from crystallize.core.experiment import Experiment
from crystallize.core.experiment_graph import ExperimentGraph
from crystallize.core.pipeline import Pipeline
from crystallize.core.pipeline_step import PipelineStep
from crystallize.core.treatment import Treatment


class DummySource(DataSource):
    def fetch(self, ctx: FrozenContext):
        return ctx.get("replicate", 0)


class PassStep(PipelineStep):
    def __call__(self, data, ctx):
        ctx.metrics.add("val", data + ctx.get("increment", 0))
        return data

    @property
    def params(self):
        return {}


def test_experiment_graph_runs_in_order():
    exp_a = Experiment(
        datasource=DummySource(), pipeline=Pipeline([PassStep()]), name="a"
    )
    exp_b = Experiment(
        datasource=DummySource(), pipeline=Pipeline([PassStep()]), name="b"
    )
    exp_c = Experiment(
        datasource=DummySource(), pipeline=Pipeline([PassStep()]), name="c"
    )
    for e in (exp_a, exp_b, exp_c):
        e.validate()

    graph = ExperimentGraph()
    for e in (exp_a, exp_b, exp_c):
        graph.add_experiment(e)
    graph.add_dependency(exp_c, exp_a)
    graph.add_dependency(exp_c, exp_b)

    treatment = Treatment("inc", {"increment": 1})
    results = graph.run(treatments=[treatment], replicates=2)

    assert results["a"].metrics.treatments["inc"].metrics["val"] == [1, 2]
    assert results["c"].metrics.treatments["inc"].metrics["val"] == [1, 2]


def test_experiment_graph_cycle_raises():
    exp_a = Experiment(
        datasource=DummySource(), pipeline=Pipeline([PassStep()]), name="a"
    )
    exp_b = Experiment(
        datasource=DummySource(), pipeline=Pipeline([PassStep()]), name="b"
    )
    for e in (exp_a, exp_b):
        e.validate()

    graph = ExperimentGraph()
    graph.add_experiment(exp_a)
    graph.add_experiment(exp_b)
    graph.add_dependency(exp_b, exp_a)
    graph.add_dependency(exp_a, exp_b)

    try:
        graph.run()
    except ValueError:
        assert True
    else:
        assert False


def test_multi_artifact_datasource():
    class PathSource(DataSource):
        def __init__(self, path):
            self.path = path
            self.replicates = 2

        def fetch(self, ctx: FrozenContext):
            return self.path

    ds = MultiArtifactDataSource(first=PathSource("x"), second=PathSource("y"))
    ctx = FrozenContext({"replicate": 0})
    assert ds.fetch(ctx) == {"first": "x", "second": "y"}
    assert ds.replicates == 2
