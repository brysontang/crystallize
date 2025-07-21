import builtins
from crystallize.experiments.result import Result
from crystallize.experiments.result_structs import ExperimentMetrics, TreatmentMetrics


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


def test_print_tree_plain_output(capsys):
    metrics = ExperimentMetrics(
        baseline=TreatmentMetrics({}),
        treatments={},
        hypotheses=[],
    )
    provenance = {
        "ctx_changes": {
            "baseline": {
                0: [
                    {
                        "step": "AddStep",
                        "ctx_changes": {
                            "reads": {"x": 1},
                            "wrote": {},
                            "metrics": {},
                        },
                    }
                ]
            }
        }
    }
    r = Result(metrics=metrics, provenance=provenance)
    r.print_tree()
    output = capsys.readouterr().out
    assert "AddStep" in output
    assert "x=1" in output


def test_print_tree_without_rich(monkeypatch, capsys):
    metrics = ExperimentMetrics(
        baseline=TreatmentMetrics({}),
        treatments={},
        hypotheses=[],
    )
    prov = {
        "ctx_changes": {
            "baseline": {0: [{"step": "AddStep", "ctx_changes": {"reads": {"x": 1}, "wrote": {}, "metrics": {}}}]}
        }
    }
    r = Result(metrics=metrics, provenance=prov)

    original_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name.startswith("rich"):
            raise ImportError
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    r.print_tree()
    output = capsys.readouterr().out
    assert "Experiment Summary" in output
    assert "AddStep" in output
