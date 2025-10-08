---
title: Parameter Optimization
description: Use the ask/tell loop to search over treatments programmatically.
---

Crystallize ships with a simple optimisation hook that lets you drive experiments from an external strategy (grid search, Bayesian optimisation, evolutionary algorithms, …). The pattern mirrors [ask/tell](https://en.wikipedia.org/wiki/Sequential_model-based_optimization): the optimiser proposes a treatment, Crystallize evaluates it, and the optimiser consumes the aggregated metric.

## 1. Implement a `BaseOptimizer`

```python
from crystallize.experiments.optimizers import BaseOptimizer, Objective
from crystallize import Treatment

class GridSearchOptimizer(BaseOptimizer):
    def __init__(self, deltas: list[float], objective: Objective):
        super().__init__(objective)
        self.deltas = deltas
        self._index = 0
        self._scores: list[float] = []

    def ask(self) -> list[Treatment]:
        delta = self.deltas[self._index]
        return [Treatment(name=f"grid_{delta}", apply={"delta": delta})]

    def tell(self, objective_values: dict[str, float]) -> None:
        self._scores.append(next(iter(objective_values.values())))
        self._index += 1

    def get_best_treatment(self) -> Treatment:
        best_idx = min(range(len(self._scores)), key=self._scores.__getitem__)
        return Treatment(name="grid_best", apply={"delta": self.deltas[best_idx]})
```

Key points:

- `Objective.metric` names the metric to optimise (must exist in `ctx.metrics`). The current helper averages the metric across replicates.
- `ask()` returns a list of treatments. The built-in extraction assumes exactly one treatment per trial.
- `tell()` receives a `{metric_name: aggregated_value}` mapping.

## 2. Configure the Experiment

```python
@data_source
def initial_data(ctx: FrozenContext) -> list[int]:
    return [1, 2, 3]

@pipeline_step()
def add_delta(data: list[int], ctx: FrozenContext, *, delta: float = 0.0) -> list[int]:
    return [x + delta for x in data]

@pipeline_step()
def record_sum(data: list[int], ctx: FrozenContext):
    ctx.metrics.add("sum", sum(data))
    return data

experiment = Experiment(
    datasource=initial_data(),
    pipeline=Pipeline([add_delta(), record_sum()]),
)

optimizer = GridSearchOptimizer(
    deltas=[0.0, 1.0, 2.0],
    objective=Objective(metric="sum", direction="minimize"),
)
```

## 3. Run the Loop

```python
best_treatment = experiment.optimize(
    optimizer,
    num_trials=len(optimizer.deltas),
    replicates_per_trial=1,
)
print(best_treatment.name, best_treatment._apply_value)  # internal representation
```

`Experiment.optimize` (synchronous) calls the async helper under the hood:

1. Call `ask()` to obtain a treatment.
2. Run the experiment with that treatment (respecting `replicates_per_trial`).
3. Average the specified metric across replicates and hand it to `tell()`.
4. Repeat for `num_trials`.
5. Return `get_best_treatment()`.

You can also call `await experiment.aoptimize(...)` inside your own async code.

## 4. Tips

- Use `direction` to indicate how you interpret the metric (currently informational; implement minimisation/maximisation logic in `tell()`).
- You can access full metrics inside `tell()` by running the experiment manually and extracting whatever you need before calling `tell()`. The built-in helper only passes the average of the named metric.
- To evaluate multiple treatments per trial, extend `_extract_objective_from_result` or run the experiment yourself and call `optimizer.tell(...)` with whatever aggregation makes sense.
- Optimisation is orthogonal to the CLI. Run the optimisation loop in Python and then apply the returned treatment in production via `experiment.apply(best_treatment)`.
