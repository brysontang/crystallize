---
title: Building Your First Experiment
description: Assemble a pipeline, treatments, and hypotheses from scratch.
---

This tutorial walks through the same workflow used in `examples/minimal_experiment/main.py`, breaking each piece down so you can adapt it to your own project.

## 1. Datasource

```python
from crystallize import data_source, FrozenContext

@data_source
def fetch_numbers(ctx: FrozenContext) -> list[int]:
    """Return the baseline payload that enters the pipeline."""
    return [0, 0, 0]
```

Datasources can load from disk, call APIs, or synthesise data. They run once per replicate and should be deterministic with respect to the context.

## 2. Pipeline Steps

```python
from crystallize import pipeline_step

@pipeline_step()
def add_delta(data: list[int], ctx: FrozenContext, *, delta: float = 0.0) -> list[float]:
    """Inject a configurable delta (supplied by treatments or defaults)."""
    return [x + delta for x in data]

@pipeline_step()
def summarize(data: list[float], ctx: FrozenContext):
    """Record the total while preserving the data for downstream steps."""
    return data, {"total": sum(data)}
```

Notes:

- Keyword-only parameters (`delta`) are pulled from the context when you instantiate the step without explicitly passing them.
- Returning `(data, metrics)` adds entries to the metrics collector while forwarding the data to the next step.
- Set `@pipeline_step(cacheable=True)` to enable step-level caching. Crystallize hashes the step definition, explicit parameters, and input data before writing to `.cache/`.

## 3. Treatments & Hypotheses

```python
from crystallize import treatment, hypothesis, verifier
from scipy.stats import ttest_ind

boost_total = treatment("boost_total", {"delta": 10.0})

@verifier
def welch_t_test(baseline, treatment, alpha: float = 0.05):
    stat, p_value = ttest_ind(
        treatment["total"], baseline["total"], equal_var=False
    )
    return {"p_value": p_value, "significant": p_value < alpha}

@hypothesis(verifier=welch_t_test(), metrics="total")
def order_by_p_value(result: dict[str, float]) -> float:
    return result.get("p_value", 1.0)
```

- Treatments merge their payload into the context before each replicate. They never mutate existing keys—immutability is enforced by `FrozenContext`.
- Hypotheses pair a verifier (statistical test) with a ranker, so you can sort treatments by any metric you care about.

## 4. Assemble and Run

```python
from crystallize import Experiment, Pipeline, ParallelExecution

experiment = (
    Experiment.builder("basic")
    .datasource(fetch_numbers())
    .add_step(add_delta())
    .add_step(summarize())
    .plugins([ParallelExecution(max_workers=4)])
    .treatments([boost_total()])
    .hypotheses([order_by_p_value])
    .replicates(12)
    .build()
)

result = experiment.run()
```

What you get:

- **Metrics**: `result.metrics.baseline.metrics["total"]` and the treatment equivalent contain per-replicate lists.
- **Hypothesis summary**: `result.get_hypothesis("order_by_p_value").results` returns the p-value and significance flag.
- **Artifacts**: If any step called `ctx.artifacts.add("file.txt", b"...")`, the default `ArtifactPlugin` saves them under `data/basic/v0/replicate_*/...`.

Default plugins (`ArtifactPlugin`, `SeedPlugin`, `LoggingPlugin`) are attached automatically. Override them by passing your own list to `.plugins([...])`.

## 5. Variations to Try

- **Caching**: Add `@pipeline_step(cacheable=True)` to expensive steps and watch the CLI highlight cached runs.
- **Concurrency**: Switch `ParallelExecution` to `ParallelExecution(executor_type="process")` for CPU-bound workloads.
- **More metrics**: Return additional metrics from steps or call `ctx.metrics.add` directly for richer hypothesis inputs.
- **Experiment Graphs**: When you need multi-stage workflows, declare outputs (`Artifact`) and load them from downstream experiments via `ExperimentGraph`.
