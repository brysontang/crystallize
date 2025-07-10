---
title: Frozen Context
description: Immutable context in the Crystallize framework.
---

## Immutable Context (FrozenContext)

`FrozenContext` is a dictionary-like object that provides an immutable configuration store passed throughout the framework (e.g., to `DataSource`, `PipelineStep`, `Treatment`). It prevents accidental mutations, ensuring thread-safety and reproducibility.

### Why Immutable Context?

Mutable globals or configs can lead to subtle bugs in experiments. By enforcing immutability (you can add new keys but not overwrite existing ones), `FrozenContext` guarantees that configurations are consistent across runs and replicates.

Treatments use this to introduce variations safely, and components like `DataSource` or steps can pull values from it (e.g., paths, params).

### How It Works

- Create: `ctx = FrozenContext({"seed": 42})`
- Access: `ctx["seed"]`
- Add: `ctx["new_key"] = value` (allowed if key doesn't exist)
- Mutate existing: Raises `ContextMutationError`
- As dict: `ctx.as_dict()` (read-only view)

Example:

```python
from crystallize.core.context import FrozenContext

ctx = FrozenContext({"param1": 10})
ctx["param2"] = 20  # OK
try:
    ctx["param1"] = 15  # Raises ContextMutationError
except ContextMutationError:
    pass
print(ctx.as_dict())  # {'param1': 10, 'param2': 20}
```

### Trade-offs

| Aspect                 | Pros                                      | Cons                                        |
| ---------------------- | ----------------------------------------- | ------------------------------------------- |
| **Immutability**       | Deterministic behavior; thread-safe.      | Requires planning all base configs upfront. |
| **Partial Mutability** | Allows extensions (e.g., via Treatments). | Can still grow unexpectedly if not managed. |

Used across [Experiment](#experiment), [Pipeline and Steps](#pipeline-and-steps), [Data Source](#data-source), and [Treatments](#treatments-hypotheses-and-statistical-validation).
