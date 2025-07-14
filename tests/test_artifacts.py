from pathlib import Path

from crystallize.core.cache import compute_hash
from crystallize.core.context import FrozenContext
from crystallize.core.datasource import DataSource
from crystallize.core.experiment import Experiment
from crystallize.core.pipeline import Pipeline
from crystallize.core.pipeline_step import PipelineStep
from crystallize.core.plugins import ArtifactPlugin


class DummySource(DataSource):
    def fetch(self, ctx: FrozenContext):
        return 0


class LogStep(PipelineStep):
    def __call__(self, data, ctx):
        ctx.artifacts.add("out.txt", b"hello")
        return {"result": data}

    @property
    def params(self):
        return {}


class CheckStep(PipelineStep):
    def __init__(self, log_counts):
        self.log_counts = log_counts

    def __call__(self, data, ctx):
        self.log_counts.append(len(ctx.artifacts))
        return {"result": data}

    @property
    def params(self):
        return {}


def test_artifacts_saved_and_cleared(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    logs = []
    pipeline = Pipeline([LogStep(), CheckStep(logs)])
    ds = DummySource()
    plugin = ArtifactPlugin(root_dir=str(tmp_path / "arts"))
    exp = Experiment(datasource=ds, pipeline=pipeline, plugins=[plugin])
    exp.validate()
    exp.run()

    exp_id = compute_hash(pipeline.signature())
    expected = (
        tmp_path
        / "arts"
        / exp_id
        / "v0"
        / "replicate_0"
        / "baseline"
        / "LogStep"
        / "out.txt"
    )
    assert expected.read_text() == "hello"
    assert logs == [0]


def test_artifact_versioning(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    pipeline = Pipeline([LogStep()])
    ds = DummySource()
    plugin = ArtifactPlugin(root_dir=str(tmp_path / "arts"), versioned=True)
    exp = Experiment(datasource=ds, pipeline=pipeline, plugins=[plugin])
    exp.validate()
    exp.run()
    exp.run()

    exp_id = compute_hash(pipeline.signature())
    path0 = (
        tmp_path
        / "arts"
        / exp_id
        / "v0"
        / "replicate_0"
        / "baseline"
        / "LogStep"
        / "out.txt"
    )
    path1 = (
        tmp_path
        / "arts"
        / exp_id
        / "v1"
        / "replicate_0"
        / "baseline"
        / "LogStep"
        / "out.txt"
    )
    assert path0.exists() and path1.exists()
