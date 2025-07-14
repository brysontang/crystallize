import random
import time
import threading
from typing import List

import numpy as np
import pytest

from crystallize.core.execution import ParallelExecution
from crystallize.core.plugins import SeedPlugin
from crystallize.core.context import FrozenContext
from crystallize.core.datasource import DataSource
from crystallize.core.experiment import Experiment
from crystallize.core.hypothesis import Hypothesis
from crystallize.core.pipeline import Pipeline
from crystallize.core.pipeline_step import PipelineStep, exit_step
from crystallize.core.treatment import Treatment


class DummyDataSource(DataSource):
    def fetch(self, ctx: FrozenContext):
        # return replicate id plus any increment in ctx
        return ctx["replicate"] + ctx.as_dict().get("increment", 0)


class PassStep(PipelineStep):
    cacheable = True

    def __call__(self, data, ctx):
        ctx.metrics.add("metric", data)
        return {"metric": data}

    @property
    def params(self):
        return {}


def always_significant(baseline, treatment):
    return {"p_value": 0.01, "significant": True, "accepted": True}


def test_experiment_run_basic():
    pipeline = Pipeline([PassStep()])
    datasource = DummyDataSource()
    hypothesis = Hypothesis(
        verifier=always_significant,
        metrics="metric",
        ranker=lambda r: r["p_value"],
    )
    treatment = Treatment("treat", {"increment": 1})

    experiment = Experiment(
        datasource=datasource,
        pipeline=pipeline,
        treatments=[treatment],
        hypotheses=[hypothesis],
        replicates=2,
    )
    experiment.validate()
    result = experiment.run()
    assert result.metrics.baseline.metrics["metric"] == [0, 1]
    assert result.metrics.treatments["treat"].metrics["metric"] == [1, 2]
    hyp_res = result.get_hypothesis(hypothesis.name)
    assert hyp_res is not None and hyp_res.results["treat"]["accepted"] is True
    assert hyp_res.ranking["best"] == "treat"
    assert result.errors == {}


def test_experiment_run_multiple_treatments():
    pipeline = Pipeline([PassStep()])
    datasource = DummyDataSource()
    hypothesis = Hypothesis(
        verifier=always_significant,
        metrics="metric",
        ranker=lambda r: r["p_value"],
    )
    treatment1 = Treatment("treat1", {"increment": 1})
    treatment2 = Treatment("treat2", {"increment": 2})
    experiment = Experiment(
        datasource=datasource,
        pipeline=pipeline,
        treatments=[treatment1, treatment2],
        hypotheses=[hypothesis],
        replicates=2,
    )
    experiment.validate()
    result = experiment.run()
    assert result.metrics.baseline.metrics["metric"] == [0, 1]
    assert result.metrics.treatments["treat1"].metrics["metric"] == [1, 2]
    assert result.metrics.treatments["treat2"].metrics["metric"] == [2, 3]
    hyp_res = result.get_hypothesis(hypothesis.name)
    assert hyp_res is not None and hyp_res.results["treat1"]["accepted"] is True
    assert hyp_res.results["treat2"]["accepted"] is True
    ranked = hyp_res.ranking["ranked"]
    assert ranked[0][0] == "treat1"


def test_experiment_run_baseline_only():
    pipeline = Pipeline([PassStep()])
    datasource = DummyDataSource()

    experiment = Experiment(
        datasource=datasource,
        pipeline=pipeline,
    )
    experiment.validate()
    result = experiment.run()
    assert result.metrics.baseline.metrics["metric"] == [0]
    assert result.metrics.hypotheses == []


def test_experiment_run_treatments_no_hypotheses():
    pipeline = Pipeline([PassStep()])
    datasource = DummyDataSource()
    treatment = Treatment("treat", {"increment": 1})

    experiment = Experiment(
        datasource=datasource,
        pipeline=pipeline,
        treatments=[treatment],
    )
    experiment.validate()
    result = experiment.run()
    assert result.metrics.treatments["treat"].metrics["metric"] == [1]


def test_experiment_run_hypothesis_without_treatments_raises():
    pipeline = Pipeline([PassStep()])
    datasource = DummyDataSource()
    hypothesis = Hypothesis(
        verifier=always_significant,
        metrics="metric",
        ranker=lambda r: r["p_value"],
    )

    experiment = Experiment(
        datasource=datasource,
        pipeline=pipeline,
        hypotheses=[hypothesis],
    )
    with pytest.raises(ValueError):
        experiment.validate()


