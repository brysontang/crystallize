"""Tests for crystallize.experiments.experiment_builder module."""

import pytest

from crystallize.datasources.datasource import DataSource
from crystallize.datasources import Artifact
from crystallize.experiments.experiment_builder import ExperimentBuilder
from crystallize.experiments.hypothesis import Hypothesis
from crystallize.experiments.treatment import Treatment
from crystallize.pipelines.pipeline import Pipeline
from crystallize.pipelines.pipeline_step import PipelineStep
from crystallize.plugins.plugins import BasePlugin
from crystallize.utils.context import FrozenContext


class DummyDataSource(DataSource):
    """Simple datasource for testing."""

    def fetch(self, ctx: FrozenContext):
        return 0


class DummyStep(PipelineStep):
    """Simple step for testing."""

    def __call__(self, data, ctx):
        return data

    @property
    def params(self):
        return {}


class DummyPlugin(BasePlugin):
    """Simple plugin for testing."""

    pass


def dummy_verifier(baseline, treatment):
    return {"p_value": 0.05, "significant": True, "accepted": True}


class TestExperimentBuilder:
    """Tests for ExperimentBuilder class."""

    def test_init_with_name(self) -> None:
        """Test builder initialization with a name."""
        builder = ExperimentBuilder(name="test_experiment")
        assert builder._name == "test_experiment"

    def test_init_without_name(self) -> None:
        """Test builder initialization without a name."""
        builder = ExperimentBuilder()
        assert builder._name is None

    def test_datasource_method(self) -> None:
        """Test datasource() method sets datasource."""
        builder = ExperimentBuilder()
        ds = DummyDataSource()
        result = builder.datasource(ds)

        assert result is builder  # Returns self for chaining
        assert builder._datasource is ds

    def test_pipeline_method(self) -> None:
        """Test pipeline() method sets pipeline."""
        builder = ExperimentBuilder()
        pipeline = Pipeline([DummyStep()])
        result = builder.pipeline(pipeline)

        assert result is builder
        assert builder._pipeline is pipeline

    def test_add_step_method(self) -> None:
        """Test add_step() method appends steps."""
        builder = ExperimentBuilder()
        step1 = DummyStep()
        step2 = DummyStep()

        builder.add_step(step1).add_step(step2)

        assert len(builder._steps) == 2
        assert builder._steps[0] is step1
        assert builder._steps[1] is step2

    def test_plugins_method(self) -> None:
        """Test plugins() method sets plugins."""
        builder = ExperimentBuilder()
        plugins = [DummyPlugin(), DummyPlugin()]
        result = builder.plugins(plugins)

        assert result is builder
        assert builder._plugins == plugins

    def test_treatments_method(self) -> None:
        """Test treatments() method sets treatments."""
        builder = ExperimentBuilder()
        treatments = [
            Treatment("treat_a", {"param": 1}),
            Treatment("treat_b", {"param": 2}),
        ]
        result = builder.treatments(treatments)

        assert result is builder
        assert builder._treatments == treatments

    def test_hypotheses_method(self) -> None:
        """Test hypotheses() method sets hypotheses."""
        builder = ExperimentBuilder()
        hypotheses = [
            Hypothesis(verifier=dummy_verifier, metrics="metric"),
        ]
        result = builder.hypotheses(hypotheses)

        assert result is builder
        assert builder._hypotheses == hypotheses

    def test_replicates_method(self) -> None:
        """Test replicates() method sets replicates."""
        builder = ExperimentBuilder()
        result = builder.replicates(5)

        assert result is builder
        assert builder._replicates == 5

    def test_description_method(self) -> None:
        """Test description() method sets description."""
        builder = ExperimentBuilder()
        result = builder.description("My experiment description")

        assert result is builder
        assert builder._description == "My experiment description"

    def test_initial_ctx_method(self) -> None:
        """Test initial_ctx() method sets initial context."""
        builder = ExperimentBuilder()
        ctx = {"key": "value", "number": 42}
        result = builder.initial_ctx(ctx)

        assert result is builder
        assert builder._initial_ctx == ctx

    def test_outputs_method(self) -> None:
        """Test outputs() method sets outputs."""
        builder = ExperimentBuilder()
        outputs = [Artifact("output.txt")]
        result = builder.outputs(outputs)

        assert result is builder
        assert builder._outputs == outputs

    def test_build_creates_experiment(self) -> None:
        """Test build() creates an Experiment with all settings."""
        builder = (
            ExperimentBuilder(name="test")
            .datasource(DummyDataSource())
            .add_step(DummyStep())
            .replicates(3)
            .description("A test experiment")
        )

        experiment = builder.build()

        assert experiment.name == "test"
        assert experiment.description == "A test experiment"

    def test_build_uses_pipeline_if_provided(self) -> None:
        """Test build() uses provided pipeline over steps."""
        pipeline = Pipeline([DummyStep()])
        step = DummyStep()  # This should be ignored

        builder = (
            ExperimentBuilder()
            .datasource(DummyDataSource())
            .pipeline(pipeline)
            .add_step(step)
        )

        experiment = builder.build()

        # The pipeline should be the explicitly provided one
        assert experiment.pipeline is pipeline

    def test_build_creates_pipeline_from_steps(self) -> None:
        """Test build() creates pipeline from steps if no pipeline provided."""
        step1 = DummyStep()
        step2 = DummyStep()

        builder = (
            ExperimentBuilder()
            .datasource(DummyDataSource())
            .add_step(step1)
            .add_step(step2)
        )

        experiment = builder.build()

        assert len(experiment.pipeline.steps) == 2

    def test_build_without_datasource_raises(self) -> None:
        """Test build() raises ValueError if datasource not provided."""
        builder = ExperimentBuilder().add_step(DummyStep())

        with pytest.raises(ValueError, match="datasource must be provided"):
            builder.build()

    def test_fluent_chaining(self) -> None:
        """Test that all methods can be chained fluently."""
        experiment = (
            ExperimentBuilder(name="chained")
            .datasource(DummyDataSource())
            .pipeline(Pipeline([DummyStep()]))
            .plugins([DummyPlugin()])
            .treatments([Treatment("t", {})])
            .hypotheses([])
            .replicates(2)
            .description("Chained experiment")
            .initial_ctx({"key": "value"})
            .outputs([Artifact("out.txt")])
            .build()
        )

        assert experiment.name == "chained"
        assert experiment.description == "Chained experiment"

    def test_build_with_empty_initial_ctx(self) -> None:
        """Test build() handles empty initial_ctx correctly."""
        builder = (
            ExperimentBuilder()
            .datasource(DummyDataSource())
            .add_step(DummyStep())
            .initial_ctx({})
        )

        # Should build without error
        experiment = builder.build()
        assert experiment is not None

    def test_default_values(self) -> None:
        """Test that builder has correct default values."""
        builder = ExperimentBuilder()

        assert builder._name is None
        assert builder._datasource is None
        assert builder._steps == []
        assert builder._pipeline is None
        assert builder._plugins == []
        assert builder._treatments == []
        assert builder._hypotheses == []
        assert builder._replicates == 1
        assert builder._description is None
        assert builder._initial_ctx == {}
        assert builder._outputs == []
