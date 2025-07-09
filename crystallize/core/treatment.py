from typing import Callable, Any
from crystallize.core.context import FrozenContext


class Treatment:
    """
    A named mutator that tweaks parameters for an experiment replicate.

    Args:
        name: Human-readable identifier.
        apply_fn: Callable receiving (ctx) and mutating it by *adding new keys*
                  or overriding step-specific param spaces. Must NOT mutate
                  existing keys – FrozenContext enforces immutability.
    """

    def __init__(self, name: str, apply_fn: Callable[[FrozenContext], Any]):
        self.name = name
        self._apply_fn = apply_fn

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
