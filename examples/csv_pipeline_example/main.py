from pathlib import Path

from scipy.stats import ttest_ind

from crystallize import hypothesis, verifier, treatment
from crystallize.core.builder import ExperimentBuilder
from crystallize.core.context import FrozenContext

from .datasource import csv_data_source, set_csv_path
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

    treat = better_data

    experiment = (
        ExperimentBuilder()
        .datasource((csv_data_source, {"default_path": str(base_dir / "baseline.csv")}))
        .pipeline([normalize, pca, explained_variance])
        .treatments([treat])
        .hypotheses([hyp])
        .replicates(10)
        .build()
    )
    result = experiment.run()
    print(result.metrics["hypotheses"])
    print(result.provenance)


if __name__ == "__main__":
    main()
