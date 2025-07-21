---
title: Scaling with Replicates and Parallelism
description: How to scale experiments using replicates and parallelism.
---

In this how-to guide, you'll learn to scale experiments using replicates (for statistical reliability) and parallelism (for faster execution). Replicates run the pipeline multiple times, building sample distributions for robust hypothesis testing. Parallelism leverages thread or process pools to speed up independent runs, ideal for CPU/IO-bound tasks.

We'll extend the Titanic age normalization experiment: Increase replicates for better t-test power and enable parallelism to reduce runtime. This creates "aha" moments by showing how replicates reveal variability and parallelism cuts wait times.

**Why Replicates?** Single runs lack stats; replicates (e.g., 20+) enable verifiers like t-tests to detect significance amid noise.

**Why Parallelism?** Replicates are independent—run concurrently to scale horizontally. Use "thread" for IO/light tasks, "process" for CPU-heavy (bypasses GIL).

**Term Note**: Replicates are per-condition (baseline + each treatment). Parallelism uses Python's concurrent.futures; set `max_workers` to control threads/processes.

## Step 1: Update for Replicates

Start with your script from "Verifying Hypotheses." Add replicates in the builder—higher numbers improve power but increase compute.

```python
# In your experiment build (increase replicates for stats)
exp = Experiment(
    datasource=titanic_source(),
    pipeline=Pipeline([normalize_age(), compute_metrics()]),
    plugins=[ParallelExecution()],
)
exp.validate()
result = exp.run(treatments=[scale_ages()], hypotheses=[rank_by_p_value], replicates=50)
print("Replicate count in metrics:", len(result.metrics.baseline.metrics["std_norm_age"]))  # 50
```

- **How it works**: Each replicate fetches data, runs pipeline, aggregates metrics. Baseline/treatments each get 50 samples.
- **Test**: Run with 5 first (quick), then 50—note stable p-values.

**Inline Troubleshooting**:

- _Runtime too long?_ Start low (10); enable parallelism next.
- _Metrics vary little?_ Add noise in pipeline (e.g., `data['Age'] += random.gauss(0,1)` with seed).
- FAQ: Minimum replicates? 30+ for t-tests; depends on effect size—see Explanation: Statistical Rigor.

## Step 2: Enable Parallelism

Add `.parallel(True)` and configure executor. For CPU-bound (e.g., heavy math), use "process"; default "thread" for general.

```python
# Full build with parallelism
exp = Experiment(
    datasource=titanic_source(),
    pipeline=Pipeline([normalize_age(), compute_metrics()]),
    plugins=[ParallelExecution(max_workers=4, executor_type="process")],
)
exp.validate()

import time  # To measure speed
start = time.time()
result = exp.run(treatments=[scale_ages()], hypotheses=[rank_by_p_value], replicates=50)
print("Runtime:", time.time() - start)  # Faster with parallel
print("Hypothesis p-value:", result.get_hypothesis("std_change_hyp").results["scale_ages_treatment"]["p_value"])
```

- **How it works**: Replicates run in pool; provenance logs hits if cached.
- **Timing**: Serial: ~linear with replicates; parallel: ~divided by workers.
- **Test**: Compare runtimes with/without `.parallel(True)`.

**Inline Troubleshooting**:

- _Invalid executor_type?_ Only "thread"/"process"—check spelling.
- _Memory errors?_ Reduce `max_workers` or replicates; process uses more RAM.
- _No speedup?_ If steps IO-bound, try "thread"; ensure replicates > workers.
- FAQ: When "process"? CPU tasks (e.g., ML training); "thread" for data loading. See codebase `core/experiment.py` for VALID_EXECUTOR_TYPES.

## Step 3: Add Caching for Efficiency

Steps do not cache by default (hash on params/input). In high-replicate runs, cache hits speed repeats.

```python
# Example cacheable step (from pipeline; already @pipeline_step(cacheable=True))
@pipeline_step(cacheable=True)  # Explicit for clarity
def normalize_age(
    data: pd.DataFrame,
    ctx: FrozenContext,
    *,
    scale_factor: float = 1.0,
) -> pd.DataFrame:
    # ... (as before)
    return data
```

- **Verify**: After first run, re-run—provenance shows "cache_hit: True" for unchanged steps.
- **Disable**: Set `cacheable=False` for random/non-deterministic.

**Inline Troubleshooting**:

- _Cache misses?_ Changes in ctx/input reset hash; check provenance["input_hash"].
- _Corrupted cache?_ Delete `.cache/` dir; tool recovers automatically.
- FAQ: Custom cache dir? Set env `CRYSTALLIZE_CACHE_DIR=path`. See Explanation: Caching for Reproducibility.

## Full Script with Scaling

Updated `scaling_experiment.py` (from verifying_hypotheses, add scaling):

```python
from crystallize import data_source, pipeline_step, treatment, hypothesis, verifier
from crystallize import ParallelExecution, FrozenContext
import pandas as pd
import random
from scipy.stats import ttest_ind

@data_source
def titanic_source(ctx: FrozenContext):
    data = {'Age': [22.0, 38.0, 26.0, 35.0, 35.0, 54.0, 27.0, 14.0]}
    random.seed(ctx.get("seed", 42))
    indices = random.sample(range(len(data['Age'])), 3)
    sampled_data = {'Age': [data['Age'][i] for i in indices]}
    return pd.DataFrame(sampled_data)

@pipeline_step(cacheable=True)
def normalize_age(
    data: pd.DataFrame,
    ctx: FrozenContext,
    *,
    scale_factor: float = 1.0,
) -> pd.DataFrame:
    scale = scale_factor
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

@hypothesis(verifier=age_std_t_test(), metrics="std_norm_age", name="std_change_hyp")
def rank_by_p_value(result):
    return result.get("p_value", 1.0)

if __name__ == "__main__":
    import time
    exp = Experiment(
        datasource=titanic_source(),
        pipeline=Pipeline([normalize_age(), compute_metrics()]),
        plugins=[ParallelExecution(max_workers=4, executor_type="process")],
    )
    exp.validate()
    start = time.time()
    result = exp.run(
        treatments=[scale_ages()],
        hypotheses=[rank_by_p_value],
        replicates=50,  # Scaled for power
    )
    print("Runtime:", time.time() - start)
    hyp_result = result.get_hypothesis("std_change_hyp")
    print("Hypothesis results:", hyp_result.results)
    print("Provenance (sample):", result.provenance)  # Check cache hits
```

Run: `python scaling_experiment.py`. Note faster runtime with parallelism; stable p-value with high replicates.

## Next Steps

- **Custom Verifiers**: How-to Guides: How to add a custom step (adapt for verifiers).
- **API Details**: Reference: Experiment (replicates/parallel options).
- **Concepts**: Explanation: Reproducibility rationale (caching/parallel in rigor).
- Scale to 100+ replicates on real Titanic CSV. Explore `examples/csv_pipeline_example` for parallel PCA.
