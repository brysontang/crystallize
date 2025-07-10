from pathlib import Path

from scipy.stats import ttest_ind

from crystallize.core.experiment import Experiment
from crystallize.core.hypothesis import Hypothesis
from crystallize.core.pipeline import Pipeline
from crystallize.core.stat_test import StatisticalTest
from crystallize.core.treatment import Treatment

from .datasource import CSVDataSource
from .steps.metric import ExplainedVarianceStep
from .steps.normalize import NormalizeStep
from .steps.pca import PCAStep


class WelchTTest(StatisticalTest):
    def run(self, baseline, treatment, *, alpha=0.05):
        t_stat, p_value = ttest_ind(baseline, treatment, equal_var=False)
        return {"p_value": p_value, "significant": p_value < alpha}


def main() -> None:
    base_dir = Path(__file__).parent
    datasource = CSVDataSource(default_path=str(base_dir / "baseline.csv"))
    pipeline = Pipeline([NormalizeStep(), PCAStep(), ExplainedVarianceStep()])
    hypothesis = Hypothesis(
        metric="explained_variance",
        statistical_test=WelchTTest(),
        direction="increase",
    )
    treatment = Treatment(
        "better_data",
        lambda ctx: ctx.__setitem__("csv_path", str(base_dir / "treatment.csv")),
    )

    experiment = Experiment(
        datasource=datasource,
        pipeline=pipeline,
        treatments=[treatment],
        hypotheses=[hypothesis],
        replicates=10,
    )

    result = experiment.run()
    print(result.metrics["hypotheses"])
    print(result.provenance)


if __name__ == "__main__":
    main()
