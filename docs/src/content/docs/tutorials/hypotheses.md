---
title: Verifying Hypotheses
description: How to verify hypotheses in an experiment.
---

In this tutorial, you'll add hypotheses to your experiment, enabling statistical verification of assertions against baseline and treatment results. Building on previous guides, we'll extend the Titanic age normalization example: After fetching data, normalizing ages (with optional scaling from treatments), and computing metrics, we'll test if the treatment significantly affects the standard deviation of normalized ages (or another metric).

Hypotheses provide scientific rigor by quantifying whether variations (treatments) lead to meaningful changes, using verifiers like t-tests. By the end, you'll run an experiment that ranks treatments based on p-values and checks significance.

**Term Definitions**:

- **Hypothesis**: A verifiable assertion (e.g., "Treatment increases mean age") with a statistical verifier and ranker function.
- **Verifier**: A callable that compares baseline/treatment metric samples, returning stats (e.g., p-value).
- **Ranker**: Scores verifier results to rank treatments (e.g., by p-value).

**Goal**: Verify if age scaling (treatment) significantly alters normalized age std (expect no change, as normalization is scale-invariant—demo hypothesis rejection).

## Prerequisites

- Completed "Adding Variations" (or familiar with DataSource, Pipeline, Treatments).
- SciPy installed (`pip install scipy`) for t-test.
- Pandas for DataFrames.

## Step 1: Review the Base Setup

Use your `adding_treatments.py` from the previous tutorial. It includes:

- DataSource: Samples random Titanic ages.
- Pipeline: Scales (if treatment), normalizes 'Age', computes 'std_norm_age' (~1) and 'mean_age'.
- Treatment: 'scale_ages_treatment' adds {"scale_factor": 1.5}.

Add imports for hypotheses:

```python
from crystallize import hypothesis, verifier  # For assertions and stats wrappers
from scipy.stats import ttest_ind  # SciPy t-test
```

## Step 2: Define the Verifier

Verifiers compare metric samples from baseline and treatments, returning a dict of stats (e.g., p-value, significance).

```python
# Custom verifier: t-test on metric samples
@verifier
def age_std_t_test(baseline_samples, treatment_samples, alpha: float = 0.05):
    """
    t-test: Is treatment std significantly different?
    - baseline_samples/treatment_samples: Dict of metric lists.
    - alpha: Significance threshold.
    Returns: Dict with p_value and significant.
    """
    from scipy.stats import ttest_ind  # Import inside if optional
    stat, p = ttest_ind(
        treatment_samples["std_norm_age"],
        baseline_samples["std_norm_age"],
        equal_var=False  # Welch's for unequal variance
    )
    return {"p_value": p, "significant": p < alpha}
```

- **How it works**: `@verifier` creates a factory. Instantiate with params: `v = age_std_t_test(alpha=0.01)`.
- **Test it**: `print(age_std_t_test({"std_norm_age": [1,1]}, {"std_norm_age": [1.1,1.2]}))` → Dict with p_value.

**Inline Troubleshooting**:

- _ValueError: Single metric only?_ Check that your metrics specification selects exactly one entry when required.
- _NaN/Inf in samples?_ Clean data in pipeline (e.g., `data.dropna()`).
- FAQ: Wrap SciPy functions with `@verifier` for convenience, or implement domain-specific tests manually.

## Step 3: Define the Hypothesis

Hypotheses tie verifiers to metrics and add a ranker for treatment ordering.

```python
# Hypothesis: Test if treatment changes std (expect not significant)
Hypothesis(verifier=age_std_t_test(), metrics="std_norm_age", name="std_change_hyp")
```

- **How it works**: `Hypothesis` class, links verifier and metrics.
- **Multi-metrics**: Set `metrics=["std_norm_age", "mean_age"]` for joint verification.
- **Test it**: Hypotheses run post-experiment; mock: `hyp.verify({"std_norm_age": [1]}, {"std_norm_age": [1]})`.

**Inline Troubleshooting**:

- _MissingMetricError?_ Ensure pipeline computes/adds required metrics via `ctx.metrics.add`.
- _Ranker fails?_ Handle missing keys: Use `result.get("key", default)`.
- FAQ: Why ranker? For multi-treatment experiments, identifies "best" (e.g., lowest p-value).

## Step 4: Integrate and Run