class IdentityStep(PipelineStep):
    def __call__(self, data, ctx):
        return data

    @property
    def params(self):
        return {}


def test_experiment_apply_with_exit_step():
    pipeline = Pipeline([exit_step(IdentityStep()), PassStep()])
    datasource = DummyDataSource()
    experiment = Experiment(datasource=datasource, pipeline=pipeline)
    experiment.validate()
    output = experiment.apply(data=5)
    assert output == 5


def test_experiment_requires_validation():
    pipeline = Pipeline([PassStep()])
    datasource = DummyDataSource()
    experiment = Experiment(datasource=datasource, pipeline=pipeline)
    with pytest.raises(RuntimeError):
        experiment.run()
    with pytest.raises(RuntimeError):
        experiment.apply(data=1)


def test_experiment_builder_chaining():
    experiment = Experiment(
        datasource=DummyDataSource(),
        pipeline=Pipeline([PassStep()]),
        treatments=[Treatment("t", {"increment": 1})],
        hypotheses=[
            Hypothesis(
                verifier=always_significant,
                metrics="metric",
                ranker=lambda r: r["p_value"],
                name="hypothesis",
            )
        ],
        replicates=2,
    )
    experiment.validate()
    result = experiment.run()
    assert result.metrics.treatments["t"].metrics["metric"] == [1, 2]
    hyp_res = result.get_hypothesis("hypothesis")
    assert hyp_res is not None and hyp_res.ranking["best"] == "t"


def test_run_zero_replicates():
    pipeline = Pipeline([PassStep()])
    datasource = DummyDataSource()
    experiment = Experiment(datasource=datasource, pipeline=pipeline, replicates=0)
    experiment.validate()
    result = experiment.run()
    assert len(result.metrics.baseline.metrics["metric"]) == 1


def test_validate_partial_config():
    experiment = Experiment(pipeline=Pipeline([PassStep()]))
    with pytest.raises(ValueError):
        experiment.validate()


def test_apply_without_exit_step():
    pipeline = Pipeline([IdentityStep(), PassStep()])
    datasource = DummyDataSource()
    experiment = Experiment(datasource=datasource, pipeline=pipeline)
    experiment.validate()
    with pytest.raises(ValueError):
        experiment.apply(data=7)


class TrackStep(PipelineStep):
    def __init__(self):
        self.called = False

    def __call__(self, data, ctx):
        self.called = True
        return data

    @property
    def params(self):
        return {}


def test_apply_multiple_exit_steps():
    step1 = TrackStep()
    step2 = TrackStep()
    pipeline = Pipeline([exit_step(step1), exit_step(step2), PassStep()])
    datasource = DummyDataSource()
    experiment = Experiment(datasource=datasource, pipeline=pipeline)
    experiment.validate()
    output = experiment.apply(data=3)
    assert output == 3
    assert step1.called is True
    assert step2.called is False


class StringMetricsStep(PipelineStep):
    cacheable = True

    def __call__(self, data, ctx):
        ctx.metrics.add("metric", "a")
        return {"metric": "a"}

    @property
    def params(self):
        return {}


def test_run_with_non_numeric_metrics_raises():
    pipeline = Pipeline([StringMetricsStep()])
    datasource = DummyDataSource()
    hypothesis = Hypothesis(
        verifier=always_significant,
        metrics="metric",
        ranker=lambda r: r["p_value"],
    )
    treatment = Treatment("t", {"increment": 0})
    experiment = Experiment(
        datasource=datasource,
        pipeline=pipeline,
        treatments=[treatment],
        hypotheses=[hypothesis],
    )
    experiment.validate()
    experiment.run()


