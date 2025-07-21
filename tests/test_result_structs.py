import pytest

from crystallize.experiments.result_structs import ExperimentMetrics, TreatmentMetrics, HypothesisResult


def make_metrics() -> ExperimentMetrics:
    return ExperimentMetrics(
        baseline=TreatmentMetrics({"m": [1]}),
        treatments={"t": TreatmentMetrics({"m": [2]})},
        hypotheses=[
            HypothesisResult(
                name="h",
                results={"t": {"score": 3}},
                ranking={"best": "t"},
            )
        ],
    )


def test_metrics_to_dataframe():
    metrics = make_metrics()
    df = metrics.to_df()
    assert set(df.columns) == {"condition", "hypothesis", "score"}
    assert df.iloc[0]["condition"] == "t"
    assert df.iloc[0]["hypothesis"] == "h"
    assert df.iloc[0]["score"] == 3


def test_metrics_to_df_no_pandas(monkeypatch):
    import crystallize.experiments.result_structs as rs

    metrics = make_metrics()
    monkeypatch.setattr(rs, "pd", None)
    with pytest.raises(ImportError):
        metrics.to_df()
