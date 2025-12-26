---
title: Customizing Experiments
description: Adjust seeding, parallelism, and reuse experiments for single-shot runs.
---

The `Experiment` constructor accepts plugins and an optional initial context. Use these hooks to control determinism, execution strategy, and shared resources.

## 1. Default Plugins (and Overrides)

When you build an experiment (either manually or via `Experiment.builder()`), Crystallize ensures three plugins exist:

- `ArtifactPlugin(root_dir="data")`
- `SeedPlugin(auto_seed=True)`
- `LoggingPlugin(verbose=False)`

You can replace them by supplying your own list:

```python
from crystallize import Experiment, Pipeline, SeedPlugin, ParallelExecution, LoggingPlugin

experiment = Experiment(
    datasource=my_source(),
    pipeline=Pipeline([step_one(), step_two()]),
    plugins=[
        SeedPlugin(seed=1234, auto_seed=True),
        ParallelExecution(max_workers=4, executor_type="process"),
        LoggingPlugin(verbose=True, log_level="DEBUG"),
    ],
)
```

## 2. Seeding Strategies

`SeedPlugin` exposes three knobs:

- `seed`: base integer. When provided, replicate `r` gets `(seed + r * 31337) % 2**32`.
- `auto_seed`: set to `False` to reuse the master seed for every replicate; omit the plugin to manage randomness manually.
- `seed_fn`: custom callable invoked with the computed seed (ideal for seeding NumPy, PyTorch, etc.).

```python
import numpy as np

def seed_all(seed: int) -> None:
    import random

    random.seed(seed)
    np.random.seed(seed % (2**32 - 1))

seeded = SeedPlugin(seed=123, seed_fn=seed_all)
```

If you omit `seed_fn`, Crystallize seeds both Python's `random` module and NumPy with the computed value.
The selected seed is stored in the context under `"seed_used"` and appears in the provenance tree.
Thread executors share global RNG state; Crystallize emits a warning when SeedPlugin is combined with `executor_type="thread"`. Use processes when you need strict reproducibility.

## 3. Shared Resources via `resource_factory`

If the pipeline needs a reusable object (e.g., a database client), add it to `initial_ctx` using `resource_factory`. The factory runs once per worker and caches the resource.

```python
from crystallize import resource_factory
from crystallize.utils.context import FrozenContext

def connect(ctx: FrozenContext):
    import sqlite3

    return sqlite3.connect(":memory:")

experiment = Experiment(
    datasource=my_source(),
    pipeline=Pipeline([...]),
    initial_ctx={"db": resource_factory(connect)},
)
```

Process-based execution requires that factories be picklable; wrapping them with `resource_factory` satisfies that requirement.

## 4. Choosing an Execution Strategy

```python
ParallelExecution(max_workers=8, executor_type="process")
AsyncExecution()
SerialExecution()
```

- Use threads for IO-heavy steps, processes for CPU-bound work (objects must be picklable), and `AsyncExecution` when your steps are `async def`.
- The CLI exposes `l` to toggle caching (per step or experiment) and updates the execution strategy automatically (`"resume"` for cached runs, `"rerun"` when caching is disabled).

## 5. Reusing the Experiment with `apply()`

After identifying a winning treatment, reuse the same experiment for inference:

```python
result = experiment.run(treatments=[best], replicates=40)

single_output = experiment.apply(
    treatment=best,
    data={"numbers": [10, 20, 30]},  # optional override for the datasource output
    seed=999,                        # optional override seed forwarded to SeedPlugin
)
```

- `apply()` runs the pipeline exactly once, triggers plugin hooks, and returns the final data payload.
- Passing `data` skips the datasource (useful for serving inference). When omitted, `datasource.fetch` runs as usual.
- `seed` is optional; if provided, it flows through the configured `seed_fn`.

## 6. Validation Helpers

`experiment.validate()` checks basic invariants (datasource + pipeline exist). You can call it proactively when building experiments programmatically or rely on the CLI to surface configuration errors while loading `config.yaml`.

## 7. Troubleshooting

- **Pickling errors with parallelism** – ensure pipeline steps, datasources, and any objects captured by closures live at module scope. Use `resource_factory` for non-picklable objects.
- **Randomness still drifting** – verify that all randomness goes through libraries seeded in your custom `seed_fn`. Some libraries (e.g., PyTorch) require extra flags for determinism.
- **Slow parallel runs** – start with `executor_type="thread"` for IO workloads; processes only help when the work releases the GIL.
