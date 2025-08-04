from __future__ import annotations

import json
from pathlib import Path

from crystallize.experiments.experiment import Experiment
from crystallize.experiments.treatment import Treatment
from crystallize.pipelines.pipeline import Pipeline
from crystallize.pipelines.pipeline_step import PipelineStep
from crystallize.datasources.datasource import DataSource
from crystallize.utils.context import FrozenContext
from crystallize.plugins.plugins import ArtifactPlugin
from crystallize.plugins import load_metrics, load_all_metrics
from cli.screens.run import _inject_status_plugin


class DummyDataSource(DataSource):
    def fetch(self, ctx: FrozenContext):
        return 0


class PassStep(PipelineStep):
    cacheable = True

    def __call__(self, data, ctx):
        ctx.metrics.add("metric", 1)
        return {"metric": 1}

    @property
    def params(self):
        return {}


def _make_experiment(tmp_path: Path, plugin: ArtifactPlugin | None = None) -> Experiment:
    pipeline = Pipeline([PassStep()])
    datasource = DummyDataSource()
    plugins = [plugin] if plugin else []
    exp = Experiment(datasource=datasource, pipeline=pipeline, plugins=plugins, name="demo")
    exp.validate()
    return exp


def test_retention_prunes_versions_and_big_files(tmp_path: Path):
    plugin = ArtifactPlugin(
        root_dir=tmp_path,
        versioned=True,
        artifact_retention=3,
        big_file_threshold_mb=1,
    )
    exp = _make_experiment(tmp_path, plugin)
    for i in range(5):
        exp.run()
        big = Path(plugin.root_dir) / "demo" / f"v{i}" / "big.bin"
        big.parent.mkdir(parents=True, exist_ok=True)
        with open(big, "wb") as f:
            f.write(b"0" * 2 * 1024 * 1024)
    base = Path(plugin.root_dir) / "demo"
    versions = sorted(int(p.name[1:]) for p in base.glob("v*"))
    assert versions == [0, 1, 2, 3, 4]
    for v in [0, 1, 2, 3]:
        assert not (base / f"v{v}" / "big.bin").exists()
    assert (base / "v4" / "big.bin").exists()


def test_resume_picks_latest_version(tmp_path: Path):
    plugin = ArtifactPlugin(root_dir=tmp_path, versioned=True)
    exp = _make_experiment(tmp_path, plugin)
    base = Path(plugin.root_dir) / "demo"
    for idx, val in enumerate([1, 2]):
        dest = base / f"v{idx}" / "baseline"
        dest.mkdir(parents=True, exist_ok=True)
        with open(dest / "results.json", "w") as f:
            json.dump({"metrics": {"metric": [val]}}, f)
        open(dest / ".crystallize_complete", "a").close()
    res = exp.run(strategy="resume")
    assert res.metrics.baseline.metrics["metric"] == [2]


def test_cli_injects_versioned_plugin(tmp_path: Path):
    exp = _make_experiment(tmp_path, plugin=None)
    class DummyWriter:
        def write(self, *_args, **_kwargs):
            pass
    _inject_status_plugin(exp, lambda *_: None, writer=DummyWriter())
    plugin = exp.get_plugin(ArtifactPlugin)
    assert plugin is not None and plugin.versioned is True


def test_summary_uses_stored_metrics(tmp_path: Path):
    plugin = ArtifactPlugin(root_dir=tmp_path, versioned=True, big_file_threshold_mb=1)
    exp = _make_experiment(tmp_path, plugin)
    t_a = Treatment("A", {})
    t_b = Treatment("B", {})
    exp.run(treatments=[t_a, t_b])
    base = Path(plugin.root_dir) / "demo"
    big = base / "v0" / "big.bin"
    big.parent.mkdir(parents=True, exist_ok=True)
    with open(big, "wb") as f:
        f.write(b"0" * 2 * 1024 * 1024)

    exp.run(treatments=[t_a], strategy="resume")
    versions = [int(p.name[1:]) for p in base.glob("v*")]
    assert versions == [0]
    ver, baseline, tmap = load_metrics(base, 0)
    assert ver == 0
    assert "metric" in baseline
    assert set(tmap) == {"A", "B"}

    exp.run(treatments=[t_a], strategy="rerun")
    hist_ver, _, hist_map = load_all_metrics(base)
    assert hist_ver == 1
    assert hist_map["A"][0] == 1 and hist_map["B"][0] == 0
    assert not big.exists()


def test_pruned_versions_keep_metrics(tmp_path: Path):
    plugin = ArtifactPlugin(
        root_dir=tmp_path, versioned=True, artifact_retention=1
    )
    exp = _make_experiment(tmp_path, plugin)
    t_a = Treatment("A", {})
    t_b = Treatment("B", {})
    exp.run(treatments=[t_a, t_b])
    exp.run(treatments=[t_a], strategy="rerun")
    base = Path(plugin.root_dir) / "demo"
    assert (base / "v0" / "A" / "results.json").exists()
    assert (base / "v0" / "B" / "results.json").exists()
    latest, _, tmap = load_all_metrics(base)
    assert latest == 1
    assert tmap["B"][0] == 0
