from __future__ import annotations

from typing import List

from crystallize import data_source, pipeline_step
from crystallize.core.context import FrozenContext
from crystallize.core.experiment import Experiment
from crystallize.core.pipeline import Pipeline
from crystallize.core.optimizers import BaseOptimizer, Objective
from crystallize.core.treatment import Treatment


class GridSearchOptimizer(BaseOptimizer):
    def __init__(self, param_grid: dict, objective: Objective):
        super().__init__(objective)
        self.param_grid = param_grid
        self.trial_index = 0
        self.results: List[float] = []

    def ask(self) -> list[Treatment]:
        delta_val = self.param_grid["delta"][self.trial_index]
        params = {"delta": delta_val}
        return [Treatment(name=f"grid_trial_{self.trial_index}", apply=params)]

    def tell(self, objective_values: dict[str, float]) -> None:
        self.results.append(list(objective_values.values())[0])
        self.trial_index += 1

    def get_best_treatment(self) -> Treatment:
        best_value = min(self.results)
        best_index = self.results.index(best_value)
        best_params = {"delta": self.param_grid["delta"][best_index]}
        return Treatment(name="best_grid_search", apply=best_params)


@data_source
def initial_data(ctx: FrozenContext) -> list[int]:
    return [1, 2, 3]


@pipeline_step()
def add_delta(data: list[int], ctx: FrozenContext) -> list[int]:
    return [x + ctx.get("delta", 0) for x in data]


@pipeline_step()
def record_metric(data: list[int], ctx: FrozenContext) -> list[int]:
    ctx.metrics.add("sum", sum(data))
    return data


def main() -> None:
    datasource = initial_data()
    pipeline = Pipeline([add_delta(), record_metric()])
    experiment = Experiment(datasource=datasource, pipeline=pipeline)

    optimizer = GridSearchOptimizer(
        param_grid={"delta": [0, 1, 2]},
        objective=Objective(metric="sum", direction="minimize"),
    )

    best = experiment.optimize(optimizer, num_trials=3, replicates_per_trial=1)
    print(
        f"Best params: {best._apply_fn.__closure__[0].cell_contents if hasattr(best, '_apply_fn') else {}}"
    )


if __name__ == "__main__":
    main()
