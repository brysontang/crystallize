from pathlib import Path

import pytest

from crystallize.datasources import Artifact
from crystallize.datasources.datasource import DataSource, ExperimentInput
from crystallize.experiments.experiment import Experiment
from crystallize.experiments.experiment_graph import ExperimentGraph
from crystallize.experiments.hypothesis import Hypothesis
from crystallize.experiments.treatment import Treatment
from crystallize.pipelines.pipeline import Pipeline
from crystallize.pipelines.pipeline_step import PipelineStep
from crystallize.plugins.plugins import ArtifactPlugin
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


def test_empty_graph_runs():
    graph = ExperimentGraph()
    assert graph.run() == {}


def test_hypotheses_verified():
    exp_a = Experiment(
        datasource=DummySource(), pipeline=Pipeline([PassStep()]), name="a"
    )
    exp_a.validate()
    exp_b = Experiment(
        datasource=DummySource(), pipeline=Pipeline([PassStep()]), name="b"
    )
    exp_b.validate()

    hypo = Hypothesis(
        verifier=lambda b, t: {"diff": sum(t["val"]) - sum(b["val"])}, metrics="val"
    )
    exp_b.hypotheses = [hypo]

    graph = ExperimentGraph()
    graph.add_experiment(exp_a)
    graph.add_experiment(exp_b)
    graph.add_dependency(exp_b, exp_a)

    results = graph.run(treatments=[Treatment("inc", {"increment": 1})])
    diff = results["b"].metrics.hypotheses[0].results["inc"]["diff"]
    assert diff == 1


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

    with pytest.raises(ValueError, match="contains cycles"):
        graph.run()


def test_multi_artifact_datasource():
    class DummyArtifact(Artifact):
        def __init__(self, name: str, value: str) -> None:
            super().__init__(name, loader=lambda p: value)
            self.replicates = 2

        def fetch(self, ctx: FrozenContext) -> str:  # type: ignore[override]
            return self.loader(Path())

    ds = ExperimentInput(first=DummyArtifact("x", "X"), second=DummyArtifact("y", "Y"))
    ctx = FrozenContext({"replicate": 0})
    assert ds.fetch(ctx) == {"first": "X", "second": "Y"}
    assert ds.replicates == 2


def test_add_experiment_requires_name():
    graph = ExperimentGraph()
    anon = Experiment(datasource=DummySource(), pipeline=Pipeline([PassStep()]))
    with pytest.raises(ValueError):
        graph.add_experiment(anon)


def test_add_dependency_requires_added_nodes():
    graph = ExperimentGraph()
    exp_a = Experiment(
        datasource=DummySource(), pipeline=Pipeline([PassStep()]), name="a"
    )
    exp_b = Experiment(
        datasource=DummySource(), pipeline=Pipeline([PassStep()]), name="b"
    )
    graph.add_experiment(exp_a)
    with pytest.raises(ValueError):
        graph.add_dependency(exp_b, exp_a)


