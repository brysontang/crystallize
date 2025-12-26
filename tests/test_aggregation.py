"""Tests for crystallize.experiments.aggregation module."""

from collections import defaultdict

from crystallize.experiments.aggregation import ResultAggregator
from crystallize.experiments.run_results import ReplicateResult
from crystallize.experiments.result_structs import (
    AggregateData,
    ExperimentMetrics,
    TreatmentMetrics,
)
from crystallize.pipelines.pipeline import Pipeline
from crystallize.pipelines.pipeline_step import PipelineStep


class DummyStep(PipelineStep):
    """Simple step for testing."""

    def __call__(self, data, ctx):
        return data

    @property
    def params(self):
        return {}


def make_replicate_result(
    baseline_metrics=None,
    baseline_seed=None,
    treatment_metrics=None,
    treatment_seeds=None,
    errors=None,
    provenance=None,
):
    """Helper to create ReplicateResult with defaults."""
    return ReplicateResult(
        baseline_metrics=baseline_metrics,
        baseline_seed=baseline_seed,
        treatment_metrics=treatment_metrics or {},
        treatment_seeds=treatment_seeds or {},
        errors=errors or {},
        provenance=provenance or {},
    )


class TestResultAggregatorAggregateResults:
    """Tests for ResultAggregator.aggregate_results()."""

    def test_empty_results_list(self):
        pipeline = Pipeline([DummyStep()])
        agg = ResultAggregator(pipeline, replicates=0)
        result = agg.aggregate_results([])

        assert result.baseline_metrics == {}
        assert result.treatment_metrics_dict == {}
        assert result.baseline_seeds == []
        assert result.treatment_seeds_agg == {}
        assert result.errors == {}

    def test_single_replicate_baseline_only(self):
        pipeline = Pipeline([DummyStep()])
        agg = ResultAggregator(pipeline, replicates=1)

        rep = make_replicate_result(
            baseline_metrics={"accuracy": [0.95]},
            baseline_seed=42,
        )
        result = agg.aggregate_results([rep])

        assert result.baseline_metrics == {"accuracy": [0.95]}
        assert result.baseline_seeds == [42]
        assert result.treatment_metrics_dict == {}

    def test_multiple_replicates_baseline(self):
        pipeline = Pipeline([DummyStep()])
        agg = ResultAggregator(pipeline, replicates=3)

        reps = [
            make_replicate_result(
                baseline_metrics={"accuracy": [0.90]},
                baseline_seed=100,
            ),
            make_replicate_result(
                baseline_metrics={"accuracy": [0.92]},
                baseline_seed=101,
            ),
            make_replicate_result(
                baseline_metrics={"accuracy": [0.94]},
                baseline_seed=102,
            ),
        ]
        result = agg.aggregate_results(reps)

        assert result.baseline_metrics == {"accuracy": [0.90, 0.92, 0.94]}
        assert result.baseline_seeds == [100, 101, 102]

    def test_single_treatment(self):
        pipeline = Pipeline([DummyStep()])
        agg = ResultAggregator(pipeline, replicates=2)

        reps = [
            make_replicate_result(
                baseline_metrics={"metric": [1]},
                baseline_seed=10,
                treatment_metrics={"treatment_a": {"metric": [2]}},
                treatment_seeds={"treatment_a": 20},
            ),
            make_replicate_result(
                baseline_metrics={"metric": [1]},
                baseline_seed=11,
                treatment_metrics={"treatment_a": {"metric": [3]}},
                treatment_seeds={"treatment_a": 21},
            ),
        ]
        result = agg.aggregate_results(reps)

        assert result.baseline_metrics == {"metric": [1, 1]}
        assert result.treatment_metrics_dict == {"treatment_a": {"metric": [2, 3]}}
        assert result.treatment_seeds_agg == {"treatment_a": [20, 21]}

    def test_multiple_treatments(self):
        pipeline = Pipeline([DummyStep()])
        agg = ResultAggregator(pipeline, replicates=2)

        reps = [
            make_replicate_result(
                baseline_metrics={"m": [0]},
                treatment_metrics={
                    "treat_a": {"m": [1]},
                    "treat_b": {"m": [2]},
                },
                treatment_seeds={"treat_a": 100, "treat_b": 200},
            ),
            make_replicate_result(
                baseline_metrics={"m": [0]},
                treatment_metrics={
                    "treat_a": {"m": [1]},
                    "treat_b": {"m": [2]},
                },
                treatment_seeds={"treat_a": 101, "treat_b": 201},
            ),
        ]
        result = agg.aggregate_results(reps)

        assert result.treatment_metrics_dict["treat_a"] == {"m": [1, 1]}
        assert result.treatment_metrics_dict["treat_b"] == {"m": [2, 2]}
        assert result.treatment_seeds_agg["treat_a"] == [100, 101]
        assert result.treatment_seeds_agg["treat_b"] == [200, 201]

    def test_multiple_metrics_per_replicate(self):
        pipeline = Pipeline([DummyStep()])
        agg = ResultAggregator(pipeline, replicates=2)

        reps = [
            make_replicate_result(
                baseline_metrics={"acc": [0.9], "loss": [0.1]},
            ),
            make_replicate_result(
                baseline_metrics={"acc": [0.92], "loss": [0.08]},
            ),
        ]
        result = agg.aggregate_results(reps)

        assert result.baseline_metrics == {"acc": [0.9, 0.92], "loss": [0.1, 0.08]}

    def test_errors_aggregation(self):
        pipeline = Pipeline([DummyStep()])
        agg = ResultAggregator(pipeline, replicates=2)

        err1 = RuntimeError("failed rep 0")
        err2 = ValueError("failed rep 1")
        reps = [
            make_replicate_result(errors={"baseline_rep_0": err1}),
            make_replicate_result(errors={"baseline_rep_1": err2}),
        ]
        result = agg.aggregate_results(reps)

        assert result.errors["baseline_rep_0"] is err1
        assert result.errors["baseline_rep_1"] is err2

    def test_provenance_aggregation(self):
        pipeline = Pipeline([DummyStep()])
        agg = ResultAggregator(pipeline, replicates=2)

        reps = [
            make_replicate_result(
                provenance={"baseline": [{"step": "DummyStep", "cache_hit": False}]},
            ),
            make_replicate_result(
                provenance={"baseline": [{"step": "DummyStep", "cache_hit": True}]},
            ),
        ]
        result = agg.aggregate_results(reps)

        assert 0 in result.provenance_runs["baseline"]
        assert 1 in result.provenance_runs["baseline"]
        assert result.provenance_runs["baseline"][0] == [
            {"step": "DummyStep", "cache_hit": False}
        ]
        assert result.provenance_runs["baseline"][1] == [
            {"step": "DummyStep", "cache_hit": True}
        ]

    def test_none_baseline_metrics_skipped(self):
        pipeline = Pipeline([DummyStep()])
        agg = ResultAggregator(pipeline, replicates=2)

        reps = [
            make_replicate_result(baseline_metrics={"m": [1]}, baseline_seed=10),
            make_replicate_result(baseline_metrics=None, baseline_seed=None),
        ]
        result = agg.aggregate_results(reps)

        assert result.baseline_metrics == {"m": [1]}
        assert result.baseline_seeds == [10]

    def test_partial_treatment_results(self):
        """Test when some replicates have treatments and others don't."""
        pipeline = Pipeline([DummyStep()])
        agg = ResultAggregator(pipeline, replicates=2)

        reps = [
            make_replicate_result(
                treatment_metrics={"treat": {"m": [1]}},
                treatment_seeds={"treat": 100},
            ),
            make_replicate_result(
                treatment_metrics={},
                treatment_seeds={},
            ),
        ]
        result = agg.aggregate_results(reps)

        assert result.treatment_metrics_dict == {"treat": {"m": [1]}}
        assert result.treatment_seeds_agg == {"treat": [100]}


