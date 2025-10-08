---
title: Adding Treatments
description: Introduce controlled variations to compare against the baseline.
---

Treatments represent alternative conditions (hyperparameters, prompt tweaks, model variants) that Crystallize evaluates against the implicit baseline. They work by **adding** keys to the immutable execution context before each replicate.

## 1. Declaring Treatments

```python
from crystallize import treatment, FrozenContext

boost_total = treatment("boost_total", {"delta": 10.0})

@treatment("dynamic_delta")
def dynamic_delta(ctx: FrozenContext):
    ctx.add("delta", ctx.get("delta", 0) + 1.0)
```

- Passing a dictionary returns a ready-to-use `Treatment` that merges those keys into the context.
- Using `@treatment(name)` decorates a callable that receives the context and may add keys programmatically (still without overwriting existing ones).

## 2. Wiring Treatments into the Pipeline

Treatments only have an effect if pipeline steps consume the injected keys. With the pipeline from the previous tutorial:

```python
@pipeline_step()
def add_delta(data: list[int], ctx: FrozenContext, *, delta: float = 0.0) -> list[float]:
    return [x + delta for x in data]
```

- `delta` defaults to `0.0` for the baseline.
- When `boost_total()` runs, `delta` is read from the context (`10.0`).
- Treatments can also add completely new context keys for downstream steps (e.g., `ctx.add("batch_size", 64)`).

## 3. Running with Treatments

```python
experiment = (
    Experiment.builder("with_treatments")
    .datasource(fetch_numbers())
    .add_step(add_delta())
    .add_step(summarize())
    .treatments([boost_total(), dynamic_delta()])
    .replicates(12)
    .build()
)

result = experiment.run()
print(result.metrics.baseline.metrics["total"])
print(result.metrics.treatments["boost_total (v0)"].metrics["total"])
print(result.metrics.treatments["dynamic_delta (v0)"].metrics["total"])
```

Observations:

- The baseline always runs, even if you do not call `.treatments(...)`.
- Treatment metrics are grouped by name and include the artifact version suffix (e.g., `(v0)`).
- Hypotheses receive both baseline and treatment metrics to determine significance.

## 4. Managing Treatments in the CLI

- In the run screen, the right-hand **Treatments** tree lists every treatment attached to the experiment (or each experiment in a graph).
- Press `x` to toggle the highlighted treatment. The state is persisted in `config.state.json`, so the next run remembers disabled variants.
- The summary tab labels disabled treatments and focuses hypothesis output on those that were active.

## 5. Best Practices

- Keep treatments focused—change a single concept so the comparison is easy to interpret.
- Use descriptive names; the name doubles as the directory/metric key.
- If multiple treatments affect the same parameter, consider combining them with `ExperimentGraph` so each experiment stays simple.
- When a treatment needs extra resources (e.g., a model handle), pair it with a `resource_factory` in the pipeline to avoid re-creating the resource every replicate.
