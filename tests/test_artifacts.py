from pathlib import Path

import pytest

from crystallize.utils.cache import compute_hash
from crystallize.utils.context import FrozenContext
from crystallize.datasources.datasource import DataSource
from crystallize.experiments.experiment import Experiment
from crystallize.pipelines.pipeline import Pipeline
from crystallize.pipelines.pipeline_step import PipelineStep
from crystallize.plugins.plugins import ArtifactPlugin
from crystallize.datasources import Artifact, ArtifactLog
from crystallize.utils.context import ContextMutationError


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
        tmp_path / "arts" / exp_id / "v0" / "replicate_0" / "baseline" / "LogStep" / "out.txt"
    )
    assert expected.read_text() == "hello"
    assert logs == [0]


def test_artifacts_respect_experiment_name(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    pipeline = Pipeline([LogStep()])
    ds = DummySource()
    plugin = ArtifactPlugin(root_dir=str(tmp_path / "arts"))
    exp = Experiment(datasource=ds, pipeline=pipeline, plugins=[plugin], name="my_exp")
    exp.validate()
    exp.run()

    expected = (
        tmp_path
        / "arts"
        / "my_exp"
        / "v0"
        / "replicate_0"
        / "baseline"
        / "LogStep"
        / "out.txt"
    )
    assert expected.read_text() == "hello"


def test_artifact_datasource_before_run(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    pipeline = Pipeline([LogStep()])
    run_plugin = ArtifactPlugin(root_dir=str(tmp_path / "arts"))
    exp_run = Experiment(datasource=DummySource(), pipeline=pipeline, plugins=[run_plugin])
    exp_run.validate()
    exp_run.run(replicates=2)

    fresh_exp = Experiment(
        datasource=DummySource(),
        pipeline=pipeline,
        plugins=[ArtifactPlugin(root_dir=str(tmp_path / "arts"))],
    )
    fresh_exp.validate()
    ds = fresh_exp.artifact_datasource(step="LogStep", name="out.txt")
    assert ds.replicates == 2
    assert ds.fetch(FrozenContext({"replicate": 1})).read_text() == "hello"


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
    path0 = tmp_path / "arts" / exp_id / "v0" / "replicate_0" / "baseline" / "LogStep" / "out.txt"
    path1 = tmp_path / "arts" / exp_id / "v1" / "replicate_0" / "baseline" / "LogStep" / "out.txt"
    assert path0.exists() and path1.exists()


def test_metadata_written_and_chained(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    pipeline = Pipeline([LogStep()])
    ds = DummySource()
    plugin = ArtifactPlugin(root_dir=str(tmp_path / "arts"))
    exp1 = Experiment(datasource=ds, pipeline=pipeline, plugins=[plugin])
    exp1.validate()
    exp1.run(replicates=2)

    meta_path = Path(plugin.root_dir) / exp1.id / f"v{plugin.version}" / "metadata.json"
    assert meta_path.exists()

    ds2 = exp1.artifact_datasource(step="LogStep", name="out.txt")
    pipeline2 = Pipeline([CheckStep([])])
    exp2 = Experiment(datasource=ds2, pipeline=pipeline2)
    exp2.validate()
    first_path = ds2.fetch(FrozenContext({"replicate": 0}))
    assert isinstance(first_path, Path)
    assert first_path.exists()
    exp2.run()
    assert ds2.replicates == 2


def test_artifact_datasource_replicate_mismatch(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    pipeline = Pipeline([LogStep()])
    ds = DummySource()
    plugin = ArtifactPlugin(root_dir=str(tmp_path / "arts"))
    exp1 = Experiment(datasource=ds, pipeline=pipeline, plugins=[plugin])
    exp1.validate()
    exp1.run(replicates=2)

    ds2 = exp1.artifact_datasource(step="LogStep", name="out.txt")
    pipeline2 = Pipeline([CheckStep([])])
    exp2 = Experiment(datasource=ds2, pipeline=pipeline2)
    exp2.validate()
    with pytest.raises(ValueError):
        exp2.run(replicates=3)


def test_artifact_datasource_missing_file(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    pipeline = Pipeline([LogStep()])
    ds = DummySource()
    plugin = ArtifactPlugin(root_dir=str(tmp_path / "arts"))
    exp1 = Experiment(datasource=ds, pipeline=pipeline, plugins=[plugin])
    exp1.validate()
    exp1.run()

    ds2 = exp1.artifact_datasource(step="LogStep", name="missing.txt")
    with pytest.raises(FileNotFoundError):
        ds2.fetch(FrozenContext({"replicate": 0}))


def test_artifact_datasource_require_metadata(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    pipeline = Pipeline([LogStep()])
    ds = DummySource()
    plugin = ArtifactPlugin(root_dir=str(tmp_path / "arts"))
    exp1 = Experiment(datasource=ds, pipeline=pipeline, plugins=[plugin])
    exp1.validate()
    exp1.run()

    meta = Path(plugin.root_dir) / exp1.id / f"v{plugin.version}" / "metadata.json"
    meta.unlink()

    with pytest.raises(FileNotFoundError):
        exp1.artifact_datasource(step="LogStep", name="out.txt", require_metadata=True)


def test_output_write_and_injection(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    class WriteStep(PipelineStep):
        def __init__(self, out: Artifact) -> None:
            self.out = out

        def __call__(self, data, ctx):
            self.out.write(b"data")
            return data

        @property
        def params(self):
            return {}

    out = Artifact("x.txt")
    pipeline = Pipeline([WriteStep(out)])
    exp = Experiment(
        datasource=DummySource(),
        pipeline=pipeline,
        plugins=[ArtifactPlugin(root_dir=str(tmp_path / "arts"))],
        outputs=[out],
    )
    exp.validate()
    exp.run()
    path = tmp_path / "arts" / exp.id / "v0" / "baseline" / "results.json"
    assert path.exists()


def test_artifact_log_write_once():
    log = ArtifactLog()
    log.add("a.txt", b"1")
    with pytest.raises(ContextMutationError):
        log.add("a.txt", b"2")
