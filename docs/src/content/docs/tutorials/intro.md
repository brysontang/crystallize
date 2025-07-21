---
title: Getting Started
description: A guide to getting started with Crystallize
---

Welcome to Crystallize, a Python library for running controlled, reproducible experiments in scientific and machine learning workflows. Crystallize emphasizes modular pipelines, data sources, treatments (variations), hypotheses (with statistical verification), caching, and immutable contexts. This tutorial guides beginners through installation and building your first simple experiment step-by-step.

By the end, you'll have a runnable experiment that demonstrates key concepts like data fetching, transformations, variations, and hypothesis testing using SciPy for statistics.

## Prerequisites

- Python 3.10 or later.
- Familiarity with basic Python (functions, classes, imports).
- Basic knowledge of scientific computing (e.g., SciPy for stats, random for noise).

**Terminology Note**: A "treatment" is an experimental variation (e.g., changing a parameter). A "hypothesis" is a verifiable assertion tested against baseline and treatment results using statistical methods.

## Installation

Crystallize is installable via `pip`. If building from source, clone the repository and install dependencies.

```bash
# Install from PyPI (once published)
pip install crystallize-ml

# Or from source (for development)
git clone https://github.com/your-repo/crystallize.git
cd crystallize
pip install -r requirements.txt
pip install -e .
```

Dependencies include SciPy (for statistical tests) and PyYAML (for configuration loading). For full development, use `pixi` as shown in the repository's `pixi.toml`.

**FAQ: Why Pixi?** Pixi manages environments and dependencies reproducibly, similar to Poetry or Conda, ensuring consistent runs across machines.

## Quick Overview

Here's a minimal experiment: Start with simple data, apply transformations with random noise, test a treatment that shifts values, and verify if it improves the sum metric using a t-test.

```python
from crystallize import (
    data_source,
    hypothesis,
    pipeline_step,
    treatment,
    verifier,
)
from crystallize import ParallelExecution, FrozenContext
from scipy.stats import ttest_ind
import random

# 1. Define how to get data
@data_source
def initial_data(ctx: FrozenContext):
    return [0, 0, 0]

# 2. Define the data processing pipeline
@pipeline_step()
def add_delta(data: list, ctx: FrozenContext, *, delta: float = 0.0) -> list:
    """Add a delta value from the context."""
    return [x + delta for x in data]

@pipeline_step()
def add_random(data, ctx: FrozenContext):
    # Add some random noise to the data
    # This removes scipy's "catastrophic cancellation" error
    return [x + random.random() for x in data]

@pipeline_step()
def compute_metrics(data, ctx: FrozenContext):
    # Add the metrics to the context for the hypothesis.
    ctx.metrics.add("result", sum(data))
    return {"result": sum(data)}

# 3. Define the treatment (the change we are testing)
add_ten = treatment(
    name="add_ten_treatment",
    apply={"delta": 10.0} # This dict is added to the context
)

# 4. Define the hypothesis to verify
@verifier
def welch_t_test(baseline, treatment, alpha: float = 0.05):
    t_stat, p_value = ttest_ind(
        treatment["result"], baseline["result"], equal_var=False
    )
    return {"p_value": p_value, "significant": p_value < alpha}

@hypothesis(verifier=welch_t_test(), metrics="result")
def check_for_improvement(res):
    # The ranker function determines the "best" treatment.
    # Lower p-value is better.
    return res.get("p_value", 1.0)

# 5. Build and run the experiment
if __name__ == "__main__":
    experiment = Experiment(
        datasource=initial_data(),
        pipeline=Pipeline([add_delta(), add_random(), compute_metrics()]),
        plugins=[ParallelExecution()],
    )
    experiment.validate()
    result = experiment.run(
        treatments=[add_ten()],
        hypotheses=[check_for_improvement],
        replicates=20,  # Run 20 replicates for statistical power
    )

    # Print the results for our hypothesis
    hyp_result = result.get_hypothesis("check_for_improvement")
    print(hyp_result.results)
```

This code defines an experiment that processes a list of zeros, adds a delta (varied by treatment), introduces noise, computes the sum as a metric, and tests if the treatment significantly increases the sum.

Run it: `python main.py`. Expect output showing hypothesis results (e.g., p-value and significance for the treatment).

**Troubleshooting**: If SciPy import fails, install via `pip install scipy`. For low replicates, significance may vary due to randomness—increase to 50+ for stability.

## Your First Experiment Step-by-Step

Let's build the experiment from the overview, explaining each part.

### Step 1: Define the Data Source

Data sources fetch or generate input data, using the immutable context for parameters.

```python
@data_source
def initial_data(ctx: FrozenContext):
    return [0, 0, 0]
```

This returns a simple list. For details, see Reference: DataSource.

### Step 2: Create Pipeline Steps

Pipelines are sequences of transformations.

```python
@pipeline_step()
def add_delta(data: list, ctx: FrozenContext, *, delta: float = 0.0) -> list:
    return [x + delta for x in data]

@pipeline_step()
def add_random(data, ctx: FrozenContext):
    return [x + random.random() for x in data]

@pipeline_step()
def compute_metrics(data, ctx: FrozenContext):
    ctx.metrics.add("result", sum(data))
    return {"result": sum(data)}
```

These add a delta, introduce noise (to avoid t-test errors), and compute the sum metric.

### Step 3: Define Treatments

Treatments modify the context to create variations.

```python
add_ten = treatment(
    name="add_ten_treatment",
    apply={"delta": 10.0}
)
```

This sets `delta` to 10 in the context for treatment runs.

### Step 4: Set Up Hypotheses

Hypotheses verify assertions with statistical tests.

```python
@verifier
def welch_t_test(baseline, treatment, alpha: float = 0.05):
    t_stat, p_value = ttest_ind(
        treatment["result"], baseline["result"], equal_var=False
    )
    return {"p_value": p_value, "significant": p_value < alpha}

@hypothesis(verifier=welch_t_test(), metrics="result")
def check_for_improvement(res):
    return res.get("p_value", 1.0)
```

Uses SciPy's t-test to check significance, ranking by p-value.

### Step 5: Build and Run

Assemble the experiment directly.

```python
experiment = Experiment(
    datasource=initial_data(),
    pipeline=Pipeline([add_delta(), add_random(), compute_metrics()]),
    plugins=[ParallelExecution()],
)
experiment.validate()
result = experiment.run(
    treatments=[add_ten()],
    hypotheses=[check_for_improvement],
    replicates=20,
)
hyp_result = result.get_hypothesis("check_for_improvement")
print(hyp_result.results)
```

Validate with `experiment.validate()` before running. Results include p-value and significance.

**Inline FAQ: Why add noise?** Identical samples cause SciPy t-test errors; noise simulates real variability.

## Next Steps

- **Add Custom Steps**: See How-to Guides: How to add a custom step.
- **API Details**: Explore Reference: Experiment, Pipeline, Hypothesis.
- **Why Immutability?** Read Explanation: Reproducibility rationale.
- Try the `examples/minimal_experiment` in the codebase for variations. For YAML configs, see How-to: Run from YAML.
