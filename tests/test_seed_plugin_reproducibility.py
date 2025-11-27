import random

import numpy as np

from crystallize.datasources.datasource import DataSource
from crystallize.experiments.experiment import Experiment
from crystallize.pipelines.pipeline import Pipeline
from crystallize.pipelines.pipeline_step import PipelineStep
from crystallize.plugins.execution import ParallelExecution
from crystallize.plugins.plugins import SeedPlugin
from crystallize.utils.context import FrozenContext


def _seed_fn(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed % (2**32 - 1))


class RandomSource(DataSource):
    def fetch(self, ctx: FrozenContext) -> float:  # type: ignore[override]
        return random.random() + np.random.random()


class AddRandomStep(PipelineStep):
    def __call__(self, data, ctx):
        val = data + random.random() + np.random.random()
        ctx.metrics.add("rand", val)
        return {"rand": val}

    @property
    def params(self):
        return {}


def _run(seed_plugin, execution_plugin=None):
    pipeline = Pipeline([AddRandomStep()])
    ds = RandomSource()
    plugins = [seed_plugin]
    if execution_plugin is not None:
        plugins.append(execution_plugin)
    exp = Experiment(datasource=ds, pipeline=pipeline, plugins=plugins)
    exp.validate()
    res = exp.run(replicates=5)
    return res.metrics.baseline.metrics["rand"]


def test_seed_plugin_reproducibility_process_executor():
    seed_plugin = SeedPlugin(seed=42, seed_fn=_seed_fn)

    serial = _run(seed_plugin)
    process = _run(seed_plugin, ParallelExecution(executor_type="process"))

    assert serial == process


def test_seed_plugin_warns_for_thread_executor(caplog):
    seed_plugin = SeedPlugin(seed=99, seed_fn=_seed_fn)

    with caplog.at_level("WARNING", logger="crystallize"):
        _run(seed_plugin, ParallelExecution(executor_type="thread"))

    assert any("executor_type='thread'" in rec.message for rec in caplog.records)