def test_graph_resume_skips_experiments(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    class CountStep(PipelineStep):
        def __init__(self):
            self.calls = 0

        def __call__(self, data, ctx):
            self.calls += 1
            ctx.metrics.add("val", data)
            return data

        @property
        def params(self):
            return {}

    step_a = CountStep()
    plugin = ArtifactPlugin(root_dir=str(tmp_path / "arts"))
    exp_a = Experiment(
        datasource=DummySource(),
        pipeline=Pipeline([step_a]),
        plugins=[plugin],
        name="a",
        outputs=[Artifact("x.txt")],
    )
    exp_a.validate()
    graph = ExperimentGraph()
    graph.add_experiment(exp_a)
    graph.run()
    assert step_a.calls == 1

    step_a2 = CountStep()
    exp_a2 = Experiment(
        datasource=DummySource(),
        pipeline=Pipeline([step_a2]),
        plugins=[plugin],
        name="a",
        outputs=[Artifact("x.txt")],
    )
    exp_a2.validate()
    graph2 = ExperimentGraph()
    graph2.add_experiment(exp_a2)
    graph2.run(strategy="resume")
    assert step_a2.calls == 0


def test_graph_resume_checks_downstream_outputs(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    out1 = Artifact("one.txt")
    out2 = Artifact("two.txt")

    class ProduceStep(PipelineStep):
        def __init__(self, out_a: Artifact, out_b: Artifact | None = None) -> None:
            self.out_a = out_a
            self.out_b = out_b
            self.calls = 0

        def __call__(self, data, ctx):
            self.calls += 1
            self.out_a.write(b"a")
            if self.out_b:
                self.out_b.write(b"b")
            ctx.metrics.add("val", data)
            return data

        @property
        def params(self):
            return {}

    # initial run producing only one.txt
    step_a = ProduceStep(out1)
    plugin = ArtifactPlugin(root_dir=str(tmp_path / "arts"))
    exp_a = Experiment(
        datasource=DummySource(),
        pipeline=Pipeline([step_a]),
        plugins=[plugin],
        name="a",
        outputs=[out1],
    )
    exp_a.validate()

    ds_b = exp_a.artifact_datasource(step="ProduceStep", name="one.txt")
    exp_b = Experiment(
        datasource=ds_b,
        pipeline=Pipeline([PassStep()]),
        plugins=[plugin],
        name="b",
    )
    exp_b.validate()

    graph = ExperimentGraph()
    graph.add_experiment(exp_a)
    graph.add_experiment(exp_b)
    graph.add_dependency(exp_b, exp_a)
    graph.run()
    assert step_a.calls == 1

    # second run where B now needs two.txt as well
    step_a2 = ProduceStep(out1, out2)
    exp_a2 = Experiment(
        datasource=DummySource(),
        pipeline=Pipeline([step_a2]),
        plugins=[plugin],
        name="a",
        outputs=[out1, out2],
    )
    exp_a2.validate()

    ds_b2 = ExperimentInput(
        one=exp_a2.outputs["one.txt"],
        two=exp_a2.outputs["two.txt"],
    )
    exp_b2 = Experiment(
        datasource=ds_b2,
        pipeline=Pipeline([PassStep()]),
        plugins=[plugin],
        name="b",
    )
    exp_b2.validate()

    graph2 = ExperimentGraph()
    graph2.add_experiment(exp_a2)
    graph2.add_experiment(exp_b2)
    graph2.add_dependency(exp_b2, exp_a2)
    graph2.run(strategy="resume")

    assert step_a2.calls == 1


def test_from_experiments_builds_graph():
    out_a = Artifact("a.txt")
    out_b = Artifact("b.txt")

    class ProduceStep(PipelineStep):
        def __init__(self, art: Artifact) -> None:
            self.art = art

        def __call__(self, data, ctx):
            self.art.write(b"x")
            return data

        @property
        def params(self):
            return {}

    exp_a = Experiment(
        datasource=DummySource(),
        pipeline=Pipeline([ProduceStep(out_a)]),
        name="a",
        outputs=[out_a],
    )
    exp_b = Experiment(
        datasource=DummySource(),
        pipeline=Pipeline([ProduceStep(out_b)]),
        name="b",
        outputs=[out_b],
    )
    ds_c = ExperimentInput(first=out_a, second=out_b)
    exp_c = Experiment(datasource=ds_c, pipeline=Pipeline([PassStep()]), name="c")

    for e in (exp_a, exp_b, exp_c):
        e.validate()

    graph = ExperimentGraph.from_experiments([exp_a, exp_b, exp_c])
    results = graph.run()
    assert set(results) == {"a", "b", "c"}


def test_from_experiments_cycle_raises():
    art_a = Artifact("x")
    art_b = Artifact("y")
    exp_a = Experiment(
        datasource=ExperimentInput(b=art_b),
        pipeline=Pipeline([PassStep()]),
        name="a",
        outputs=[art_a],
    )
    exp_b = Experiment(
        datasource=ExperimentInput(a=art_a),
        pipeline=Pipeline([PassStep()]),
        name="b",
        outputs=[art_b],
    )
    for e in (exp_a, exp_b):
        e.validate()

    with pytest.raises(ValueError, match="cycles"):
        ExperimentGraph.from_experiments([exp_a, exp_b])


def test_from_experiments_unused_raises():
    exp_a = Experiment(
        datasource=DummySource(), pipeline=Pipeline([PassStep()]), name="a"
    )
    exp_b = Experiment(
        datasource=DummySource(), pipeline=Pipeline([PassStep()]), name="b"
    )
    for e in (exp_a, exp_b):
        e.validate()

    with pytest.raises(ValueError, match="Unused experiments"):
        ExperimentGraph.from_experiments([exp_a, exp_b])


def test_from_experiments_duplicate_artifact():
    art = Artifact("same")
    exp_a = Experiment(
        datasource=DummySource(),
        pipeline=Pipeline([PassStep()]),
        name="a",
        outputs=[art],
    )
    exp_b = Experiment(
        datasource=DummySource(),
        pipeline=Pipeline([PassStep()]),
        name="b",
        outputs=[art],
    )
    for e in (exp_a, exp_b):
        e.validate()

    with pytest.raises(ValueError, match="multiple experiments"):
        ExperimentGraph.from_experiments([exp_a, exp_b])
