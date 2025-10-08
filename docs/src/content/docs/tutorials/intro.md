---
title: Getting Started
description: A tour of the core Crystallize concepts with a runnable example.
---

This tutorial introduces the main ideas behind Crystallize—immutable execution contexts, pipeline steps, treatments, hypotheses, and the default plugin stack—using the same code that powers `examples/minimal_experiment`.

## 1. Define the Building Blocks

```python
from crystallize import (
    Experiment,
    Pipeline,
    ParallelExecution,
    FrozenContext,
    data_source,
    pipeline_step,
    treatment,
    hypothesis,
    verifier,
)
from scipy.stats import ttest_ind

@data_source
def initial_data(ctx: FrozenContext) -> list[int]:
    return [0, 0, 0]

@pipeline_step()
def add_delta(data: list[int], ctx: FrozenContext, *, delta: float = 0.0) -> list[float]:
    return [x + delta for x in data]

@pipeline_step()
def track_sum(data: list[float], ctx: FrozenContext):
    return data, {"total": sum(data)}

boost_total = treatment("boost_total", {"delta": 10.0})

@verifier
def welch_t_test(baseline, treatment, alpha: float = 0.05):
    stat, p_value = ttest_ind(
        treatment["total"], baseline["total"], equal_var=False
    )
    return {"p_value": p_value, "significant": p_value < alpha}

@hypothesis(verifier=welch_t_test(), metrics="total")
def ordered_by_p_value(result: dict[str, float]) -> float:
    return result.get("p_value", 1.0)
```

What’s happening:

- `@data_source` turns `initial_data` into a callable that produces the first payload passed to the pipeline.
- `@pipeline_step` wraps a function into a `PipelineStep`. Keyword-only parameters are injected from the immutable `FrozenContext` unless supplied explicitly. Returning `(data, metrics)` records additional metrics without mutating the context.
- `treatment()` declares a variation that merges the provided dictionary into the context before each replicate.
- `@verifier` + `@hypothesis` pair a statistical test with a ranking function. Hypotheses receive aggregated metrics once all replicates finish.

## 2. Build and Run the Experiment

```python
experiment = (
    Experiment.builder("demo")
    .datasource(initial_data())
    .add_step(add_delta())
    .add_step(track_sum())
    .plugins([ParallelExecution(max_workers=4)])
    .treatments([boost_total()])
    .hypotheses([ordered_by_p_value])
    .replicates(10)
    .build()
)

result = experiment.run()
print(result.metrics.baseline.metrics)
print(result.get_hypothesis("ordered_by_p_value").results)
```

The builder attaches three default plugins:

- `ArtifactPlugin(root_dir="data")` persists artifacts and metrics under `data/<experiment>/vN/`.
- `SeedPlugin(auto_seed=True)` seeds Python’s RNG per replicate. Provide `SeedPlugin(seed=42)` to create reproducible seeds across runs.
- `LoggingPlugin` writes structured logs to the `crystallize` logger.

## 3. Inspect the Output

- `result.metrics.baseline.metrics["total"]` contains a list of replicate totals for the baseline.
- `result.metrics.treatments["boost_total (v0)"].metrics["total"]` stores the treatment metrics. The `(v0)` suffix indicates which artifact version produced the results.
- `result.get_hypothesis("ordered_by_p_value").results` returns a dictionary with the p-value and significance flag from the verifier.
- `result.print_tree()` renders execution provenance (step timings and context additions) for debugging.

## 4. CLI Equivalents

The exact same experiment can be created with the CLI scaffold:

1. Run `crystallize` and press `n` to open **Create New Experiment**.
2. Generate an experiment with `datasources.py`, `steps.py`, and `verifiers.py` populated with example code.
3. Edit `config.yaml` to add the `boost_total` treatment and attach the hypothesis.
4. Press `Enter` to run it from the TUI. The summary tab highlights metrics, hypotheses, and stored artifacts; `x` toggles treatments and `l` switches between rerunning and using cached outputs.

## 5. Where to Go Next

- Increase `replicates` and observe how the summary aggregates metrics.
- Introduce your own treatments (next tutorial) or replace the verifier with a custom statistical check.
- Use `Experiment.from_yaml(...)` to load folder-based experiments and wire multiple stages together with `ExperimentGraph`.
