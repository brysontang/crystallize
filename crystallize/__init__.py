"""Public convenience API for Crystallize."""

from __future__ import annotations

from crystallize.experiments.experiment_graph import ExperimentGraph
from crystallize.experiments.experiment import Experiment
from crystallize.experiments.experiment_builder import ExperimentBuilder
from crystallize.datasources.datasource import DataSource, ExperimentInput
from crystallize.datasources import Artifact
from crystallize.experiments.treatment import Treatment
from crystallize.utils.context import FrozenContext
from crystallize.pipelines.pipeline import PipelineStep
from crystallize.pipelines.pipeline import Pipeline
from crystallize.experiments.hypothesis import Hypothesis

from crystallize.utils.decorators import (
    data_source,
    hypothesis,
    inject_from_ctx,
    pipeline,
    pipeline_step,
    resource_factory,
    treatment,
    verifier,
)
from crystallize.plugins.execution import (
    AsyncExecution,
    ParallelExecution,
    SerialExecution,
)
from crystallize.plugins.plugins import (
    ArtifactPlugin,
    BasePlugin,
    LoggingPlugin,
    SeedPlugin,
)

__all__ = [
    "pipeline_step",
    "inject_from_ctx",
    "treatment",
    "hypothesis",
    "data_source",
    "verifier",
    "pipeline",
    "resource_factory",
    "PipelineStep",
    "Pipeline",
    "Hypothesis",
    "Experiment",
    "DataSource",
    "FrozenContext",
    "Treatment",
    "BasePlugin",
    "SerialExecution",
    "ParallelExecution",
    "AsyncExecution",
    "SeedPlugin",
    "LoggingPlugin",
    "ArtifactPlugin",
    "ExperimentGraph",
    "Artifact",
    "ExperimentInput",
    "ExperimentBuilder",
]
