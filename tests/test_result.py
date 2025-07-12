from crystallize.core.result import Result


def test_result_accessors_and_errors():
    metrics = {"a": 1}
    artifacts = {"model": object()}
    errors = {"run": RuntimeError("fail")}
    r = Result(metrics=metrics, artifacts=artifacts, errors=errors)
    assert r.get_metrics("a") == 1
    assert r.get_artifact("model") is artifacts["model"]
    assert r.errors == errors

