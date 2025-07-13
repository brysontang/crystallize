---
title: Building Your First Experiment
description: A guide to building your first experiment with Crystallize
---

In this tutorial, you'll build a basic experiment focusing on the DataSource (for fetching input data) and Pipeline (for processing it). We'll use a small subset of the Titanic dataset (hardcoded for simplicity; in practice, load from CSV via pandas). This hands-on guide assumes you've installed Crystallize and run the intro example from Getting Started.

The goal: Fetch Titanic-like passenger data, normalize the 'Age' column (simple transformation), and compute the mean age as a metric. This prepares for treatments/hypotheses in later tutorials.

**Note**: For real workflows, download Titanic CSV (e.g., from https://raw.githubusercontent.com/datasciencedojo/datasets/master/titanic.csv) and use `pandas.read_csv` in your DataSource. Here, we hardcode a subset to keep it self-contained.

## Step 1: Set Up Your Script

Create `basic_experiment.py` and import essentials:

```python
from crystallize import (
    ExperimentBuilder,   # To assemble the experiment
    data_source,         # Decorator for data fetchers
    pipeline_step,       # Decorator for transformation steps
)
from crystallize.core.context import FrozenContext  # Immutable context
import pandas as pd  # For data handling (assumes pandas installed)
```

These provide factories for sources and steps. For details, see Reference: DataSource and PipelineStep.

## Step 2: Define the DataSource

The DataSource generates a small Titanic-like DataFrame.

```python
# Define data source with hardcoded Titanic subset
@data_source
def titanic_source(ctx: FrozenContext):
    """
    Generate small Titanic-like data (subset for demo).
    - ctx: Immutable context (unused here).
    Returns: pandas DataFrame.
    """
    data = {
        'Age': [22.0, 38.0, 26.0, 35.0, 35.0, 54.0, 27.0, 14.0],
    }
    # Sample 3 random rows from the data
    indices = random.sample(range(len(data['Age'])), 3)
    sampled_data = {'Age': [data['Age'][i] for i in indices]}

    return pd.DataFrame(sampled_data)
```

- **How it works**: `@data_source` turns this into a factory. Instantiate as `source = titanic_source()`.
- **Test it**: `source = titanic_source(); print(source.fetch(FrozenContext({})).head())` → Shows DF.
- **Real-world**: Replace hardcoded data with `pd.read_csv('titanic.csv')` or URL fetch (if internet available).

**Inline Troubleshooting**:

- _Pandas not found?_ Install via `pip install pandas` (optional but useful for data tasks).
- _Data empty?_ Ensure return is non-empty; add checks like `if df.empty: raise ValueError`.
- FAQ: Why DataFrame? Crystallize handles any data type (lists, arrays)—DF is common for ML.

For CSV loading examples, see `examples/csv_pipeline_example/datasource.py`.

## Step 3: Build the Pipeline

Pipeline steps transform the DataFrame. Record metrics with `ctx.metrics.add` so hypotheses can verify them later.

```python
from scipy.stats import skew, kurtosis

# Pipeline step: Simple verifiable transformation (normalize Age)
@pipeline_step()
def normalize_age(data: pd.DataFrame, ctx: FrozenContext):
    mean_age = data['Age'].mean()
    std_age = data['Age'].std()
    data['Normalized_Age'] = (data['Age'] - mean_age) / std_age
    return data

@pipeline_step()
def compute_metrics(data: pd.DataFrame, ctx: FrozenContext):
    std_norm_age = data['Normalized_Age'].std()
    ctx.metrics.add("std_norm_age", std_norm_age)  # expect ≈ 1

    # Optional metrics to explore distribution shape further:
    # from scipy.stats import skew, kurtosis
    # age_skewness = skew(data['Normalized_Age'])
    # age_kurtosis = kurtosis(data['Normalized_Age'])
    # ctx.metrics.add("age_skewness", age_skewness)
    # ctx.metrics.add("age_kurtosis", age_kurtosis)

    return data
```

- **Assembly**: `pipeline_steps = [normalize_age, compute_metrics]`.
- **Transformation**: Normalizes Age (verifiable: mean should be ~0).
- **Test a step**: `step = normalize_age(); df = pd.DataFrame({'Age': [20,30]}); print(step(df, FrozenContext({}))['Normalized_Age'].mean())` → 0.0.

**Inline Troubleshooting**:

- _KeyError: Column missing?_ Check prior steps add required columns; use `if 'col' not in data`.
- _Caching fails?_ Ensure params/input hashable; avoid non-deterministic code unless `cacheable=False`.
- _Mutation error?_ Don't modify ctx existing keys—use `ctx.add`.
- FAQ: Where do metrics come from? Steps add values to `ctx.metrics`; hypotheses aggregate them across replicates.

For advanced steps like PCA, see `examples/csv_pipeline_example/steps/pca.py`.

## Step 4: Assemble and Run

Build and execute:

```python
# Build experiment
exp = (
    ExperimentBuilder()
    .datasource(titanic_source)                # Set source
    .pipeline([normalize_age, compute_metrics]) # Chain steps
    .replicates(3)                             # Multiple runs (though data same here)
    .seed(42)                                  # Set seed for reproducibility
    .build()
)

# Run and inspect
result = exp.run()
print("Baseline metrics:", result.metrics.baseline.metrics)
# e.g., {'mean_norm_age': (0.0, 0.0, 0.0)}  # Mean normalized is always 0
```

- **Output**: Metrics from replicates (mean ~0, verifiable transformation).
- **Provenance**: `print(result.provenance)` for reproducibility.

**Inline Troubleshooting**:

- _Validation error?_ Ensure `.validate()` or build succeeds—needs source/pipeline.
- _Metrics empty?_ Verify `ctx.metrics.add` is called in your steps.
- FAQ: Replicates with same data? Adds variability if steps random; prepares for stats.

## Full Script

`basic_experiment.py`:

```python
from crystallize import ExperimentBuilder, data_source, pipeline_step
from crystallize.core.context import FrozenContext
import pandas as pd
import random  # Unused here, but for future noise
from scipy.stats import skew, kurtosis

@data_source
def titanic_source(ctx: FrozenContext):
    data = {
        'Age': [22.0, 38.0, 26.0, 35.0, 35.0, 54.0, 27.0, 14.0],
    }
    # Sample 3 random rows from the data
    indices = random.sample(range(len(data['Age'])), 3)
    sampled_data = {'Age': [data['Age'][i] for i in indices]}

    return pd.DataFrame(sampled_data)

@pipeline_step()
def normalize_age(data: pd.DataFrame, ctx: FrozenContext):
    mean_age = data['Age'].mean()
    std_age = data['Age'].std()
    data['Normalized_Age'] = (data['Age'] - mean_age) / std_age
    print(data['Normalized_Age'])
    return data

@pipeline_step()
def compute_metrics(data: pd.DataFrame, ctx: FrozenContext):
    std_norm_age = data['Normalized_Age'].std()
    ctx.metrics.add("std_norm_age", std_norm_age)  # expect ≈ 1

    # Optional metrics to explore distribution shape further:
    # from scipy.stats import skew, kurtosis
    # age_skewness = skew(data['Normalized_Age'])
    # age_kurtosis = kurtosis(data['Normalized_Age'])
    # ctx.metrics.add("age_skewness", age_skewness)
    # ctx.metrics.add("age_kurtosis", age_kurtosis)

    return data

if __name__ == "__main__":
    exp = (
        ExperimentBuilder()
        .datasource(titanic_source)
        .pipeline([normalize_age, compute_metrics])
        .replicates(3)
        .seed(42)
        .build()
    )
    r = exp.run()

    print("Baseline metrics:", r.metrics.baseline.metrics)

```

Run: `python basic_experiment.py`. Verify mean_norm_age is 0.0 (simple transformation check).

To train linear regression: Add a step using statsmodels (available in code env) to fit OLS on Age~Fare, metric as R-squared.

## Next Steps

- **Add Variations**: See Tutorials: Adding Treatments and Hypotheses.
- **ML Models**: Extend pipeline with regression—see How-to: Integrate ML steps.
- **Reference**: Pipeline, DataSource.
- **Explanations**: Caching in pipelines—see Explanation: Reproducibility.
- Download full Titanic CSV and update DataSource for real data. See `examples/csv_pipeline_example` for CSV handling.
