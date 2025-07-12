import pytest
from concurrent.futures import ThreadPoolExecutor
from crystallize.core.context import FrozenContext, ContextMutationError


def test_frozen_context_get_set():
    ctx = FrozenContext({'a': 1})
    assert ctx.get('a') == 1

    # adding new key is allowed
    ctx.add('b', 2)
    assert ctx.get('b') == 2

    # attempting to mutate existing key should raise
    with pytest.raises(ContextMutationError):
        ctx['a'] = 3

    as_dict = ctx.as_dict()
    assert as_dict['a'] == 1 and as_dict['b'] == 2


@pytest.mark.parametrize("value", [1, {"x": 1}])
def test_add_existing_key_raises(value):
    ctx = FrozenContext({"a": 1})
    with pytest.raises(ContextMutationError) as exc:
        ctx.add("a", value)
    assert "Cannot mutate existing key: 'a'" in str(exc.value)


@pytest.mark.parametrize("default", [None, 0, {}])
def test_get_missing_returns_default(default):
    ctx = FrozenContext({})
    result = ctx.get("missing", default)
    assert result == default
    if isinstance(default, dict):
        assert result.get("foo") is None


def test_metrics_accumulates_without_mutation():
    ctx = FrozenContext({})
    ctx.metrics.add("a", 1)
    ctx.metrics.add("a", 2)
    assert ctx.metrics["a"] == (1, 2)


def test_context_handles_empty_and_nested_values():
    source = {"nested": {"x": 1}}
    ctx = FrozenContext(source)
    source["nested"]["x"] = 2
    # deep immutability: source mutations should not affect context
    assert ctx.get("nested")["x"] == 1
    nested = ctx.get("nested")
    nested["x"] = 3
    assert ctx.get("nested")["x"] == 1


def test_context_as_dict_is_read_only():
    ctx = FrozenContext({})
    view = ctx.as_dict()
    with pytest.raises(TypeError):
        view["new"] = 1
    ctx.metrics.add("a", 1)
    metrics_view = ctx.metrics.as_dict()
    with pytest.raises(TypeError):
        metrics_view["b"] = (2,)
    with pytest.raises(AttributeError):
        metrics_view["a"].append(2)


def test_nested_values_not_deep_copied_but_immutable_view():
    import copy

    source = {"nested": [1]}
    ctx = FrozenContext(source)
    view = ctx.as_dict()
    view["nested"].append(2)
    assert ctx["nested"] == [1]

    ctx_deep = FrozenContext(copy.deepcopy(source))
    source["nested"].append(3)
    assert ctx_deep["nested"] == [1]


def test_metrics_thread_safety():
    ctx = FrozenContext({})

    def add_many(_: int) -> None:
        for _ in range(100):
            ctx.metrics.add("x", 1)

    with ThreadPoolExecutor(max_workers=4) as ex:
        ex.map(add_many, range(4))

    assert len(ctx.metrics["x"]) == 400 and all(v == 1 for v in ctx.metrics["x"])


def test_metrics_thread_safe_adds():
    from concurrent.futures import ThreadPoolExecutor

    ctx = FrozenContext({})

    def add_metric(i: int) -> None:
        ctx.metrics.add("key", i)

    with ThreadPoolExecutor(5) as ex:
        ex.map(add_metric, range(5))

    vals = ctx.metrics["key"]
    assert sorted(vals) == [0, 1, 2, 3, 4]
