---
title: Creating Custom Pipeline Steps
description: How to create reusable pipeline steps using the @pipeline_step decorator.
---

Crystallize pipelines are built from small, deterministic **steps**. This guide shows how to create your own steps with the `@pipeline_step` decorator and how they interact with the immutable context (`ctx`), metrics collection, and caching.

## 1. Define a Step with `@pipeline_step`

Use the decorator on a regular function. `data` and `ctx` are required
arguments. Additional keyword arguments make your step configurable and are
automatically pulled from the execution context when not supplied explicitly.

```python
from crystallize import pipeline_step
from crystallize import FrozenContext

@pipeline_step(cacheable=True)
def scale_data(data: list, ctx: FrozenContext, *, factor: float = 1.0) -> list:
    """Multiply incoming numeric data by ``factor``.

    The ``factor`` parameter is automatically populated from the context if it
    exists, otherwise its default is used.
    """
    return [x * factor for x in data]
```

Calling `scale_data()` returns a `PipelineStep` instance. You can create one
directly or pass parameters with `functools.partial` when adding it to a
pipeline:

```python
from functools import partial

scaler = scale_data(factor=2.0)  # explicit instantiation
# or later:
steps = [partial(scale_data, factor=2.0), normalize]
```

Either form works with `a Pipeline`.

## 2. Automatic Parameter Injection

Any keyword argument in the step signature (besides ``data`` and ``ctx``) will be
looked up in the :class:`FrozenContext` when the step runs. This keeps your
dependencies explicit and avoids repetitive ``ctx.get()`` calls.

The ``scale_data`` function above demonstrates this pattern—``factor`` is pulled
from the context if you don't provide it when constructing the step.

## 3. When to Use ``ctx``

The context object is still important for information that isn't represented by
parameters. Examples include:

- reading ``ctx.get('replicate')`` to know the current replicate number
- recording metrics with ``ctx.metrics.add()``
- saving files or other artifacts via ``Artifact.write()``

Use parameter injection for simple values and fall back to ``ctx`` for these
framework features.

```python
@pipeline_step()
def normalize(data: list, ctx: FrozenContext) -> list:
    scale = ctx.get("scale_factor", 1.0)
    return [x / scale for x in data]
```

## 4. Recording Metrics

Each context has a `metrics` object used to accumulate results. Use `ctx.metrics.add(name, value)` to record values in any step. Metrics are aggregated across replicates and passed to hypotheses for verification. The last step may return any data type—returning metrics is optional.

```python
@pipeline_step()
def compute_sum(data, ctx: FrozenContext):
    total = sum(data)
    ctx.metrics.add("sum", total)
    return data
```

Intermediate steps may also write metrics if useful. All metrics collected across replicates are provided to verifiers.

## 5. Enabling Caching

By default steps created with `@pipeline_step` are **not** cached. Set `cacheable=True` on the decorator to store step outputs based on a hash of the step's parameters, the step's code, and the input data. A cached step reruns only when one of these elements changes.

```python
@pipeline_step(cacheable=True)
def heavy_transform(data, ctx: FrozenContext, method: str = "a"):  # expensive work
    return complex_operation(data, method)
```

When the same input data and parameters are seen again, Crystallize loads the result from `.cache/<step_hash>/<input_hash>.pkl` instead of executing the step. Change the parameters, modify the code, or pass different input, and the step runs anew.

Caching is useful for deterministic or long-running operations. Avoid it for highly stochastic steps where reuse would give misleading results.

If your step generates random numbers, configure a reproducible seed using
`SeedPlugin(seed=value)` or provide a custom `seed_fn`
for library-specific RNGs. See
[Tutorial: Basic Experiment](../tutorials/basic-experiment.md#step-4-assemble-and-run)
for examples of seeding experiments.

## Example: Putting It Together

```python
from functools import partial
from crystallize import ParallelExecution, Experiment, Pipeline, FrozenContext

# Step definitions from above
exp = Experiment(
    datasource=lambda ctx: [1, 2, 3],
    pipeline=Pipeline([
        partial(scale_data, factor=1.5),
        normalize(),
        compute_sum(),
    ]),
    plugins=[ParallelExecution()],
)
exp.validate()
result = exp.run(replicates=3)
print(result.metrics.baseline.metrics)

```
This small experiment scales and normalizes data, then records the sum metric for each replicate.

## Troubleshooting & FAQs

- **Why can't my step modify `ctx` directly?** `FrozenContext` is immutable to avoid side effects. Use `ctx.add()` only to add new keys (usually inside treatments).
- **Metrics missing in the result?** Verify each step calls `ctx.metrics.add` for values you want to analyze.
- **Caching not taking effect?** Verify `cacheable=True`, parameters are hashable, and that the input data is identical between runs.

## Next Steps

- Learn how to add [custom treatments](../tutorials/adding-treatments.md) to pass values into `ctx`.
- See the [Reference: PipelineStep](../glossary.md#pipelinestep) for API details.
- Explore [Explanation: Reproducibility](../index.mdx#what-is-crystallize) for more on caching and context design.
