from typing import Any, Callable, Mapping, Union
from crystallize.core.context import FrozenContext


class Treatment:
    """
    A named mutator that tweaks parameters for an experiment replicate.

    Args:
        name: Human-readable identifier.
        apply: Either a callable ``apply(ctx)`` or a mapping of key-value pairs
            to add to the context. The callable form allows dynamic logic while
            the mapping form simply inserts the provided keys. Existing keys
            must not be mutated – ``FrozenContext`` enforces immutability.
    """

    def __init__(
        self,
        name: str,
        apply: Union[Callable[[FrozenContext], Any], Mapping[str, Any]],
    ):
        self.name = name
        if callable(apply):
            self._apply_fn = apply
        else:
            def _apply_fn(ctx: FrozenContext, items=apply) -> None:
                for k, v in items.items():
                    ctx.add(k, v)

            self._apply_fn = _apply_fn

    # ---- framework use --------------------------------------------------

    def apply(self, ctx: FrozenContext) -> None:
        """
        Apply the treatment to the execution context.

        Implementations typically add new keys like:

            ctx['embed_dim'] = 512
            ctx.override(step='hpo', param_space={'lr': [1e-4, 5e-5]})

        Raises:
            ContextMutationError if attempting to overwrite existing keys.
        """
        self._apply_fn(ctx)

    # ---- dunder helpers -------------------------------------------------

    def __repr__(self) -> str:  # pragma: no cover
        return f"Treatment(name='{self.name}')"
