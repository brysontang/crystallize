---
title: LLM Quick Reference
---

Minimal patterns for writing Crystallize code. Copy-paste ready.

## Quickest Start (No Classes)

```python
from crystallize import quick_experiment

def my_function(config):
    # Your logic here
    return {"score": config["x"] * 2}

results = quick_experiment(
    fn=my_function,
    configs={
        "baseline": {"x": 1},
        "treatment": {"x": 10},
    },
    replicates=5,
    seed=42,
)
# results["baseline"] = [{"score": 2}, {"score": 2}, ...]
# results["treatment"] = [{"score": 20}, {"score": 20}, ...]
```

## With Metrics (Still Simple)

```python
from crystallize import quick_experiment

def my_function(config, ctx):
    result = run_something(config)
    ctx.record("accuracy", result.accuracy, tags={"model": config["model"]})
    ctx.record("latency", result.latency)
    return result

results = quick_experiment(
    fn=my_function,
    configs={"gpt4": {"model": "gpt-4"}, "claude": {"model": "claude"}},
    replicates=10,
)
```

## Full Experiment (When You Need More Control)

```python
from crystallize import (
    Experiment,
    Treatment,
    data_source,
    pipeline_step,
    pipeline,
)

# 1. Define data source
@data_source
def my_data(ctx):
    return {"input": [1, 2, 3]}

# 2. Define pipeline step
@pipeline_step()
def process(data, ctx):
    result = sum(data["input"])
    ctx.record("total", result)
    return result

# 3. Create experiment
experiment = Experiment(
    datasource=my_data(),
    pipeline=pipeline(process()),
    replicates=5,
)

# 4. Add treatments (optional)
experiment.treatments = [
    Treatment("doubled", {"multiplier": 2}),
]

# 5. Run
result = experiment.run()

# 6. Access results
print(result.metrics.baseline.metrics["total"])  # [6, 6, 6, 6, 6]
```

## Debug Mode

```python
# Quick single run to test
result = experiment.debug()

# Test specific treatment
result = experiment.debug("doubled")
```

## Save Results

```python
result = experiment.run()

# To JSON
result.to_json("results.json")

# To Parquet (for pandas)
result.to_parquet("results.parquet")
```

## Key Types

| Type | Purpose | Example |
|------|---------|---------|
| `FrozenContext` | Immutable context passed to steps | `ctx.record("x", 1)` |
| `Treatment` | Config variation | `Treatment("name", {"key": value})` |
| `Result` | Experiment output | `result.metrics.baseline.metrics["x"]` |

## Common Patterns

### Reading Config in Steps

```python
@pipeline_step()
def my_step(data, ctx):
    # Read from context (set by treatment)
    multiplier = ctx.get("multiplier", 1)
    return data * multiplier
```

### Multiple Steps

```python
@pipeline_step()
def step1(data, ctx):
    return data + 1

@pipeline_step()
def step2(data, ctx):
    ctx.record("final", data)
    return data

experiment = Experiment(
    datasource=my_data(),
    pipeline=pipeline(step1(), step2()),
)
```

### Standalone Testing

```python
from crystallize import standalone_context

ctx = standalone_context({"input": 42})
result = my_step({"value": 1}, ctx)
print(ctx.metrics["my_metric"])
```

## Plugins

Plugins add cross-cutting behavior without changing your experiment code.

### Built-in Plugins

```python
from crystallize import (
    Experiment,
    SeedPlugin,
    LoggingPlugin,
    ArtifactPlugin,
    ParallelExecution,
    SerialExecution,
)

experiment = Experiment(
    datasource=my_data(),
    pipeline=pipeline(my_step()),
    plugins=[
        SeedPlugin(seed=42, auto_seed=True),      # Reproducibility
        LoggingPlugin(verbose=True),               # Logging
        ArtifactPlugin(root_dir="./data"),         # Save artifacts
        ParallelExecution(max_workers=4),          # Run replicates in parallel
    ],
)
```

| Plugin | Purpose |
|--------|---------|
| `SeedPlugin(seed=42)` | Set random seed for reproducibility |
| `LoggingPlugin(verbose=True)` | Log experiment progress |
| `ArtifactPlugin(root_dir="./data")` | Save `ctx.artifacts` to disk |
| `ParallelExecution(max_workers=4)` | Run replicates in parallel |
| `SerialExecution()` | Run replicates one at a time (default) |

### Custom Plugin

```python
from crystallize import BasePlugin

class MyPlugin(BasePlugin):
    def before_run(self, experiment):
        print(f"Starting {experiment.name}")

    def after_run(self, experiment, result):
        print(f"Done! Baseline metrics: {result.metrics.baseline.metrics}")

    def before_step(self, experiment, step):
        print(f"Running step: {step.__class__.__name__}")

    def after_step(self, experiment, step, data, ctx):
        print(f"Step complete, metrics so far: {ctx.metrics.as_dict()}")

experiment = Experiment(
    datasource=my_data(),
    pipeline=pipeline(my_step()),
    plugins=[MyPlugin()],
)
```

### Plugin Lifecycle

```
before_run()
  └── for each replicate:
        before_replicate()
        └── for each step:
              before_step()
              [step executes]
              after_step()
after_run()
```