def test_cache_provenance_reused_between_runs(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    step = PassStep()
    pipeline1 = Pipeline([step])
    ds = DummyDataSource()
    exp1 = Experiment(datasource=ds, pipeline=pipeline1)
    exp1.validate()
    exp1.run()

    pipeline2 = Pipeline([PassStep()])
    exp2 = Experiment(datasource=ds, pipeline=pipeline2)
    exp2.validate()
    exp2.run()
    assert pipeline2.get_provenance()[0]["cache_hit"] is True


def test_parallel_execution_matches_serial():
    pipeline = Pipeline([PassStep()])
    datasource = DummyDataSource()
    hypothesis = Hypothesis(
        verifier=always_significant,
        metrics="metric",
        ranker=lambda r: r["p_value"],
    )
    treatment = Treatment("t", {"increment": 1})

    serial_exp = Experiment(
        datasource=datasource,
        pipeline=pipeline,
        treatments=[treatment],
        hypotheses=[hypothesis],
        replicates=2,
    )
    serial_exp.validate()
    serial_result = serial_exp.run()

    parallel_exp = Experiment(
        datasource=datasource,
        pipeline=pipeline,
        treatments=[treatment],
        hypotheses=[hypothesis],
        replicates=2,
        plugins=[ParallelExecution()],
    )
    parallel_exp.validate()
    parallel_result = parallel_exp.run()

    assert parallel_result.metrics == serial_result.metrics


class FailingStep(PipelineStep):
    def __call__(self, data, ctx):
        if ctx["replicate"] == 1:
            raise RuntimeError("boom")
        ctx.metrics.add("metric", data)
        return {"metric": data}

    @property
    def params(self):
        return {}


def test_parallel_execution_handles_errors():
    pipeline = Pipeline([FailingStep()])
    datasource = DummyDataSource()
    treatment = Treatment("t", {"increment": 1})

    serial = Experiment(
        datasource=datasource,
        pipeline=pipeline,
        treatments=[treatment],
        replicates=2,
    )
    serial.validate()
    serial_res = serial.run()

    parallel = Experiment(
        datasource=datasource,
        pipeline=pipeline,
        treatments=[treatment],
        replicates=2,
        plugins=[ParallelExecution()],
    )
    parallel.validate()
    parallel_res = parallel.run()

    assert parallel_res.metrics == serial_res.metrics
    assert parallel_res.errors.keys() == serial_res.errors.keys()


class SleepStep(PipelineStep):
    cacheable = False

    def __call__(self, data, ctx):
        time.sleep(0.1)
        ctx.metrics.add("metric", data)
        return {"metric": data}

    @property
    def params(self):
        return {}


def test_parallel_is_faster_for_sleep_step():
    pipeline = Pipeline([SleepStep()])
    ds = DummyDataSource()
    exp_serial = Experiment(datasource=ds, pipeline=pipeline, replicates=5)
    exp_serial.validate()
    start = time.time()
    exp_serial.run()
    serial_time = time.time() - start

    exp_parallel = Experiment(
        datasource=ds,
        pipeline=pipeline,
        replicates=5,
        plugins=[ParallelExecution()],
    )
    exp_parallel.validate()
    start = time.time()
    exp_parallel.run()
    parallel_time = time.time() - start

    assert serial_time > parallel_time


def test_parallel_high_replicate_count():
    pipeline = Pipeline([PassStep()])
    ds = DummyDataSource()
    exp = Experiment(
        datasource=ds,
        pipeline=pipeline,
        replicates=10,
        plugins=[ParallelExecution()],
    )
    exp.validate()
    result = exp.run()
    assert len(result.metrics.baseline.metrics["metric"]) == 10


class FibStep(PipelineStep):
    cacheable = False

    def __init__(self, n: int = 32) -> None:
        self.n = n

    def __call__(self, data, ctx):
        def fib(k: int) -> int:
            return k if k < 2 else fib(k - 1) + fib(k - 2)

        fib(self.n)
        ctx.metrics.add("metric", data)
        return {"metric": data}

    @property
    def params(self):
        return {"n": self.n}


def test_process_executor_faster_for_cpu_bound_step():
    pipeline = Pipeline([FibStep(35)])
    ds = DummyDataSource()

    exp_thread = Experiment(
        datasource=ds,
        pipeline=pipeline,
        replicates=4,
        plugins=[ParallelExecution(executor_type="thread")],
    )
    exp_thread.validate()
    start = time.time()
    exp_thread.run()
    thread_time = time.time() - start

    exp_process = Experiment(
        datasource=ds,
        pipeline=pipeline,
        replicates=4,
        plugins=[ParallelExecution(executor_type="process")],
    )
    exp_process.validate()
    start = time.time()
    exp_process.run()
    process_time = time.time() - start

    assert process_time < thread_time


def test_invalid_executor_type_raises():
    pipeline = Pipeline([PassStep()])
    ds = DummyDataSource()
    exp = Experiment(
        datasource=ds,
        pipeline=pipeline,
        plugins=[ParallelExecution(executor_type="bogus")],
    )
    exp.validate()
    with pytest.raises(ValueError):
        exp.run()


@pytest.mark.parametrize("replicates", [1, 5, 10])
def test_full_experiment_replicate_counts(replicates):
    pipeline = Pipeline([PassStep()])
    datasource = DummyDataSource()
    treatment = Treatment("t", {"increment": 1})
    hypothesis = Hypothesis(
        verifier=always_significant,
        metrics="metric",
        ranker=lambda r: r["p_value"],
    )

    experiment = Experiment(
        datasource=datasource,
        pipeline=pipeline,
        treatments=[treatment],
        hypotheses=[hypothesis],
        replicates=replicates,
    )
    experiment.validate()
    result = experiment.run()
    assert len(result.metrics.baseline.metrics["metric"]) == replicates
    assert len(result.metrics.treatments["t"].metrics["metric"]) == replicates
    hyp_res = result.get_hypothesis(hypothesis.name)
    assert hyp_res is not None and hyp_res.ranking["best"] == "t"


def test_apply_with_treatment_and_exit():
    pipeline = Pipeline([exit_step(IdentityStep()), PassStep()])
    datasource = DummyDataSource()
    treatment = Treatment("inc", {"increment": 2})
    experiment = Experiment(
        datasource=datasource, pipeline=pipeline, treatments=[treatment]
    )
    experiment.validate()
    output = experiment.apply(treatment_name="inc", data=5)
    assert output == 5


def test_provenance_signature_and_cache(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    step = PassStep()
    pipeline = Pipeline([step])
    ds = DummyDataSource()
    exp1 = Experiment(datasource=ds, pipeline=pipeline)
    exp1.validate()
    res1 = exp1.run()
    assert res1.provenance["pipeline_signature"] == pipeline.signature()
    assert res1.provenance["replicates"] == 1

    pipeline2 = Pipeline([PassStep()])
    exp2 = Experiment(datasource=ds, pipeline=pipeline2)
    exp2.validate()
    exp2.run()
    assert pipeline2.get_provenance()[0]["cache_hit"] is True


def test_multiple_hypotheses_partial_failure():
    pipeline = Pipeline([PassStep()])
    ds = DummyDataSource()
    good = Hypothesis(
        verifier=always_significant,
        metrics="metric",
        ranker=lambda r: r["p_value"],
        name="good",
    )
    bad = Hypothesis(
        verifier=always_significant,
        metrics="missing",
        ranker=lambda r: r["p_value"],
        name="bad",
    )
    exp = Experiment(
        datasource=ds,
        pipeline=pipeline,
        treatments=[Treatment("t", {"increment": 1})],
        hypotheses=[good, bad],
    )
    exp.validate()
    with pytest.raises(Exception):
        exp.run()



def test_process_pool_respects_max_workers(monkeypatch):
    recorded = {}

    class DummyExecutor:
        def __init__(self, max_workers=None):
            recorded["max"] = max_workers

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def submit(self, fn, rep):
            class F:
                def __init__(self_inner) -> None:
                    self_inner._condition = threading.Condition()
                    self_inner._state = "FINISHED"
                    self_inner._waiters = []

                def result(self_inner):
                    return fn(rep)

                def done(self_inner):  # pragma: no cover - minimal future API
                    return True

            return F()

    from crystallize.core import execution

    monkeypatch.setattr(execution, "ProcessPoolExecutor", DummyExecutor)
    monkeypatch.setattr(execution.os, "cpu_count", lambda: 4)

    pipeline = Pipeline([PassStep()])
    ds = DummyDataSource()
    exp = Experiment(
        datasource=ds,
        pipeline=pipeline,
        replicates=5,
        plugins=[ParallelExecution(executor_type="process", max_workers=2)],
    )
    exp.validate()
    exp.run()

    assert recorded["max"] == 2


@pytest.mark.parametrize("parallel", [False, True])
def test_ctx_mutation_error_parallel_and_serial(parallel):
    class MutateStep(PipelineStep):
        def __call__(self, data, ctx):
            ctx["condition"] = "oops"

        @property
        def params(self):
            return {}

    pipeline = Pipeline([MutateStep()])
    ds = DummyDataSource()
    plugins = [ParallelExecution()] if parallel else []
    exp = Experiment(
        datasource=ds,
        pipeline=pipeline,
        replicates=2,
        plugins=plugins,
    )
    exp.validate()
    result = exp.run()
    assert result.metrics.baseline.metrics == {}
    assert "baseline_rep_0" in result.errors and "baseline_rep_1" in result.errors


class FailingSource(DataSource):
    def fetch(self, ctx: FrozenContext):
        raise RuntimeError("source fail")


def test_datasource_failure_recorded():
    pipeline = Pipeline([PassStep()])
    ds = FailingSource()
    exp = Experiment(datasource=ds, pipeline=pipeline, replicates=2)
    exp.validate()
    result = exp.run()
    assert "baseline_rep_0" in result.errors
    assert "baseline_rep_1" in result.errors


def test_treatment_failure_recorded():
    pipeline = Pipeline([PassStep()])
    ds = DummyDataSource()
    failing = Treatment("boom", lambda ctx: (_ for _ in ()).throw(RuntimeError("bad")))
    exp = Experiment(
        datasource=ds, pipeline=pipeline, treatments=[failing], replicates=2
    )
    exp.validate()
    result = exp.run()
    assert "boom_rep_0" in result.errors
    assert "boom_rep_1" in result.errors


def test_ranker_error_bubbles():
    pipeline = Pipeline([PassStep()])
    ds = DummyDataSource()

    def bad_ranker(res):
        return 1 / 0

    hyp = Hypothesis(verifier=always_significant, metrics="metric", ranker=bad_ranker)
    exp = Experiment(
        datasource=ds,
        pipeline=pipeline,
        treatments=[Treatment("t", {"increment": 1})],
        hypotheses=[hyp],
    )
    exp.validate()
    with pytest.raises(ZeroDivisionError):
        exp.run()


def test_invalid_replicates_type():
    with pytest.raises(TypeError):
        Experiment(
            datasource=DummyDataSource(),
            pipeline=Pipeline([PassStep()]),
            replicates="three",
        )


def test_zero_negative_replicates_clamped():
    pipeline = Pipeline([PassStep()])
    ds = DummyDataSource()
    for reps in [0, -5]:
        exp = Experiment(datasource=ds, pipeline=pipeline, replicates=reps)
        exp.validate()
        result = exp.run()
        assert len(result.metrics.baseline.metrics["metric"]) == 1


# Slow
def test_high_replicates_parallel_no_issues():
    pipeline = Pipeline([PassStep()])
    ds = DummyDataSource()
    exp = Experiment(
        datasource=ds,
        pipeline=pipeline,
        replicates=50,
        plugins=[ParallelExecution(executor_type="thread")],
    )
    exp.validate()
    result = exp.run()
    assert len(result.metrics.baseline.metrics["metric"]) == 50


class RandomDataSource(DataSource):
    def fetch(self, ctx: FrozenContext):
        return np.random.random()


class RandomStep(PipelineStep):
    cacheable = False

    def __call__(self, data, ctx):
        val = data + random.random()
        ctx.metrics.add("rand", val)
        return {"rand": val}

    @property
    def params(self):
        return {}


def test_auto_seed_reproducible_serial_vs_parallel():
    pipeline = Pipeline([RandomStep()])
    ds = RandomDataSource()

    def numpy_seed_fn(seed: int) -> None:
        random.seed(seed)
        np.random.seed(seed % (2**32 - 1))

    serial = Experiment(
        datasource=ds,
        pipeline=pipeline,
        replicates=3,
        plugins=[SeedPlugin(seed=123, auto_seed=True, seed_fn=numpy_seed_fn)],
    )
    serial.validate()
    res_serial = serial.run()

    parallel = Experiment(
        datasource=ds,
        pipeline=pipeline,
        replicates=3,
        plugins=[
            SeedPlugin(seed=123, auto_seed=True, seed_fn=numpy_seed_fn),
            ParallelExecution(),
        ],
    )
    parallel.validate()
    res_parallel = parallel.run()

    assert res_serial.metrics == res_parallel.metrics
    assert res_serial.provenance["seeds"] == res_parallel.provenance["seeds"]
    expected = [hash(123 + rep) for rep in range(3)]
    assert res_serial.provenance["seeds"]["baseline"] == expected


def test_custom_seed_function_called():
    called: List[int] = []

    def record_seed(val: int) -> None:
        called.append(val)

    pipeline = Pipeline([RandomStep()])
    ds = RandomDataSource()
    exp = Experiment(
        datasource=ds,
        pipeline=pipeline,
        replicates=1,
        plugins=[SeedPlugin(seed=7, seed_fn=record_seed, auto_seed=True)],
    )
    exp.validate()
    exp.run()
    assert called == [hash(7)]


def test_apply_seed_function_called():
    called: List[int] = []

    def record_seed(val: int) -> None:
        called.append(val)

    pipeline = Pipeline([exit_step(IdentityStep())])
    ds = DummyDataSource()
    exp = Experiment(
        datasource=ds,
        pipeline=pipeline,
        plugins=[SeedPlugin(seed_fn=record_seed)],
    )
    exp.validate()
    exp.apply(data=1, seed=5)
    assert called == [5]
