from crystallize.datasources.datasource import DataSource
from crystallize.experiments.experiment import Experiment
from crystallize.experiments.experiment_graph import ExperimentGraph
from crystallize.experiments.treatment import Treatment
from crystallize.pipelines.pipeline import Pipeline
from crystallize.pipelines.pipeline_step import PipelineStep
from crystallize.utils.context import FrozenContext


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


def build_experiment(name: str, treatments=None) -> Experiment:
    exp = Experiment(
        datasource=DummySource(),
        pipeline=Pipeline([PassStep()]),
        name=name,
        treatments=treatments or [],
    )
    exp.validate()
    return exp


def test_treatment_inheritance_linear():
    t = Treatment("inc", {"increment": 1})
    exp1 = build_experiment("a", [t])
    exp2 = build_experiment("b")
    exp3 = build_experiment("c")

    graph = ExperimentGraph()
    for exp in (exp1, exp2, exp3):
        graph.add_experiment(exp)
    graph.add_dependency(exp2, exp1)
    graph.add_dependency(exp3, exp2)

    results = graph.run()

    assert "inc" in results["b"].metrics.treatments
    assert "inc" in results["c"].metrics.treatments


def test_treatment_inheritance_merge_same():
    t = Treatment("inc", {"increment": 1})
    exp_a = build_experiment("a", [t])
    exp_b = build_experiment("b", [t])
    exp_c = build_experiment("c")

    graph = ExperimentGraph()
    for exp in (exp_a, exp_b, exp_c):
        graph.add_experiment(exp)
    graph.add_dependency(exp_c, exp_a)
    graph.add_dependency(exp_c, exp_b)

    results = graph.run()

    assert set(results["c"].metrics.treatments) == {"inc"}


def test_treatment_inheritance_merge_different():
    t1 = Treatment("inc_a", {"increment": 1})
    t2 = Treatment("inc_b", {"increment": 2})
    exp_a = build_experiment("a", [t1])
    exp_b = build_experiment("b", [t2])
    exp_c = build_experiment("c")

    graph = ExperimentGraph()
    for exp in (exp_a, exp_b, exp_c):
        graph.add_experiment(exp)
    graph.add_dependency(exp_c, exp_a)
    graph.add_dependency(exp_c, exp_b)

    results = graph.run()

    assert set(results["c"].metrics.treatments) == {"inc_a", "inc_b"}


def test_treatment_propagation_from_middle():
    t = Treatment("mid", {"increment": 1})
    exp1 = build_experiment("one")
    exp2 = build_experiment("two", [t])
    exp3 = build_experiment("three")
    exp4 = build_experiment("four")

    graph = ExperimentGraph()
    for exp in (exp1, exp2, exp3, exp4):
        graph.add_experiment(exp)
    graph.add_dependency(exp2, exp1)
    graph.add_dependency(exp3, exp2)
    graph.add_dependency(exp4, exp3)

    results = graph.run()

    assert "mid" in results["three"].metrics.treatments
    assert "mid" in results["four"].metrics.treatments

