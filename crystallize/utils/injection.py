from __future__ import annotations

import inspect
from functools import wraps
from typing import Any, Callable

from .context import FrozenContext
from crystallize.datasources import Artifact


def inject_from_ctx(fn: Callable[..., Any]) -> Callable[..., Any]:
    """Inject missing parameters from ``ctx`` when calling ``fn``.

    Parameters not explicitly provided will be looked up in the given
    :class:`FrozenContext` using their parameter name. If a value is not
    present in the context, the parameter's default is used.
    """

    signature = inspect.signature(fn)

    @wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        bound = signature.bind_partial(*args, **kwargs)
        if "ctx" not in bound.arguments:
            raise TypeError("inject_from_ctx requires 'ctx' argument")
        ctx = bound.arguments["ctx"]
        if not isinstance(ctx, FrozenContext):
            raise TypeError("'ctx' must be a FrozenContext")

        for name, param in signature.parameters.items():
            if name in bound.arguments or name == "ctx" or name == "data":
                continue
            default = param.default if param.default is not inspect.Signature.empty else None
            value = ctx.get(name, default)
            if callable(value):
                sig = inspect.signature(value)
                if "ctx" in sig.parameters:
                    value = value(ctx)
                else:
                    value = value()
            bound.arguments[name] = value

        for name, val in list(bound.arguments.items()):
            if isinstance(val, Artifact) and getattr(val, "_ctx", None) is None:
                bound.arguments[name] = val._clone_with_context(ctx)
        return fn(*bound.args, **bound.kwargs)

    return wrapper
