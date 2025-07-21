import logging

from crystallize.datasources.datasource import DataSource
from crystallize.experiments.experiment import Experiment
from crystallize.pipelines.pipeline import Pipeline
from crystallize.pipelines.pipeline_step import PipelineStep
from crystallize.plugins.plugins import LoggingPlugin
from crystallize.experiments.result import Result
from crystallize.experiments.result_structs import ExperimentMetrics, TreatmentMetrics, HypothesisResult


class DummySource(DataSource):
    def fetch(self, ctx):
        return 0


class DummyStep(PipelineStep):
    def __call__(self, data, ctx):  # pragma: no cover - simple pass-through
        return {"metric": data}

    @property
    def params(self):
        return {}


def _make_experiment(plugin: LoggingPlugin) -> Experiment:
    pipeline = Pipeline([DummyStep()])
    ds = DummySource()
    exp = Experiment(datasource=ds, pipeline=pipeline, plugins=[plugin])
    return exp


def _make_result() -> Result:
    metrics = ExperimentMetrics(
        baseline=TreatmentMetrics({"metric": [0]}),
        treatments={},
        hypotheses=[
            HypothesisResult(
                name="h",
                results={"baseline": {"value": 1}},
                ranking={"best": None},
            )
        ],
    )
    return Result(metrics=metrics, errors={})


def test_logging_plugin_emits_messages(caplog):
    plugin = LoggingPlugin(verbose=True, log_level="INFO")
    exp = _make_experiment(plugin)
    result = _make_result()
    with caplog.at_level(logging.INFO, logger="crystallize"):
        plugin.before_run(exp)
        plugin.after_step(exp, DummyStep(), None, exp._setup_ctx)
        plugin.after_run(exp, result)
    messages = [r.getMessage() for r in caplog.records]
    assert any("Experiment:" in m for m in messages)
    assert any("finished step DummyStep" in m for m in messages)
    assert any(m.startswith("Completed in") for m in messages)


def test_logging_plugin_invalid_level():
    logger = logging.getLogger("crystallize")
    plugin = LoggingPlugin(log_level="WRONG")
    exp = _make_experiment(plugin)
    plugin.before_run(exp)
    assert logger.level == logging.INFO
    logger.handlers.clear()
    logger.setLevel(logging.NOTSET)
