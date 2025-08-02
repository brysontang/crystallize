from __future__ import annotations

import json
from pathlib import Path

import yaml

def test_step_duration_skips_cache(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    cache_dir = tmp_path / "cache"
    if cache_dir.exists():
        import shutil
        shutil.rmtree(cache_dir)
    cache_dir.mkdir()
    monkeypatch.setenv("CRYSTALLIZE_CACHE_DIR", str(cache_dir))

    from cli.status_plugin import CLIStatusPlugin
    from cli.utils import compute_static_eta
    from crystallize import Experiment, Pipeline, data_source, pipeline_step

    @data_source
    def ds(ctx):
        return 0

    @pipeline_step()
    def simple(data, ctx):
        return data

    plugin = CLIStatusPlugin(lambda e, i: None)
    exp = Experiment(
        datasource=ds(), pipeline=Pipeline([simple()]), plugins=[plugin], name="exp"
    )
    exp.validate()
    exp.run()

    hist = tmp_path / ".cache" / "crystallize" / "steps" / "exp.json"
    data = json.loads(hist.read_text())
    step_name = next(iter(data))
    assert len(data[step_name]) == 1

    cfg = tmp_path / "config.yaml"
    cfg.write_text(
        yaml.safe_dump(
            {"name": "exp", "datasource": {}, "steps": ["simple"], "treatments": {}}
        )
    )
    eta = compute_static_eta(cfg)
    assert abs(eta.total_seconds() - data[step_name][0]) < 0.5


def test_step_duration_skips_error(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    cache_dir = tmp_path / "cache"
    if cache_dir.exists():
        import shutil
        shutil.rmtree(cache_dir)
    cache_dir.mkdir()
    monkeypatch.setenv("CRYSTALLIZE_CACHE_DIR", str(cache_dir))

    from cli.status_plugin import CLIStatusPlugin
    from crystallize import Experiment, Pipeline, data_source, pipeline_step

    @data_source
    def ds(ctx):
        return 0

    @pipeline_step()
    def boom(data, ctx):
        raise RuntimeError("boom")

    plugin = CLIStatusPlugin(lambda e, i: None)
    exp = Experiment(
        datasource=ds(), pipeline=Pipeline([boom()]), plugins=[plugin], name="exp"
    )
    exp.validate()
    result = exp.run()
    assert result.errors

    hist = tmp_path / ".cache" / "crystallize" / "steps" / "exp.json"
    assert json.loads(hist.read_text()) == {}


def test_context_emit_invokes_handler() -> None:
    from crystallize.utils.context import FrozenContext

    called: dict[str, float] = {}

    def handler(ctx: FrozenContext, val: float) -> None:
        called["val"] = val

    ctx = FrozenContext({})
    ctx.add("textual__emit", handler)
    emit = ctx.get("textual__emit")
    assert emit is not None
    emit(ctx, 0.3)
    assert called["val"] == 0.3
