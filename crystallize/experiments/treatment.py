from typing import Any, Callable, Mapping, Union
from crystallize.utils.context import FrozenContext


# Add this helper class at the top of the file
class _MappingApplier:
    """A picklable callable that applies a mapping to a context."""

    def __init__(self, items: Mapping[str, Any]):
        self.items = items

    def __call__(self, ctx: FrozenContext) -> None:
        for k, v in self.items.items():
            ctx.add(k, v)


class Treatment:
    """Set up initial context values for a replicate.

    Unlike plugins, a treatment does not hook into the execution lifecycle; it
    simply mutates the :class:`FrozenContext` before the pipeline starts.  The
    ``apply`` argument can be a callable or a mapping providing the context
    additions.

    Args:
        name: Human-readable identifier for the treatment.
        apply: Either a callable ``apply(ctx)`` or a mapping of keys to insert.
            Existing keys must not be mutated—``FrozenContext`` enforces this
            immutability.
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

            self._apply_fn = _MappingApplier(apply)

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
