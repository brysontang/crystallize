
from crystallize.core.experiment import Experiment
from crystallize.core.optimizers import BaseOptimizer, Objective
from crystallize.core.pipeline import Pipeline
from crystallize.core.treatment import Treatment
from examples.optimization_experiment import main as opt_example


class MockOptimizer(BaseOptimizer):
    def __init__(self) -> None:
        super().__init__(Objective(metric="sum", direction="minimize"))
        self.ask_count = 0
        self.tell_count = 0

    def ask(self) -> list[Treatment]:
        self.ask_count += 1
        return [Treatment("mock", {"delta": 0})]

    def tell(self, objective_values: dict[str, float]) -> None:
        self.tell_count += 1

    def get_best_treatment(self) -> Treatment:
        return Treatment("best", {"delta": 0})


def test_grid_search_optimizer_runs_and_returns_best() -> None:
    datasource = opt_example.initial_data()
    pipeline = Pipeline([opt_example.add_delta(), opt_example.record_metric()])
    experiment = Experiment(datasource=datasource, pipeline=pipeline)
    optimizer = opt_example.GridSearchOptimizer(
        param_grid={"delta": [0, 1, 2]},
        objective=Objective(metric="sum", direction="minimize"),
    )

    best = experiment.optimize(optimizer, num_trials=3, replicates_per_trial=1)

    assert optimizer.trial_index == 3
    assert optimizer.results == [6, 9, 12]
    ctx = opt_example.FrozenContext({"condition": "test"})
    best.apply(ctx)
    assert ctx.get("delta") == 0


def test_mock_optimizer_counts_calls() -> None:
    datasource = opt_example.initial_data()
    pipeline = Pipeline([opt_example.add_delta(), opt_example.record_metric()])
    experiment = Experiment(datasource=datasource, pipeline=pipeline)
    optimizer = MockOptimizer()

    experiment.optimize(optimizer, num_trials=5, replicates_per_trial=1)

    assert optimizer.ask_count == 5
    assert optimizer.tell_count == 5


