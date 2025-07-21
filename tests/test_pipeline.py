from typing import Any, Mapping

import pytest

from crystallize.utils.context import FrozenContext
from crystallize.utils.exceptions import PipelineExecutionError
from crystallize.pipelines.pipeline import Pipeline
from crystallize.pipelines.pipeline_step import PipelineStep


class AddStep(PipelineStep):
    def __init__(self, value: int):
        self.value = value

    def __call__(self, data: Any, ctx: FrozenContext) -> Any:
        return data + self.value

    @property
    def params(self) -> dict:
        return {"value": self.value}


class MetricsStep(PipelineStep):
    def __call__(self, data: Any, ctx: FrozenContext) -> Mapping[str, Any]:
        return {"result": data}

    @property
    def params(self) -> dict:
        return {}


class FailStep(PipelineStep):
    def __call__(self, data: Any, ctx: FrozenContext) -> Any:  # pragma: no cover
        raise ValueError("boom")

    @property
    def params(self) -> dict:
        return {}


def test_pipeline_runs_and_returns_metrics():
    pipeline = Pipeline([AddStep(1), MetricsStep()])
    ctx = FrozenContext({})
    result = pipeline.run(0, ctx)
    assert result == {"result": 1}


def test_pipeline_signature():
    pipeline = Pipeline([AddStep(2), MetricsStep()])
    sig = pipeline.signature()
    assert "AddStep" in sig and "MetricsStep" in sig


def test_pipeline_execution_error():
    pipeline = Pipeline([FailStep()])
    ctx = FrozenContext({})
    with pytest.raises(PipelineExecutionError):
        pipeline.run(0, ctx)


def test_pipeline_execution_mid_chain():
    pipeline = Pipeline([AddStep(1), AddStep(2), MetricsStep()])
    ctx = FrozenContext({})
    result = pipeline.run(0, ctx)
    assert result == {"result": 3}
    prov = pipeline.get_provenance()
    assert len(prov) == 3
    assert prov[1]["step"] == "AddStep"
