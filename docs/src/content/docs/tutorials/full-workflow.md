---
title: The Full Workflow
description: Putting optimization, validation, and application together.
---

In this capstone tutorial you'll learn how the three stages of discovery fit together in Crystallize:

- `optimize()` for automated exploration of parameter space.
- `run()` for statistical validation of a promising treatment.
- `apply()` for single-shot inference once a winner is proven.

We'll build a minimal experiment, search for the best parameter, verify it, and finally reuse it.

## Step 1: The Machine – Defining the Experiment

First create the core experiment that stays fixed across all stages.

```python
from crystallize import data_source, pipeline_step
from crystallize.core.context import FrozenContext
from crystallize.core.pipeline import Pipeline
from crystallize.core.pipeline_step import exit_step
from crystallize.core.experiment import Experiment
import random

@data_source
def numbers(ctx: FrozenContext) -> list[int]:
    return [0, 0, 0]

@pipeline_step()
def add_delta(data: list[int], ctx: FrozenContext, *, delta: float = 0.0) -> list[int]:
    return [x + delta for x in data]

@pipeline_step()
def add_noise(data: list[int], ctx: FrozenContext) -> list[int]:
    return [x + random.random() for x in data]

@pipeline_step()
def record_sum(data: list[int], ctx: FrozenContext) -> list[int]:
    ctx.metrics.add("total", sum(data))
    return data

pipeline = Pipeline([add_delta(), add_noise(), exit_step(record_sum())])
datasource = numbers()
exp = Experiment(datasource=datasource, pipeline=pipeline)
exp.validate()
```

This experiment – our *machine* – will be reused for optimization, validation, and application.

## Step 2: Exploration – Finding the Best Parameters with `optimize()`

Define a simple grid search optimizer to explore different `delta` values.

```python
from crystallize.core.optimizers import BaseOptimizer, Objective
from crystallize.core.treatment import Treatment

class GridSearchOptimizer(BaseOptimizer):
    def __init__(self, grid: dict, objective: Objective):
        super().__init__(objective)
        self.grid = grid
        self.index = 0
        self.results: list[float] = []

    def ask(self) -> list[Treatment]:
        val = self.grid["delta"][self.index]
        return [Treatment(name=f"trial_{val}", apply={"delta": val})]

    def tell(self, values: dict[str, float]) -> None:
        self.results.append(list(values.values())[0])
        self.index += 1

    def get_best_treatment(self) -> Treatment:
        best_value = min(self.results)
        best_index = self.results.index(best_value)
        delta = self.grid["delta"][best_index]
        return Treatment(name="best_delta", apply={"delta": delta})

optimizer = GridSearchOptimizer({"delta": [-1, 0, 1]}, Objective("total", "minimize"))
best_treatment = exp.optimize(optimizer, num_trials=3, replicates_per_trial=5)
```

`optimize()` returns a single `Treatment` object – the most promising candidate from the search. It is **not** statistical proof, merely a good lead.

## Step 3: Validation – Proving the Result with `run()`

Now validate that the optimized treatment actually beats the baseline.

```python
from crystallize import hypothesis, verifier
from scipy.stats import ttest_ind

@verifier
def welch_t_test(baseline, treatment, alpha: float = 0.05):
    stat, p = ttest_ind(treatment["total"], baseline["total"], equal_var=False)
    return {"p_value": p, "significant": p < alpha}

@hypothesis(verifier=welch_t_test(), metrics="total")
def rank_by_p_value(result):
    return result.get("p_value", 1.0)

result = exp.run(treatments=[best_treatment], hypotheses=[rank_by_p_value], replicates=30)
print(result.get_hypothesis("rank_by_p_value").results)
```

If the p-value is below your threshold, the treatment is statistically significant – you now have a proven winner.

## Step 4: Deployment – Using the Winner with `apply()`

Finally, reuse the same experiment and treatment for a one-off inference run.

```python
output = exp.apply(treatment=best_treatment)
```

`apply()` runs the pipeline once (stopping at the `exit_step`), executing plugin hooks and step setup/teardown, then returns the final output. This mirrors using your tuned configuration in production.

---

This sequence – **optimize → run → apply** – is the complete Crystallize workflow for turning ideas into validated results and finally real-world usage.

