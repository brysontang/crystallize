import asyncio
from pathlib import Path

from cli.screens.run import _launch_run
from crystallize import data_source, pipeline_step
from crystallize.experiments.experiment import Experiment
from crystallize.experiments.experiment_graph import ExperimentGraph
from crystallize.pipelines.pipeline import Pipeline
from crystallize.plugins.plugins import ArtifactPlugin
from crystallize.utils.constants import METADATA_FILENAME


@data_source
def dummy_source(ctx):
    return 0


@pipeline_step()
def add_one(data, ctx):
    return data


class FakeApp:
    def __init__(self, responses):
        self.responses = responses
        self.screens = []

    async def push_screen_wait(self, screen):
        self.screens.append(type(screen).__name__)
        return self.responses.get(type(screen).__name__)

    async def push_screen(self, screen):
        self.screens.append(type(screen).__name__)


def test_launch_run_deletes(tmp_path: Path):
    plugin = ArtifactPlugin(root_dir=str(tmp_path))
    exp = Experiment(
        datasource=dummy_source(),
        pipeline=Pipeline([add_one()]),
        name="e",
        plugins=[plugin],
    )
    exp.validate()
    graph = ExperimentGraph.from_experiments([exp])

    base = Path(plugin.root_dir) / "e"
    metadata_dir = base / "v0"
    metadata_dir.mkdir(parents=True)
    (metadata_dir / METADATA_FILENAME).write_text("{}")

    app = FakeApp(
        {
            "PrepareRunScreen": ("rerun", (0,)),
            "ConfirmScreen": True,
        }
    )

    asyncio.run(_launch_run(app, graph))

    assert "RunScreen" in app.screens
    assert not base.exists()


def test_launch_run_missing_metadata(tmp_path: Path):
    plugin = ArtifactPlugin(root_dir=str(tmp_path))
    exp = Experiment(
        datasource=dummy_source(),
        pipeline=Pipeline([add_one()]),
        name="e",
        plugins=[plugin],
    )
    exp.validate()
    graph = ExperimentGraph.from_experiments([exp])

    base = Path(plugin.root_dir) / "e"
    base.mkdir()

    app = FakeApp({"PrepareRunScreen": ("rerun", ())})

    asyncio.run(_launch_run(app, graph))

    assert "RunScreen" in app.screens
    assert "ConfirmScreen" not in app.screens
    assert base.exists()


def test_launch_run_cancel(tmp_path: Path):
    exp = Experiment(datasource=dummy_source(), pipeline=Pipeline([add_one()]))
    exp.validate()

    app = FakeApp({"PrepareRunScreen": None})
    asyncio.run(_launch_run(app, exp))

    assert "RunScreen" not in app.screens
