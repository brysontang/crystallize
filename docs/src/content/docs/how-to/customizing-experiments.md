---
title: Customizing Experiments
description: Configure seeds, parallelism, and validation using SeedPlugin, ParallelExecution, and the apply method.
---

Crystallize's `Experiment` class accepts a list of plugins. Use the built-in `SeedPlugin` and `ParallelExecution` to tweak randomness, parallel execution, and other options. This page shows how to customize these settings and how to reuse an experiment with `.apply()`.

## 1. Build an Experiment

Instantiate your components and pass configuration objects:
```python
from crystallize.core.plugins import SeedPlugin
from crystallize.core.execution import ParallelExecution
from crystallize.core.experiment import Experiment
from crystallize.core.pipeline import Pipeline

exp = Experiment(
    datasource=my_source(),
    pipeline=Pipeline([step1(), step2()]),
    plugins=[
        SeedPlugin(seed=42),
        ParallelExecution(),
    ],
)
exp.validate()
```

## 2. Seeding for Reproducibility

The `SeedPlugin` dataclass controls how randomness is managed:

- `seed`: base seed used for all replicates.
- `auto_seed`: when `True` (default), each replicate uses `hash(seed + replicate)`.
- `seed_fn`: custom function run with the computed seed.

Example custom seed function:
```python
$(cat /tmp/custom_seed_snippet.txt)
```

## 3. Parallel Execution

Use `ParallelExecution` to run replicates concurrently. Choose the executor type:

- `executor_type="thread"` (default) for IO-bound steps.
- `executor_type="process"` for CPU-heavy work that bypasses the GIL.
- `max_workers` limits the number of threads/processes.

```python
$(cat /tmp/parallel_snippet.txt)
```

Parallelism uses Python's `concurrent.futures`; results match serial execution.

## 4. Validation Rules

An experiment must have a data source and pipeline. If hypotheses are defined, at least one treatment is required. Call `validate()` to enforce these conditions.

## 5. Reusing Pipelines with `.apply()`

After choosing a treatment, you can pass new data through the pipeline:
```python
result = exp.apply(treatment_name="treatment_a", data=my_data, seed=123)
```

`apply()` runs until the first `exit_step` in the pipeline and returns the data at that point. The optional `seed` is forwarded to the experiment's `seed_fn`; if omitted, the experiment's stored seed is not used. This is handy for debugging or production inference once your treatment is validated.

## Troubleshooting & FAQs

- **`ValueError: Pipeline must contain an exit_step`** – `.apply()` requires at least one `exit_step` to know where to stop.
- **`Unknown treatment`** – The name passed to `treatment_name` must match a treatment in the experiment.
- **Parallelism slower?** – Use `process` executors for CPU-bound work and ensure steps release the GIL for threads.

## Next Steps

- Learn to create [custom pipeline steps](custom-steps.md).
- See the [Tutorials: Parallelism](../tutorials/parallelism.md) for performance tips.