class TestResultAggregatorBuildResult:
    """Tests for ResultAggregator.build_result()."""

    def test_build_result_basic(self):
        pipeline = Pipeline([DummyStep()])
        agg = ResultAggregator(pipeline, replicates=2)

        metrics = ExperimentMetrics(
            baseline=TreatmentMetrics({"m": [1, 2]}),
            treatments={},
            hypotheses=[],
        )
        aggregate = AggregateData(
            baseline_metrics={"m": [1, 2]},
            treatment_metrics_dict={},
            baseline_seeds=[10, 11],
            treatment_seeds_agg={},
            provenance_runs=defaultdict(dict),
            errors={},
        )

        result = agg.build_result(metrics, aggregate)

        assert result.metrics is metrics
        assert result.errors == {}
        assert result.provenance["replicates"] == 2
        assert result.provenance["seeds"]["baseline"] == [10, 11]
        assert result.provenance["pipeline_signature"] == pipeline.signature()

    def test_build_result_with_treatments(self):
        pipeline = Pipeline([DummyStep()])
        agg = ResultAggregator(pipeline, replicates=2)

        metrics = ExperimentMetrics(
            baseline=TreatmentMetrics({"m": [0, 0]}),
            treatments={"treat_a": TreatmentMetrics({"m": [1, 1]})},
            hypotheses=[],
        )
        aggregate = AggregateData(
            baseline_metrics={"m": [0, 0]},
            treatment_metrics_dict={"treat_a": {"m": [1, 1]}},
            baseline_seeds=[10, 11],
            treatment_seeds_agg={"treat_a": [20, 21]},
            provenance_runs=defaultdict(dict),
            errors={},
        )

        result = agg.build_result(metrics, aggregate)

        assert result.provenance["seeds"]["baseline"] == [10, 11]
        assert result.provenance["seeds"]["treat_a"] == [20, 21]

    def test_build_result_with_errors(self):
        pipeline = Pipeline([DummyStep()])
        agg = ResultAggregator(pipeline, replicates=1)

        metrics = ExperimentMetrics(
            baseline=TreatmentMetrics({}),
            treatments={},
            hypotheses=[],
        )
        err = RuntimeError("test error")
        aggregate = AggregateData(
            baseline_metrics={},
            treatment_metrics_dict={},
            baseline_seeds=[],
            treatment_seeds_agg={},
            provenance_runs=defaultdict(dict),
            errors={"baseline_rep_0": err},
        )

        result = agg.build_result(metrics, aggregate)

        assert result.errors["baseline_rep_0"] is err

    def test_build_result_with_provenance(self):
        pipeline = Pipeline([DummyStep()])
        agg = ResultAggregator(pipeline, replicates=2)

        metrics = ExperimentMetrics(
            baseline=TreatmentMetrics({"m": [1, 2]}),
            treatments={},
            hypotheses=[],
        )
        prov_runs = defaultdict(dict)
        prov_runs["baseline"][0] = [{"step": "DummyStep", "cache_hit": False}]
        prov_runs["baseline"][1] = [{"step": "DummyStep", "cache_hit": True}]

        aggregate = AggregateData(
            baseline_metrics={"m": [1, 2]},
            treatment_metrics_dict={},
            baseline_seeds=[10, 11],
            treatment_seeds_agg={},
            provenance_runs=prov_runs,
            errors={},
        )

        result = agg.build_result(metrics, aggregate)

        assert result.provenance["ctx_changes"]["baseline"][0] == [
            {"step": "DummyStep", "cache_hit": False}
        ]
        assert result.provenance["ctx_changes"]["baseline"][1] == [
            {"step": "DummyStep", "cache_hit": True}
        ]
