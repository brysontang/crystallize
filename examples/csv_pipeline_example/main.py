from pathlib import Path

from scipy.stats import ttest_ind

from crystallize import (
    hypothesis,
    pipeline,
    statistical_test,
    treatment,
)
from crystallize.core.context import FrozenContext
from crystallize.core.experiment import Experiment

from .datasource import csv_data_source, set_csv_path
from .steps.metric import explained_variance
from .steps.normalize import normalize
from .steps.pca import pca


@statistical_test
def welch_t_test(baseline, treatment, *, alpha: float = 0.05):
    t_stat, p_value = ttest_ind(baseline, treatment, equal_var=False)
    return {"p_value": p_value, "significant": p_value < alpha}


@treatment("better_data")
def better_data(ctx: FrozenContext) -> None:
    ctx["csv_path"] = str(Path(__file__).parent / "treatment.csv")


def main() -> None:
    base_dir = Path(__file__).parent
    datasource = csv_data_source(default_path=str(base_dir / "baseline.csv"))
    pipe = pipeline(normalize(), pca(), explained_variance())
    hyp = hypothesis(
        metric="explained_variance",
        statistical_test=welch_t_test(),
        direction="increase",
    )
    treat = better_data()

    experiment = (
        Experiment()
        .with_datasource(datasource)
        .with_pipeline(pipe)
        .with_treatments([treat])
        .with_hypotheses([hyp])
        .with_replicates(10)
    )
    experiment.validate()
    result = experiment.run()
    print(result.metrics["hypotheses"])
    print(result.provenance)


if __name__ == "__main__":
    main()
