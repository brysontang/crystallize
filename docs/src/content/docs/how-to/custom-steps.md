---
title: Creating Custom Pipeline Steps
description: How to create reusable pipeline steps using the @pipeline_step decorator.
---

Crystallize pipelines are built from small, deterministic **steps**. This guide shows how to create your own steps with the `@pipeline_step` decorator and how they interact with the immutable context (`ctx`), metrics collection, and caching.

## 1. Define a Step with `@pipeline_step`

Use the decorator on a regular function. The function receives two fixed arguments—`data` and `ctx`—followed by any parameters you define. Parameters can have defaults and are stored in the step for provenance and caching.

```python
from crystallize import pipeline_step
from crystallize.core.context import FrozenContext

@pipeline_step(cacheable=False)
def scale_data(data, ctx: FrozenContext, factor: float = 1.0):
    """Multiply incoming numeric data by ``factor``."""
    return [x * factor for x in data]
```

Calling `scale_data()` returns a `PipelineStep` instance. Pass arguments when creating the instance:

```python
scaler = scale_data(factor=2.0)  # step.params == {"factor": 2.0}
```

Include the step in a `Pipeline` or via `ExperimentBuilder.pipeline([scaler, ...])`.

## 2. Using the Immutable `ctx`

`ctx` is a [`FrozenContext`](../glossary.md#frozencontext) shared across the pipeline. Treatments add keys to it, and steps read them without mutation. Retrieve values with `ctx.get("key", default)` to provide a baseline value when the key is absent.

```python
@pipeline_step()
def normalize(data, ctx: FrozenContext):
    scale = ctx.get("scale_factor", 1.0)  # default when no treatment applies
    return [x / scale for x in data]
```

If a treatment sets `{"scale_factor": 2.0}`, this step automatically uses that value on treatment runs while keeping the baseline path unchanged. Attempting to overwrite an existing key raises `ContextMutationError`.

## 3. Recording Metrics

Each context has a `metrics` object used to accumulate results. Use `ctx.metrics.add(name, value)` to record values in any step. Metrics are aggregated across replicates and passed to hypotheses for verification. The last step may return any data type—returning metrics is optional.

```python
@pipeline_step()
def compute_sum(data, ctx: FrozenContext):
    total = sum(data)
    ctx.metrics.add("sum", total)
    return data
```

Intermediate steps may also write metrics if useful. All metrics collected across replicates are provided to verifiers.

## 4. Enabling Caching

By default steps created with `@pipeline_step` are **not** cached. Set `cacheable=True` on the decorator to store step outputs based on a hash of the step's parameters, the step's code, and the input data. A cached step reruns only when one of these elements changes.

```python
@pipeline_step(cacheable=True)
def heavy_transform(data, ctx: FrozenContext, method: str = "a"):  # expensive work
    return complex_operation(data, method)
```

When the same input data and parameters are seen again, Crystallize loads the result from `.cache/<step_hash>/<input_hash>.pkl` instead of executing the step. Change the parameters, modify the code, or pass different input, and the step runs anew.

Caching is useful for deterministic or long-running operations. Avoid it for highly stochastic steps where reuse would give misleading results.

## Example: Putting It Together

```python
from crystallize import ExperimentBuilder
from crystallize.core.context import FrozenContext

# Step definitions from above
scaler = scale_data(factor=1.5)
normalizer = normalize()
collector = compute_sum()

exp = (
    ExperimentBuilder()
    .datasource(lambda: [1, 2, 3])
    .pipeline([scaler, normalizer, collector])
    .replicates(3)
    .build()
)

result = exp.run()
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
