import pytest
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
