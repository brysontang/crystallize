import pytest
from crystallize.utils.context import FrozenContext
from crystallize.pipelines.pipeline_step import PipelineStep
from crystallize import pipeline_step


class AddStep(PipelineStep):
    def __init__(self, value: int) -> None:
        self.value = value

    def __call__(self, data, ctx):
        return data + self.value

    @property
    def params(self) -> dict:
        return {"value": self.value}


def test_step_hash_reflects_code_and_params():
    """Hash changes when either params *or* code change."""

    # --- same code, different param --------------------------------------
    a1 = AddStep(1)
    a2 = AddStep(2)
    assert a1.step_hash != a2.step_hash

    # --- same param, different code --------------------------------------
    class AddStepV2(AddStep):  # override call, keep same value
        def __call__(self, data, ctx):
            return data + self.value + 10

    b1 = AddStepV2(1)
    assert a1.step_hash != b1.step_hash


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


@pipeline_step()
def no_ctx_step(data, *, inc: int = 1):
    return data + inc


def test_pipeline_step_without_ctx_parameter():
    ctx = FrozenContext({"inc": 2})
    step = no_ctx_step()
    assert step(3, ctx) == 5
