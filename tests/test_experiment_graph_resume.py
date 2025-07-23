from pathlib import Path

from crystallize.datasources import Artifact
from crystallize.datasources.datasource import DataSource
from crystallize.experiments.experiment import Experiment
from crystallize.experiments.experiment_graph import ExperimentGraph
from crystallize.pipelines.pipeline import Pipeline
from crystallize.pipelines.pipeline_step import PipelineStep
from crystallize.plugins.plugins import ArtifactPlugin


class DummySource(DataSource):
    def fetch(self, ctx):
        return ctx.get("replicate", 0)


class WriteStep(PipelineStep):
    def __init__(self, artifact: Artifact, value: int = 0):
        self.artifact = artifact
        self.value = value
        self.calls = 0

    def __call__(self, data, ctx):
        self.calls += 1
        if isinstance(data, Path):
            data_val = int(data.read_text())
        else:
            data_val = data
        result = data_val + self.value
        ctx.metrics.add("val", result)
        ctx.artifacts.add(self.artifact.name, str(result).encode())
        return result

    @property
    def params(self):
        return {"value": self.value}


class ConsumeStep(PipelineStep):
    def __init__(self):
        self.calls = 0

    def __call__(self, data, ctx):
        self.calls += 1
        ctx.metrics.add("val", int(Path(data).read_text()))
        return data

    @property
    def params(self):
        return {}




def test_mixed_replicates_resume(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    plugin = ArtifactPlugin(root_dir=str(tmp_path / "arts"))

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
    exp_a = Experiment(
        datasource=DummySource(),
        pipeline=Pipeline([step_a]),
        plugins=[plugin],
        name="A",
        outputs=[Artifact("a.txt")],
        replicates=1,
    )

    step_b = CountStep()
    ds_b = DummySource()
    exp_b = Experiment(
        datasource=ds_b,
        pipeline=Pipeline([step_b]),
        plugins=[plugin],
        name="B",
        replicates=10,
    )

    for e in (exp_a, exp_b):
        e.validate()

    graph = ExperimentGraph()
    graph.add_experiment(exp_a)
    graph.add_experiment(exp_b)
    graph.add_dependency(exp_b, exp_a)

    graph.run()
    assert step_a.calls == 1
    assert step_b.calls == 10

    step_a2 = CountStep()
    exp_a2 = Experiment(
        datasource=DummySource(),
        pipeline=Pipeline([step_a2]),
        plugins=[plugin],
        name="A",
        outputs=[Artifact("a.txt")],
        replicates=1,
    )

    step_b2 = CountStep()
    exp_b2 = Experiment(
        datasource=ds_b,
        pipeline=Pipeline([step_b2]),
        plugins=[plugin],
        name="B",
        replicates=10,
    )

    for e in (exp_a2, exp_b2):
        e.validate()

    graph2 = ExperimentGraph()
    graph2.add_experiment(exp_a2)
    graph2.add_experiment(exp_b2)
    graph2.add_dependency(exp_b2, exp_a2)
    res = graph2.run(strategy="resume")

    assert step_a2.calls == 0
    assert step_b2.calls == 0
    assert res["B"].metrics.baseline.metrics["val"] == list(range(10))

