---
title: Treatments, Hypothesis & Statistical Validation
description: Treatments in the Crystallize framework.
---

## Treatments, Hypotheses, and Statistical Validation

These components add experimental variation and rigorous verification to `Experiments`. `Treatment` introduces controlled changes, `Hypothesis` defines testable assertions, and `StatisticalTest` performs the validation.

### Treatments

A `Treatment` is a named function that modifies the execution context (e.g., setting a different data path or hyperparameter), enabling A/B testing or ablation studies. Since it affects the `FrozenContext`, it can influence data fetching or pipeline steps that query the context.

#### Why Treatments?

They provide a clean way to define "what if" scenarios without duplicating code.

#### Example

```python
from crystallize.core import Treatment

def apply_different_data(ctx):
    ctx["csv_path"] = "treatment.csv"  # Sets key used by DataSource

treatment = Treatment(name="better_data", apply_fn=apply_different_data)
```

### Hypotheses

A `Hypothesis` specifies a metric to compare, an optional direction (increase/decrease/equal), and a `StatisticalTest`. It's verified post-experiment using aggregated samples from baseline and treatment runs.

#### Why Hypotheses?

Encourages hypothesis-driven science, automating statistical checks for objectivity.

#### Example

```python
from crystallize.core import Hypothesis
from crystallize.core.stat_test import WelchTTest

hyp = Hypothesis(metric="explained_variance", direction="increase", statistical_test=WelchTTest(), alpha=0.05)
```

### Statistical Validation

Subclass `StatisticalTest` (e.g., `WelchTTest` using `scipy.stats.ttest_ind`) to implement custom tests. It receives sample arrays and returns a dict with `p_value`, `significant`, etc.

#### Why Built-in Stats?

Integrates rigor directly; extensible for custom needs.

#### Flow with Branches

The flow branches on context, but verification aggregates metrics from both.

### Trade-offs

| Aspect                | Pros                          | Cons                                                                           |
| --------------------- | ----------------------------- | ------------------------------------------------------------------------------ |
| **Variations**        | Easy A/B testing via context. | Limited to context mutations (no code changes).                                |
| **Stats Integration** | Reduces manual errors.        | Relies on built-ins; extend for advanced tests (vs. external libs like scipy). |
| **Directionality**    | Clear assertions.             | Optional; without it, only checks significance.                                |

See [Experiment](#experiment) for how they integrate.
