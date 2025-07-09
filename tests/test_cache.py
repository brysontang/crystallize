from crystallize.core.cache import compute_hash
from crystallize.core.context import FrozenContext
from crystallize.core.pipeline import Pipeline
from crystallize.core.pipeline_step import PipelineStep


class CountingStep(PipelineStep):
    def __init__(self):
        self.calls = 0

    def __call__(self, data, ctx):
        self.calls += 1
        return data + 1

    @property
    def params(self):
        return {}


class MetricsStep(PipelineStep):
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
    @property
    def cacheable(self) -> bool:
        return False


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
