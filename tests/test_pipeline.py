import pytest
from typing import Any, Mapping

from crystallize.core.pipeline import Pipeline, InvalidPipelineOutput
from crystallize.core.pipeline_step import PipelineStep
from crystallize.core.context import FrozenContext


class AddStep(PipelineStep):
    def __init__(self, value: int):
        self.value = value

    def __call__(self, data: Any, ctx: FrozenContext) -> Any:
        return data + self.value

    @property
    def params(self) -> dict:
        return {'value': self.value}


class MetricsStep(PipelineStep):
    def __call__(self, data: Any, ctx: FrozenContext) -> Mapping[str, Any]:
        return {'result': data}

    @property
    def params(self) -> dict:
        return {}


def test_pipeline_runs_and_returns_metrics():
    pipeline = Pipeline([AddStep(1), MetricsStep()])
    ctx = FrozenContext({})
    result = pipeline.run(0, ctx)
    assert result == {'result': 1}


def test_invalid_pipeline_output_raises():
    pipeline = Pipeline([AddStep(1)])
    ctx = FrozenContext({})
    with pytest.raises(InvalidPipelineOutput):
        pipeline.run(0, ctx)


def test_pipeline_signature():
    pipeline = Pipeline([AddStep(2), MetricsStep()])
    sig = pipeline.signature()
    assert "AddStep" in sig and "MetricsStep" in sig
