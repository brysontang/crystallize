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
