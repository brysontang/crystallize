import pytest
from crystallize.core.context import FrozenContext
from crystallize.core.datasource import DataSource
from crystallize.core import data_source


class DummySource(DataSource):
    def __init__(self) -> None:
        self.called = False

    def fetch(self, ctx: FrozenContext) -> int:
        self.called = True
        return ctx.get("value", 0)


def test_datasource_subclass_called_with_context():
    src = DummySource()
    ctx = FrozenContext({"value": 3})
    assert src.fetch(ctx) == 3
    assert src.called is True


@data_source
def function_source(ctx: FrozenContext, base: int, inc: int = 1) -> int:
    return ctx["replicate"] + base + inc


def test_data_source_factory_and_params():
    src = function_source(base=2, inc=2)
    ctx = FrozenContext({"replicate": 5})
    assert src.fetch(ctx) == 9


def test_data_source_missing_param_raises():
    with pytest.raises(TypeError):
        function_source()
