---
title: Customizing Experiments
description: Configure seeds, parallelism, and validation using ExperimentBuilder and the apply method.
---

Crystallize's `ExperimentBuilder` simplifies assembling an `Experiment` with sensible defaults. This page shows how to tweak important settings—random seeds, parallel execution, and validation—plus how to reuse a built experiment with `.apply()`.

## 1. Build with `ExperimentBuilder`

`ExperimentBuilder` is a fluent factory. Chain methods to define the data source, pipeline, treatments, hypotheses, and other options:

```python
from crystallize import ExperimentBuilder

exp = (
    ExperimentBuilder()
    .datasource(my_source)
    .pipeline([step1, step2])
    .treatments([treatment_a])
    .hypotheses([my_hyp])
    .replicates(3)
    .parallel(True)          # optional
    .seed(42)                # optional
    .build()
)
```

`build()` creates and validates the `Experiment`. You can also call `validate()` manually if constructing an `Experiment` directly.

## 2. Seeding for Reproducibility

Experiments may involve randomness. Control it with three builder methods:

- `.seed(value)`: base seed used for all replicates.
- `.auto_seed(True)`: if enabled (default), each replicate uses `hash(seed + replicate)`.
- `.seed_fn(func)`: custom function run with the computed seed.

The default `seed_fn` only seeds Python's `random` module. Provide your own if you need to seed other libraries:

```python
def custom_seed_function(seed: int) -> None:
    import random
    import numpy as np
    random.seed(seed)
    np.random.seed(seed % (2**32 - 1))

exp = ExperimentBuilder().seed_fn(custom_seed_function)
```

## 3. Parallel Execution

Set `.parallel(True)` to run replicates concurrently. Choose the executor type:

- `executor_type="thread"` (default) for IO-bound steps.
- `executor_type="process"` for CPU-heavy steps that bypass the GIL.
- `.max_workers(n)` limits the number of threads/processes.

Parallelism uses Python's `concurrent.futures`; results match serial execution.

## 4. Validation Rules

An experiment must have a data source and pipeline. If hypotheses are defined, at least one treatment is required. `build()` calls `validate()` automatically and raises `ValueError` if these conditions are not met.

## 5. Reusing Pipelines with `.apply()`

After choosing a treatment, you can pass new data through the pipeline:

```python
result = exp.apply(treatment_name="treatment_a", data=my_data, seed=123)
```

`apply()` runs until the first `exit_step` in the pipeline and returns the data at that point. The optional `seed` is forwarded to the experiment's `seed_fn`; if omitted, the experiment's stored seed is not used. This is handy for debugging or production inference once your treatment is validated.

## Troubleshooting & FAQs

- **`ValueError: Pipeline must contain an exit_step`** – `.apply()` requires at least one `exit_step` to know where to stop.
- **`Unknown treatment`** – The name passed to `treatment_name` must match a treatment from the builder.
- **Parallelism slower?** – Use `process` executors for CPU-bound work and ensure steps release the GIL for threads.

## Next Steps

- Learn to create [custom pipeline steps](custom-steps.md).
- See the [Tutorials: Parallelism](../tutorials/parallelism.md) for performance tips.
