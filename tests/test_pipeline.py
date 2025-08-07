from typing import Any, Mapping
import asyncio

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


class TupleMetricsStep(PipelineStep):
    def __call__(self, data: Any, ctx: FrozenContext):
        return data, {"metric": data}

    @property
    def params(self) -> dict:
        return {}


class TupleDataStep(PipelineStep):
    def __call__(self, data: Any, ctx: FrozenContext):
        return data, data + 1

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


def test_pipeline_metrics_tuple_return():
    pipeline = Pipeline([TupleMetricsStep()])
    ctx = FrozenContext({})
    result = pipeline.run(5, ctx)
    assert result == 5
    assert ctx.metrics["metric"] == (5,)


def test_pipeline_tuple_data_not_metrics():
    pipeline = Pipeline([TupleDataStep()])
    ctx = FrozenContext({})
    result = pipeline.run(1, ctx)
    assert result == (1, 2)
    assert ctx.metrics.as_dict() == {}


class TrackStep(PipelineStep):
    def __call__(self, data: Any, ctx: FrozenContext):
        _ = ctx["a"]
        ctx.add("b", 2)
        return data, {"m": data}

    @property
    def params(self) -> dict:
        return {}


def test_provenance_records_ctx_and_metrics():
    pipeline = Pipeline([TrackStep()])
    ctx = FrozenContext({"a": 1})
    pipeline.run(5, ctx, verbose=True)
    prov = pipeline.get_provenance()[0]
    assert prov["ctx_changes"]["reads"] == {"a": 1}
    assert prov["ctx_changes"]["wrote"] == {"b": {"before": None, "after": 2}}
    assert prov["ctx_changes"]["metrics"] == {"m": {"before": (), "after": (5,)}}


class AsyncAddStep(PipelineStep):
    def __init__(self, value: int):
        self.value = value

    async def __call__(self, data: Any, ctx: FrozenContext) -> Any:
        await asyncio.sleep(0)
        return data + self.value

    @property
    def params(self) -> dict:
        return {"value": self.value}


def test_async_pipeline_step_runs():
    pipeline = Pipeline([AsyncAddStep(5), MetricsStep()])
    ctx = FrozenContext({})
    result = pipeline.run(1, ctx)
    assert result == {"result": 6}


class BrokenHashStep(PipelineStep):
    def __init__(self):
        self._hash_error = ValueError("Hash computation failed")

    def __call__(self, data: Any, ctx: FrozenContext) -> Any:
        return data

    @property
    def step_hash(self):
        raise self._hash_error

    @property
    def params(self) -> dict:
        return {}


def test_pipeline_step_hash_error():
    pipeline = Pipeline([BrokenHashStep()])
    ctx = FrozenContext({})

    with pytest.raises(ValueError) as exc_info:
        pipeline.run(0, ctx)

    assert str(exc_info.value) == "Hash computation failed"
