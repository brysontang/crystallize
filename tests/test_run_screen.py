from pathlib import Path

import importlib
import sys
import time

from cli.screens.run import _inject_status_plugin, delete_artifacts, _reload_modules
from cli.status_plugin import CLIStatusPlugin
from crystallize import data_source, pipeline_step
from crystallize.experiments.experiment import Experiment
from crystallize.pipelines.pipeline import Pipeline
from crystallize.plugins.plugins import ArtifactPlugin
from cli.widgets.writer import WidgetWriter


@data_source
def dummy_source(ctx):
    return 0


@pipeline_step()
def add_one(data, ctx):
    return data + 1


class DummyWidget:
    def write(self, msg):
        pass

    def refresh(self):
        pass


class DummyApp:
    def call_from_thread(self, func, *args, **kwargs):
        func(*args, **kwargs)


def test_delete_artifacts(tmp_path: Path):
    plugin = ArtifactPlugin(root_dir=str(tmp_path))
    exp = Experiment(datasource=dummy_source(), pipeline=Pipeline([add_one()]), name="e", plugins=[plugin])
    exp.validate()
    path = Path(plugin.root_dir) / "e"
    path.mkdir()
    delete_artifacts(exp)
    assert not path.exists()


def test_inject_status_plugin_adds_experiment(tmp_path: Path):
    plugin = ArtifactPlugin(root_dir=str(tmp_path))
    exp = Experiment(datasource=dummy_source(), pipeline=Pipeline([add_one()]), name="exp", plugins=[plugin])
    exp.validate()
    events = []

    def cb(event, info):
        events.append(info)

    writer = WidgetWriter(DummyWidget(), DummyApp(), [])
    _inject_status_plugin(exp, cb, writer)
    plugin = exp.get_plugin(CLIStatusPlugin)
    assert plugin is not None
    plugin.callback("start", {})
    assert events[0]["experiment"] == "exp"


def test_reload_modules(tmp_path: Path):
    pkg_dir = tmp_path / "pkg"
    pkg_dir.mkdir()
    init_file = pkg_dir / "__init__.py"
    init_file.write_text("VALUE = 1\n")
    sys.path.insert(0, str(tmp_path))
    mod = importlib.import_module("pkg")
    assert mod.VALUE == 1
    time.sleep(1)
    init_file.write_text("VALUE = 2\n")
    _reload_modules(tmp_path)
    importlib.invalidate_caches()
    mod2 = importlib.import_module("pkg")
    assert mod2.VALUE == 2
    sys.path.remove(str(tmp_path))
    sys.modules.pop("pkg", None)
