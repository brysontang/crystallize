from pathlib import Path

from scipy.stats import ttest_ind

from crystallize import hypothesis, verifier, treatment
from crystallize.core.execution import ParallelExecution
from crystallize.core.experiment import Experiment
from crystallize.core.pipeline import Pipeline

from .datasource import csv_data_source
from .steps.metric import explained_variance
from .steps.normalize import normalize
from .steps.pca import pca


@verifier
def welch_t_test(baseline, treatment, *, alpha: float = 0.05):
    t_stat, p_value = ttest_ind(baseline['explained_variance'], treatment['explained_variance'], equal_var=False)
    return {"p_value": p_value, "significant": p_value < alpha}


better_data = treatment(
    "better_data",
    {"csv_path": str(Path(__file__).parent / "treatment.csv")},
)


def rank_by_p(result: dict) -> float:
    return result["p_value"]


@hypothesis(verifier=welch_t_test(), metrics="explained_variance")
def hyp(result):
    return result["p_value"]

def main() -> None:
    base_dir = Path(__file__).parent
    datasource = csv_data_source(default_path=str(base_dir / "baseline.csv"))
    pipeline_obj = Pipeline([normalize(), pca(), explained_variance()])
    experiment = Experiment(
        datasource=datasource,
        pipeline=pipeline_obj,
        treatments=[better_data()],
        hypotheses=[hyp],
        replicates=10,
        plugins=[ParallelExecution()],
    )
    experiment.validate()
    result = experiment.run()
    print(result.metrics["hypotheses"])
    print(result.provenance)


if __name__ == "__main__":
    main()
