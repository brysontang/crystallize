import types
import pytest
from textual.app import App
from textual.widgets import RichLog, Button
from cli.screens.run import RunScreen
from crystallize import data_source, pipeline_step
from crystallize.experiments.experiment import Experiment
from crystallize.pipelines.pipeline import Pipeline


@data_source
def ds(ctx):
    return 0


@pipeline_step()
def step(data, ctx):
    return data


@pytest.mark.asyncio
async def test_run_screen_toggle_plain_text():
    exp = Experiment(datasource=ds(), pipeline=Pipeline([step()]))
    exp.validate()
    screen = RunScreen(exp, "rerun", None)

    screen.run_worker = lambda *a, **k: types.SimpleNamespace(
        is_finished=True, cancel=lambda: None
    )

    async with App().run_test() as pilot:
        await pilot.app.push_screen(screen)
        log = screen.query_one("#live_log", RichLog)
        button = screen.query_one("#toggle_text", Button)
        assert log.markup and log.highlight
        assert button.label == "Plain Text"
        await pilot.press("t")
        assert not log.markup and not log.highlight
        assert button.label == "Rich Text"