Add to builder; run to verify.

```python
# Update build with hypothesis
exp = Experiment(
    datasource=titanic_source(),
    pipeline=Pipeline([normalize_age(), compute_metrics()]),
    plugins=[ParallelExecution()],
)
exp.validate()

# Run and inspect hypothesis
result = exp.run(
    treatments=[scale_ages()],
    hypotheses=[rank_by_p_value],  # Add here
    replicates=20,  # Increase for stats power
)
hyp_result = result.get_hypothesis("std_change_hyp")
print("Hypothesis results:", hyp_result.results)  # e.g., {'scale_ages_treatment': {'p_value': ~1, 'significant': False}}
print("Ranking:", hyp_result.ranking)  # Best treatment (likely none significant)
```

- **Output**: Verifier dict per treatment; ranking by score.
- **Interpretation**: High p-value (>0.05) → No significant change (normalization invariant to scaling).
- **Provenance**: Includes hypothesis for full repro.

**Inline Troubleshooting**:

- _No hypotheses results?_ Ensure treatments present (hypotheses need variations).
- _Low power?_ Increase replicates (20+ for t-test); add noise if samples identical.
- FAQ: Multiple hypotheses? Add to `.hypotheses([...])`; each verifies independently.

## Full Updated Script

`verifying_hypotheses.py` (extend from adding_treatments):

```python
from crystallize import data_source, pipeline_step, treatment, hypothesis, verifier
from crystallize import ParallelExecution, FrozenContext
import pandas as pd
import random
from scipy.stats import ttest_ind, skew, kurtosis

@data_source
def titanic_source(ctx: FrozenContext):
    data = {'Age': [22.0, 38.0, 26.0, 35.0, 35.0, 54.0, 27.0, 14.0]}
    random.seed(ctx.get("seed", 42))
    indices = random.sample(range(len(data['Age'])), 3)
    sampled_data = {'Age': [data['Age'][i] for i in indices]}
    return pd.DataFrame(sampled_data)

@pipeline_step()
def normalize_age(
    data: pd.DataFrame,
    ctx: FrozenContext,
    *,
    scale_factor: float = 1.0,
) -> pd.DataFrame:
    scale = scale_factor + random.random()
    data['Age'] = data['Age'] * scale
    mean_age = data['Age'].mean()
    std_age = data['Age'].std()
    data['Normalized_Age'] = (data['Age'] - mean_age) / std_age
    return data

@pipeline_step()
def compute_metrics(data: pd.DataFrame, ctx: FrozenContext):
    std_norm_age = data['Normalized_Age'].std()
    ctx.metrics.add("std_norm_age", std_norm_age)

    mean_age = data['Age'].mean()
    ctx.metrics.add("mean_age", mean_age)

    return {"std_norm_age": std_norm_age, "mean_age": mean_age}

scale_ages = treatment(name="scale_ages_treatment", apply={"scale_factor": 1.5})

@verifier
def age_std_t_test(baseline_samples, treatment_samples, alpha: float = 0.05):
    stat, p = ttest_ind(treatment_samples["std_norm_age"], baseline_samples["std_norm_age"], equal_var=False)
    return {"p_value": p, "significant": p < alpha}

hyp = Hypothesis(verifier=age_std_t_test(), metrics="std_norm_age", name="std_change_hyp")

if __name__ == "__main__":
    exp = Experiment(
        datasource=titanic_source(),
        pipeline=Pipeline([normalize_age(), compute_metrics()]),
        plugins=[ParallelExecution()],
    )
    exp.validate()
    result = exp.run(
        treatments=[scale_ages()],
        hypotheses=[hyp],
        replicates=20,
    )
    hyp_result = result.get_hypothesis("std_change_hyp")
    print("Hypothesis results:", hyp_result.results)
    print("Ranking:", hyp_result.ranking)
```

Run: `python verifying_hypotheses.py`. Expect high p-value (not significant), confirming normalization's scale-invariance.

## Next Steps

- **Parallelism/Caching**: See How-to Guides: Enable parallelism and caching.
- **API Details**: Reference: Hypothesis, Verifier.
- **Concepts**: Explanation: Statistical rigor in experiments.
- Add multi-metrics hypothesis (e.g., test "mean_age" too). Explore `examples/csv_pipeline_example` for real stats on CSV data.
