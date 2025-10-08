---
title: Verifying Hypotheses
description: Attach statistical checks to your experiments.
---

Hypotheses bring statistical discipline to your experiments. Each hypothesis couples a **verifier** (statistical test) with a **ranker** (function that scores the verifier’s output so treatments can be ordered).

## 1. Write a Verifier

```python
from crystallize import verifier
from scipy.stats import ttest_ind

@verifier
def welch_t_test(
    baseline: dict[str, list[float]],
    treatment: dict[str, list[float]],
    *,
    alpha: float = 0.05,
) -> dict[str, float | bool]:
    stat, p_value = ttest_ind(
        treatment["total"], baseline["total"], equal_var=False
    )
    return {"p_value": p_value, "significant": p_value < alpha}
```

- `baseline` and `treatment` contain the aggregated metrics recorded by your pipeline (values are lists across replicates).
- Return any dictionary you like; keys become part of the hypothesis result.
- Parameters supplied to the decorated function (e.g., `alpha`) can be overridden when instantiating the verifier: `welch_t_test(alpha=0.01)`.

## 2. Wrap It in a Hypothesis

```python
from crystallize import hypothesis

@hypothesis(verifier=welch_t_test(), metrics="total")
def order_by_p_value(result: dict[str, float]) -> float:
    return result.get("p_value", 1.0)
```

- `metrics="total"` tells Crystallize to pass only the `total` metric into the verifier.
- The decorated function runs once per treatment and should return a scalar. Smaller values rank higher by default.
- Multiple metrics are supported: pass a list of metric names or nested lists for grouped metrics.

## 3. Attach to an Experiment

```python
experiment = (
    Experiment.builder("hypothesis_demo")
    .datasource(fetch_numbers())
    .add_step(add_delta())
    .add_step(summarize())
    .treatments([boost_total()])
    .hypotheses([order_by_p_value])
    .replicates(16)
    .build()
)

result = experiment.run()
hyp = result.get_hypothesis("order_by_p_value")
print(hyp.results)   # {'boost_total': {'p_value': ..., 'significant': True/False}}
print(hyp.ranking)   # {'best': 'boost_total', 'ordered': ['boost_total']}
```

Key fields on the returned `HypothesisResult`:

- `results`: mapping of treatment → verifier output dictionary.
- `ranking["best"]`: treatment name with the lowest ranker value (or `None` if no treatments were active).
- `errors`: list of verifier failures (exceptions are captured so the run continues).

## 4. Display in the CLI

- The run screen’s **Summary** tab has a dedicated Hypotheses table that shows significance flags per treatment.
- Press `S` after a run to jump to the summary; disabled treatments are greyed out.
- Historical metrics (when `ArtifactPlugin(versioned=True)`) can be loaded via `Toggle All Treatments` or persisted summaries.

## 5. Tips

- Hypotheses run after all replicates finish. If you need per-replicate checks, add a pipeline step instead.
- Always record the metrics you reference—missing keys raise `KeyError`. When pipelines return `(data, metrics_dict)`, those metrics are automatically available.
- Multiple hypotheses can share the same verifier with different `alpha` thresholds or metric sets.
- Complex ranking logic (e.g., Pareto comparisons) belongs in the ranker function; return a tuple for lexicographic ordering if needed.
