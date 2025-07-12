from crystallize.core.result import Result
from crystallize.core.result_structs import ExperimentMetrics, TreatmentMetrics


def test_result_accessors_and_errors():
    metrics = ExperimentMetrics(
        baseline=TreatmentMetrics({"a": [1]}),
        treatments={},
        hypotheses=[],
    )
    artifacts = {"model": object()}
    errors = {"run": RuntimeError("fail")}
    r = Result(metrics=metrics, artifacts=artifacts, errors=errors)
    assert r.metrics.baseline.metrics["a"] == [1]
    assert r.get_artifact("model") is artifacts["model"]
    assert r.errors == errors

