import pytest
import numpy as np
from crystallize.core.context import FrozenContext
from crystallize.core.datasource import DataSource
from crystallize.core.pipeline_step import PipelineStep
from crystallize.core.pipeline import Pipeline
from crystallize.core.treatment import Treatment
from crystallize.core.experiment import Experiment

from crystallize.core.exceptions import MissingMetricError
from crystallize.core.hypothesis import Hypothesis
from crystallize.core import verifier


def make_verifier(accepted: bool):
    def verifier(baseline, treatment):
        return {"accepted": accepted}

    return verifier


def test_verify_returns_result():
    hyp = Hypothesis(verifier=make_verifier(True), metrics="metric", ranker=lambda r: 0.0)
    result = hyp.verify({"metric": [1, 2]}, {"metric": [3, 4]})
    assert result["accepted"] is True


def test_missing_metric_error():
    hyp = Hypothesis(verifier=make_verifier(True), metrics="metric", ranker=lambda r: 0.0)
    with pytest.raises(MissingMetricError):
        hyp.verify({"other": [1]}, {"metric": [2]})


def test_name_defaults_to_metric():
    hyp = Hypothesis(verifier=make_verifier(True), metrics="metric", ranker=lambda r: 0.0)
    assert hyp.name == "<lambda>"


def test_custom_name():
    hyp = Hypothesis(verifier=make_verifier(True), metrics="metric", ranker=lambda r: 0.0, name="custom")
    assert hyp.name == "custom"


def test_multi_metric():
    def verifier(baseline, treatment):
        return {
            "sum_baseline": sum(baseline["a"]) + sum(baseline["b"]),
            "sum_treatment": sum(treatment["a"]) + sum(treatment["b"]),
        }

    hyp = Hypothesis(verifier=verifier, metrics=["a", "b"], ranker=lambda r: 0.0)
    res = hyp.verify({"a": [1], "b": [2]}, {"a": [3], "b": [4]})
    assert res["sum_baseline"] == 3 and res["sum_treatment"] == 7


def test_grouped_metrics_return_list():
    def verifier(baseline, treatment):
        key = next(iter(baseline))
        return {"diff": sum(treatment[key]) - sum(baseline[key])}

    hyp = Hypothesis(verifier=verifier, metrics=[["x"], ["y"]], ranker=lambda r: r.get("diff", 0))
    out = hyp.verify({"x": [1], "y": [10]}, {"x": [2], "y": [20]})
    assert isinstance(out, list) and len(out) == 2


def test_rank_treatments_with_custom_ranker():
    hyp = Hypothesis(verifier=make_verifier(True), metrics="m", ranker=lambda r: r["score"])
    results = {"t1": {"score": 3}, "t2": {"score": 1}}
    ranking = hyp.rank_treatments(results)
    assert ranking["best"] == "t2"




def test_hypothesis_verifier_fuzz_no_crash():
    hyp_lib = pytest.importorskip("hypothesis")
    given = hyp_lib.given
    st = hyp_lib.strategies

    @given(
        st.dictionaries(st.text(min_size=1), st.lists(st.floats(allow_nan=False, allow_infinity=False), min_size=1)),
        st.dictionaries(st.text(min_size=1), st.lists(st.floats(allow_nan=False, allow_infinity=False), min_size=1)),
    )
    def run(baseline, treatment):
        # Ensure both dictionaries have at least one matching key
        if not baseline or not treatment:
            return
        
        common_key = next(iter(baseline))
        treatment[common_key] = treatment.get(common_key, baseline[common_key])

        def verifier(b, t):
            return {"mean": np.mean(list(t.values())[0]) - np.mean(list(b.values())[0])}

        hyp = Hypothesis(verifier=verifier, metrics=common_key)
        hyp.verify(baseline, treatment)

    run()


class RandomDataSource(DataSource):
    def fetch(self, ctx: FrozenContext):
        if ctx["condition"] == "baseline":
            return np.random.normal(0, 1, 10)
        return np.random.normal(1, 1, 10)


def test_full_experiment_with_scipy_verifier():
    pytest.importorskip("scipy")
    from scipy import stats

    @verifier
    def welch_t_test(baseline, treatment, alpha: float = 0.05):
        t_stat, p_value = stats.ttest_ind(
            treatment["data"], baseline["data"], equal_var=False
        )
        return {"p_value": p_value, "significant": p_value < alpha}

    hyp = Hypothesis(verifier=welch_t_test(), metrics="data", ranker=lambda r: r["p_value"])

    class CollectStep(PipelineStep):
        def __call__(self, data, ctx):
            ctx.metrics.add("data", data)
            return {"data": data}

        @property
        def params(self):
            return {}

    pipeline = Pipeline([CollectStep()])
    ds = RandomDataSource()
    treatment = Treatment("shift", {})
    exp = Experiment(datasource=ds, pipeline=pipeline)
    exp.validate()
    result = exp.run(treatments=[treatment], hypotheses=[hyp], replicates=3)
    hyp_res = result.get_hypothesis(hyp.name)
    assert hyp_res is not None and "p_value" in hyp_res.results["shift"]


@verifier
def param_verifier(baseline_samples, treatment_samples, threshold: int = 5):
    return {"above": sum(treatment_samples["a"]) > threshold}


def test_verifier_factory_params_and_missing():
    v1 = param_verifier()
    assert v1({"a": [1]}, {"a": [6]})["above"] is True
    v2 = param_verifier(threshold=10)
    assert v2({"a": [1]}, {"a": [6]})["above"] is False
    with pytest.raises(TypeError):
        param_verifier(missing=1)

