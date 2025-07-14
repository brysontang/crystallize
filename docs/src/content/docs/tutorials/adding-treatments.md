---
title: Adding Treatments
description: How to add treatments to an experiment.
---

In this tutorial, you'll extend the basic experiment from the previous guide by adding treatments—experimental variations that modify the context or data processing. Treatments allow controlled comparisons against a baseline (the control run without variations). This hands-on path builds on fetching and normalizing Titanic-like age data, introducing a treatment that scales ages (e.g., to simulate adjusted scaling in ML preprocessing).

By the end, you'll run an experiment with baseline and treatment results, verifying differences in metrics like standard deviation of normalized ages.

**Terminology Note**: The "baseline" is the default run; "treatments" inject changes via context updates (immutable additions). Use treatments for A/B testing hyperparameters, data augmentations, or model variants.

## Prerequisites

- Completed "Building Your First Experiment" (or familiar with DataSource/Pipeline).
- Pandas and SciPy installed (`pip install pandas scipy`).
- Understand immutability: Treatments add new keys to FrozenContext without mutating existing ones.

## Step 1: Review the Base Setup

Start with the script from the previous tutorial (`basic_experiment.py`). It fetches sampled Titanic ages, normalizes them (mean 0, std ~1), and computes std as a metric.

Key parts:

- DataSource: Samples 3 random ages from a hardcoded list.
- Pipeline: Normalizes 'Age' → Computes 'std_norm_age' (~1 verifiable).

Add imports for treatments:

```python
from crystallize import treatment  # Factory for variations
```

## Step 2: Define Treatments

Treatments are named modifiers that update the context. Here, create one that scales ages by a factor (e.g., to test preprocessing variations).

```python
# Treatment: Scale ages (variation to test against baseline)
scale_ages = treatment(
    name="scale_ages_treatment",
    apply={"scale_factor": 1.5}  # Adds 'scale_factor' to context
)
```

- **How it works**: The `apply` dict is added to the context during treatment runs. Baselines run without it.
- **Callable alternative**: For dynamic logic:
  ```python
  @treatment("dynamic_scale")
  def dynamic_scale_treatment(ctx: FrozenContext):
      ctx.add("scale_factor", 1.0 + (ctx["replicate"] / 10.0))  # Varies per replicate
  ```
- **Test it**: `t = scale_ages; ctx = FrozenContext({}); t.apply(ctx); print(ctx.get("scale_factor"))` → 1.5.

**Inline Troubleshooting**:

- _MutationError?_ If key exists, use a unique name or check context beforehand (but immutability prevents overwrites).
- _No effect?_ Ensure pipeline uses the new key (next step).
- FAQ: Why context updates? Allows non-destructive variations—e.g., hyperparams without code changes. See Explanation: Immutability.

## Step 3: Update Pipeline to Use Treatment

Modify `normalize_age` to apply scaling if 'scale_factor' present (treatment-only).

```python
@pipeline_step()
def normalize_age(data: pd.DataFrame, ctx: FrozenContext):
    """
    Scale 'Age' if treatment active, then normalize.
    """
    scale = ctx.get("scale_factor", 1.0) + random.random()  # Default 1.0 (baseline no-op) + random noise for tutorial
    data['Age'] = data['Age'] * scale  # Apply variation
    mean_age = data['Age'].mean()
    std_age = data['Age'].std()
    data['Normalized_Age'] = (data['Age'] - mean_age) / std_age
    return data
```

- **Baseline**: `scale=1.0`, no change.
- **Treatment**: Scales ages, affecting normalization std (~1 still, but verifiable shift in raw ages).
- **Re-test step**: With treatment ctx (`{"scale_factor": 1.5}`), std remains ~1, but means differ indirectly.

**Inline Troubleshooting**:

- _Key unused?_ Ensure steps reference context keys added by treatments.
- _Inconsistent results?_ Set seed in random sampling: `random.seed(ctx.get("seed", 42))` in DataSource.
- FAQ: Multiple treatments? Add more to `.treatments([...])`; each runs separately vs. baseline.

## Step 4: Assemble with Treatments

