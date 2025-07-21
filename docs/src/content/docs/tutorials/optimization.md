---
title: Parameter Optimization
description: Explore the optimize -> run -> apply workflow with a simple grid search optimizer.
---

Crystallize experiments can go beyond fixed A/B tests. The `optimize()` method allows you to iterate over many treatments and search for the best configuration.

## Step 1: Understand the `BaseOptimizer`

```python
from dataclasses import dataclass
from crystallize.experiments.optimizers import BaseOptimizer, Objective
from crystallize import Treatment

@dataclass
class Objective:
    metric: str
    direction: str  # "minimize" or "maximize"

class BaseOptimizer(ABC):
    def __init__(self, objective: Objective):
        self.objective = objective

    def ask(self) -> list[Treatment]:
        raise NotImplementedError

    def tell(self, objective_values: dict[str, float]) -> None:
        raise NotImplementedError

    def get_best_treatment(self) -> Treatment:
        raise NotImplementedError
```

Every optimizer implements `ask`, `tell`, and `get_best_treatment` to drive the trial loop.

## Step 2: Implement `GridSearchOptimizer`

```python
class GridSearchOptimizer(BaseOptimizer):
    def __init__(self, param_grid: dict, objective: Objective):
        super().__init__(objective)
        self.param_grid = param_grid
        self.trial_index = 0
        self.results: list[float] = []

    def ask(self) -> list[Treatment]:
        delta = self.param_grid["delta"][self.trial_index]
        return [Treatment(name=f"trial_{self.trial_index}", apply={"delta": delta})]

    def tell(self, objective_values: dict[str, float]) -> None:
        self.results.append(list(objective_values.values())[0])
        self.trial_index += 1

    def get_best_treatment(self) -> Treatment:
        best_idx = self.results.index(min(self.results))
        return Treatment(name="best", apply={"delta": self.param_grid["delta"][best_idx]})
```

The optimizer cycles through the provided grid and records the metric returned from each trial.

## Step 3: Run Optimization

```python
from crystallize import data_source, pipeline_step
from crystallize import Experiment
from crystallize.pipelines.pipeline import Pipeline

@data_source
def initial_data(ctx):
    return [1, 2, 3]

@pipeline_step()
def add_delta(data: list, ctx, *, delta: int = 0) -> list:
    return [x + delta for x in data]

@pipeline_step()
def record_sum(data, ctx):
    ctx.metrics.add("total", sum(data))
    return data

exp = Experiment(datasource=initial_data(), pipeline=Pipeline([add_delta(), record_sum()]))
optimizer = GridSearchOptimizer({"delta": [0, 1, 2]}, Objective("total", "minimize"))

best = exp.optimize(optimizer, num_trials=3)
```

`best` is the `Treatment` with the lowest recorded sum.

## Step 4: Validate the Winner

After finding the best parameters you can verify they beat the baseline:

```python
from crystallize import Hypothesis

def always_better(baseline, treatment):
    return {"p_value": 0.01, "accepted": True, "significant": True}

hyp = Hypothesis(verifier=always_better, metrics="total", ranker=lambda r: r["p_value"])

result = exp.run(treatments=[best], hypotheses=[hyp], replicates=3)
print(result.metrics)
```

## Step 5: Apply the Winning Treatment

Use `apply()` to run the pipeline once with the optimized parameters:

```python
output = exp.apply(treatment=best)
```

This final step mirrors the real-world rollout of the chosen configuration. `apply()` triggers plugin hooks and step setup/teardown so the run behaves like a single replicate of `run()`.

