from pathlib import Path

from datasource import CSVDataSource
from steps.metric import ExplainedVarianceStep
from steps.normalize import NormalizeStep
from steps.pca import PCAStep

from crystallize.core.experiment import Experiment
from crystallize.core.hypothesis import Hypothesis
from crystallize.core.pipeline import Pipeline
from crystallize.core.stat_test import StatisticalTest
from crystallize.core.treatment import Treatment


class AlwaysSignificant(StatisticalTest):
    def run(self, baseline, treatment, *, alpha: float = 0.05):
        return {"p_value": 0.01, "significant": True}


def main() -> None:
    base_dir = Path(__file__).parent
    datasource = CSVDataSource(default_path=str(base_dir / "baseline.csv"))
    pipeline = Pipeline([NormalizeStep(), PCAStep(), ExplainedVarianceStep()])
    hypothesis = Hypothesis(
        metric="explained_variance",
        direction="increase",
        statistical_test=AlwaysSignificant(),
    )
    treatment = Treatment(
        "better_data",
        lambda ctx: ctx.__setitem__("csv_path", str(base_dir / "treatment.csv")),
    )

    experiment = Experiment(
        datasource=datasource,
        pipeline=pipeline,
        treatments=[treatment],
        hypothesis=hypothesis,
        replicates=1,
    )

    result = experiment.run()
    print(result.metrics)
    print(result.provenance)


if __name__ == "__main__":
    main()
