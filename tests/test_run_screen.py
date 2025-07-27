import types
import pytest
from textual.app import App
from textual.widgets import RichLog, Button, TextArea
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
        text_area = screen.query_one("#plain_log", TextArea)
        button = screen.query_one("#toggle_text", Button)

        # Initially RichLog visible, TextArea hidden
        assert log.display == True
        assert text_area.display == False
        assert button.label == "Plain Text"

        # Toggle to plain text mode
        await pilot.press("t")
        assert log.display == False
        assert text_area.display == True
        assert button.label == "Rich Text"

        # Toggle back to rich text mode
        await pilot.press("t")
        assert log.display == True
        assert text_area.display == False
        assert button.label == "Plain Text"
