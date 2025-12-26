from __future__ import annotations

import inspect
from functools import wraps
from typing import Any, Callable

from .context import FrozenContext
from crystallize.datasources import Artifact


class _Missing:
    """Sentinel that survives deepcopy for FrozenContext.get."""

    def __repr__(self) -> str:
        return "<missing>"

    def __deepcopy__(self, memo: Any) -> "_Missing":
        return self


_MISSING = _Missing()


def inject_from_ctx(fn: Callable[..., Any]) -> Callable[..., Any]:
    """Inject missing parameters from ``ctx`` when calling ``fn``.

    Parameters not explicitly provided will be looked up in the given
    :class:`FrozenContext` using their parameter name. If a value is not
    present in the context, the parameter's default is used.
    """

    signature = inspect.signature(fn)
    has_ctx_param = "ctx" in signature.parameters

    @wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        if has_ctx_param:
            bound = signature.bind_partial(*args, **kwargs)
            if "ctx" not in bound.arguments:
                raise TypeError("inject_from_ctx requires 'ctx' argument")
            ctx = bound.arguments["ctx"]
        else:
            if "ctx" in kwargs:
                ctx = kwargs.pop("ctx")
            elif len(args) >= 2:
                ctx = args[1]
                args = args[:1] + args[2:]
            else:
                raise TypeError("inject_from_ctx requires 'ctx' argument")
            bound = signature.bind_partial(*args, **kwargs)
        if not isinstance(ctx, FrozenContext):
            raise TypeError("'ctx' must be a FrozenContext")

        for name, param in signature.parameters.items():
            if name in bound.arguments or name == "ctx" or name == "data":
                continue
            value = ctx.get(name, _MISSING)
            if value is _MISSING:
                if param.default is not inspect.Signature.empty:
                    value = param.default
                else:
                    raise TypeError(
                        f"Dependency Injection Error: Parameter '{name}' in step '{fn.__name__}' "
                        f"is not found in the Context and has no default value."
                    )
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

        if has_ctx_param:
            bound.arguments["ctx"] = ctx

        return fn(*bound.args, **bound.kwargs)

    return wrapper
