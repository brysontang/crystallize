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
