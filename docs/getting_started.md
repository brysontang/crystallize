# Crystallize Framework: Getting Started

Crystallize is a Python framework for reproducible experiments with pipelines, treatments, and hypotheses. It supports caching, immutability, and statistical verification.

## Installation

```bash
pip install crystallize-ml
```

## Quick Example

```python
from crystallize import (
    ExperimentBuilder,
    data_source,
    hypothesis,
    pipeline_step,
    verifier,
    treatment,
)
from crystallize.core.context import FrozenContext

@data_source
def dummy_data(ctx):
    return ctx.get('value', 0)

@pipeline_step()
def process(data, ctx):
    return data + 1

@pipeline_step()
def metrics(data, ctx):
    ctx.metrics.add("result", data)
    return {"result": data}

@verifier
def t_test(baseline, treatment, *, alpha=0.05):
    # Implement or use scipy
    return {"p_value": 0.01, "significant": True}

@hypothesis(verifier=t_test(), metrics="result")
def ranker(res):
    return res["p_value"]

treatment_example = treatment("add_one", {"value": 1})

exp = (
    ExperimentBuilder()
    .datasource(dummy_data)
    .pipeline([process, metrics])
    .treatments([treatment_example])
    .hypotheses([ranker()])
    .replicates(5)
    .parallel(True)  # run replicates concurrently
    .max_workers(4)
    .executor_type("thread")  # use "process" for CPU heavy steps
    .build()
)
result = exp.run()
print(result.metrics)

# Prod apply
output = exp.apply("add_one", data=10)
print(output)
```

## Key Features

- Pipelines with caching.
- Immutable contexts for safety.
- Treatments as dicts or callables.
- Multi-hypothesis verification.
- Fluent builders and prod apply mode.
- Optional parallel execution for heavy experiments.
- Configurable worker count and executor type ("thread" or "process").

For heavy parallel workloads, ensure the cache directory supports file locks or
switch to a thread-safe backend.

For full API, see code/docs. Issues? File at [repo link].
