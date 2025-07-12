from crystallize.core.cache import compute_hash
from typing import Any
from concurrent.futures import ThreadPoolExecutor
from crystallize.core.context import FrozenContext
from crystallize.core.pipeline import Pipeline
from crystallize.core.pipeline_step import PipelineStep
import pytest
import numpy as np


class CountingStep(PipelineStep):
    cacheable = True

    def __init__(self):
        self.calls = 0

    def __call__(self, data, ctx):
        self.calls += 1
        return data + 1

    @property
    def params(self):
        return {}


class MetricsStep(PipelineStep):
    cacheable = True

    def __call__(self, data, ctx):
        return {"result": data}

    @property
    def params(self):
        return {}


def test_cache_hit_and_miss(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    step = CountingStep()
    pipeline = Pipeline([step, MetricsStep()])
    ctx = FrozenContext({})

    result1 = pipeline.run(0, ctx)
    assert result1 == {"result": 1}
    assert step.calls == 1

    step2 = CountingStep()
    pipeline2 = Pipeline([step2, MetricsStep()])
    result2 = pipeline2.run(0, ctx)
    assert result2 == {"result": 1}
    assert step2.calls == 0
    assert pipeline2.get_provenance()[0]["cache_hit"] is True

    result3 = pipeline2.run(5, ctx)
    assert result3 == {"result": 6}
    assert step2.calls == 1


class NoCacheStep(CountingStep):
    cacheable = False


def test_non_cacheable_step(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    step = NoCacheStep()
    pipeline = Pipeline([step, MetricsStep()])
    ctx = FrozenContext({})

    pipeline.run(0, ctx)
    pipeline.run(0, ctx)

    assert step.calls == 2


def test_corrupted_cache_recovers(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    step = CountingStep()
    pipeline = Pipeline([step, MetricsStep()])
    ctx = FrozenContext({})

    pipeline.run(0, ctx)

    step_hash = step.step_hash
    input_hash = compute_hash(0)
    cache_file = tmp_path / ".cache" / step_hash / f"{input_hash}.pkl"
    cache_file.write_text("corrupted")

    step.calls = 0
    pipeline.run(0, ctx)

    assert step.calls == 1


class ReturnStep(PipelineStep):
    cacheable = True

    def __init__(self, value: Any):
        self.value = value

    def __call__(self, data, ctx):
        return self.value

    @property
    def params(self):
        return {}


class Unpickleable:
    def __getstate__(self):  # pragma: no cover - can't pickle
        raise TypeError("unpickleable")


@pytest.mark.parametrize(
    "value,should_fail",
    [(np.zeros((10, 10)), False), (Unpickleable(), True)],
)
def test_cache_large_and_unpickleable(tmp_path, monkeypatch, value, should_fail):
    monkeypatch.chdir(tmp_path)
    step1 = ReturnStep(value)
    pipeline1 = Pipeline([step1, MetricsStep()])
    ctx = FrozenContext({})

    if should_fail:
        with pytest.raises(IOError):
            pipeline1.run(None, ctx)
    else:
        pipeline1.run(None, ctx)
        step2 = ReturnStep(value)
        pipeline2 = Pipeline([step2, MetricsStep()])
        pipeline2.run(None, ctx)
        assert pipeline2.get_provenance()[0]["cache_hit"] is True


def test_cache_dir_permission_error(tmp_path, monkeypatch):
    cache_dir = tmp_path / "cache"
    monkeypatch.setenv("CRYSTALLIZE_CACHE_DIR", str(cache_dir))
    monkeypatch.chdir(tmp_path)

    def deny_open(*args, **kwargs):
        raise PermissionError("read-only")

    monkeypatch.setattr("pathlib.Path.open", deny_open)

    step = CountingStep()
    pipeline = Pipeline([step, MetricsStep()])
    ctx = FrozenContext({})

    with pytest.raises(IOError):
        pipeline.run(0, ctx)


class ParamStep(PipelineStep):
    cacheable = True

    def __init__(self, value: int) -> None:
        self.value = value

    def __call__(self, data, ctx):
        return data + self.value

    @property
    def params(self):
        return {"value": self.value}


def test_step_and_input_hash_uniqueness():
    step1 = ParamStep(1)
    step2 = ParamStep(2)
    assert step1.step_hash != step2.step_hash
    assert compute_hash({"x": 1}) != compute_hash({"x": 2})


def test_concurrent_cache_writes(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    def run(pipe: Pipeline) -> None:
        ctx = FrozenContext({})
        pipe.run(0, ctx)

    pipes = [Pipeline([CountingStep(), MetricsStep()]) for _ in range(5)]
    with ThreadPoolExecutor(max_workers=5) as ex:
        list(ex.map(run, pipes))

    step = CountingStep()
    pipeline = Pipeline([step, MetricsStep()])
    ctx = FrozenContext({})
    pipeline.run(0, ctx)
    assert step.calls == 0
