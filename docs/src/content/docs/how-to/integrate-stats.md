---
title: Integrating Statistical Tests
description: Add statistical verifiers and hypotheses to analyze experiment outcomes.
---

Crystallize separates data processing from statistical evaluation. **Verifiers** implement a statistical test and **Hypotheses** use them to compare baseline and treatment metrics.

## 1. Create a Verifier

Use the `@verifier` decorator on a function that accepts baseline and treatment metric samples. Return any dictionary of results. This example wraps SciPy's Welch t-test:

```python
from crystallize import verifier
from scipy.stats import ttest_ind

@verifier
def welch_t_test(baseline, treatment, *, alpha: float = 0.05):
    t_stat, p_value = ttest_ind(
        treatment["score"], baseline["score"], equal_var=False
    )
    return {"p_value": p_value, "significant": p_value < alpha}
```

Instantiate it with parameters if needed: `t_test = welch_t_test(alpha=0.01)`.

## 2. Define a Hypothesis

Hypotheses specify which metrics feed the verifier and how to rank treatments. Provide a single metric name, a list of names, or a list of metric groups.

```python
from crystallize import hypothesis

@hypothesis(verifier=welch_t_test(), metrics="score")
def rank_by_p(result):
    return result.get("p_value", 1.0)
```

- `metrics="score"` passes one metric list to the verifier.
- Use `metrics=["a", "b"]` to pass multiple lists.
- Use `metrics=[["a"], ["b"]]` to run the verifier on each group separately. The `verify()` result mirrors the grouping (single dict or list of dicts).

## 3. Run the Experiment

Add the hypothesis to your `ExperimentBuilder` and run as usual:

```python
exp = (
    ExperimentBuilder()
    .datasource(my_source)
    .pipeline(my_pipeline)
    .treatments([my_treatment])
    .hypotheses([rank_by_p])
    .replicates(10)
    .build()
)

result = exp.run()
print(result.get_hypothesis("rank_by_p").results)
```

The `results` attribute contains the verifier output per treatment, and `ranking` orders treatments using the ranker.

## Troubleshooting & FAQs

- **MissingMetricError** – Ensure all metric keys specified in `metrics` exist in `ctx.metrics`.
- **Multiple metrics** – When using metric groups, the verifier runs separately for each group and returns a list of results.
- **Custom statistics** – Your verifier can call any library (SciPy, PyTorch, etc.) as long as it returns a dictionary.

## Next Steps

- Review [Custom Pipeline Steps](custom-steps.md) to compute the metrics you need.
- See [Customizing Experiments](customizing-experiements.md) for seeding and parallel options.
