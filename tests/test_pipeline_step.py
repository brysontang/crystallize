import pytest
from crystallize.core.context import FrozenContext
from crystallize.core.pipeline_step import PipelineStep
from crystallize.core.cache import compute_hash
from crystallize.core import pipeline_step


class AddStep(PipelineStep):
    def __init__(self, value: int) -> None:
        self.value = value

    def __call__(self, data, ctx):
        return data + self.value

    @property
    def params(self) -> dict:
        return {"value": self.value}


def test_concrete_step_basic():
    step = AddStep(2)
    ctx = FrozenContext({})
    assert step(3, ctx) == 5
    expected_hash = compute_hash({"class": "AddStep", "params": {"value": 2}})
    assert step.step_hash == expected_hash


@pipeline_step(cacheable=True)
def add(data, ctx, value: int = 1):
    return data + value


@pipeline_step(cacheable=False)
def multiply(data, ctx, factor: int):
    return data * factor


def test_pipeline_step_factory_defaults_and_hash():
    step1 = add()
    step2 = add(value=3)
    ctx = FrozenContext({})
    assert step1(1, ctx) == 2
    assert step2(1, ctx) == 4
    assert step1.cacheable is True
    assert multiply(factor=2).cacheable is False
    assert step1.step_hash == add().step_hash


def test_pipeline_step_factory_missing_param():
    with pytest.raises(TypeError):
        multiply()