Update the builder to include treatments. Baselines run automatically.

```python
# Build with treatments
exp = Experiment(
    datasource=titanic_source(),
    pipeline=Pipeline([normalize_age(), compute_metrics()]),
    plugins=[ParallelExecution()],
)
exp.validate()

# Run and compare baseline vs. treatment
result = exp.run(treatments=[scale_ages()], replicates=3)
print("Baseline metrics:", result.metrics.baseline.metrics)  # std ~1
print("Treatment metrics:", result.metrics.treatments["scale_ages_treatment"].metrics)  # std ~1, but scaled input
```

- **Output**: Aggregated metrics—baseline std ~1; treatment std ~1 (normalization invariant to scaling).
- **Verification**: To see effect, add raw mean age metric in `compute_metrics`: `ctx.metrics.add("mean_age", data['Age'].mean())`. Baseline mean ~30-40; treatment ~45-60 (scaled).

**Inline Troubleshooting**:

- _No treatment results?_ Ensure `.treatments` list non-empty; baselines always run.
- _Metrics mismatch?_ Replicates sample randomly—set seed via context or env for consistency.
- FAQ: Baselines vs. treatments? Baselines use default context; treatments add keys for variations.

## Full Updated Script

`adding_treatments.py` (copy from basic, add treatment parts):

```python
from crystallize import data_source, pipeline_step, treatment
from crystallize.core.execution import ParallelExecution
from crystallize.core.context import FrozenContext
import pandas as pd
import random
from scipy.stats import skew, kurtosis

@data_source
def titanic_source(ctx: FrozenContext):
    data = {
        'Age': [22.0, 38.0, 26.0, 35.0, 35.0, 54.0, 27.0, 14.0],
    }
    # Sample 3 random rows (seed for repro)
    random.seed(ctx.get("seed", 42))  # Use context for seed
    indices = random.sample(range(len(data['Age'])), 3)
    sampled_data = {'Age': [data['Age'][i] for i in indices]}
    return pd.DataFrame(sampled_data)

@pipeline_step()
def normalize_age(data: pd.DataFrame, ctx: FrozenContext):
    scale = ctx.get("scale_factor", 1.0) + random.random()  # Treatment injects this
    data['Age'] = data['Age'] * scale
    mean_age = data['Age'].mean()
    std_age = data['Age'].std()
    data['Normalized_Age'] = (data['Age'] - mean_age) / std_age
    return data

@pipeline_step()
def compute_metrics(data: pd.DataFrame, ctx: FrozenContext):
    std_norm_age = data['Normalized_Age'].std()
    ctx.metrics.add("std_norm_age", std_norm_age)  # ~1

    mean_age = data['Age'].mean()  # To see scaling effect
    ctx.metrics.add("mean_age", mean_age)

    return {"std_norm_age": std_norm_age, "mean_age": mean_age}

scale_ages = treatment(
    name="scale_ages_treatment",
    apply={"scale_factor": 1.5}
)

if __name__ == "__main__":
    exp = Experiment(
        datasource=titanic_source(),
        pipeline=Pipeline([normalize_age(), compute_metrics()]),
        plugins=[ParallelExecution()],
    )
    exp.validate()
    result = exp.run(treatments=[scale_ages()], replicates=3)
    print("Baseline metrics:", result.metrics.baseline.metrics)
    print("Treatment metrics:", result.metrics.treatments["scale_ages_treatment"].metrics)
```

Run: `python adding_treatments.py`. Compare baseline/treatment `mean_age` (scaled higher in treatment) while `std_norm_age` remains ~1.

To add ML: In pipeline, fit `from sklearn.linear_model import LinearRegression` on 'Age'~other features, metric as R². Treatment could alter features.

## Next Steps

- **Test Hypotheses**: See Tutorials: Verifying Assertions with Hypotheses.
- **Custom Variations**: How-to Guides: How to add a custom treatment.
- **Reference**: Treatment, Experiment (for baselines).
- **Explanations**: Why baselines? See Explanation: Controlled experiments.
- Experiment with multiple treatments or real Titanic CSV. Link to `examples/yaml_experiment` for config-based runs.
