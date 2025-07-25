from __future__ import annotations

from typing import Any, Dict, List, Optional

from crystallize.datasources.datasource import DataSource
from crystallize.experiments.hypothesis import Hypothesis
from crystallize.experiments.treatment import Treatment
from crystallize.pipelines.pipeline import Pipeline
from crystallize.pipelines.pipeline_step import PipelineStep
from crystallize.plugins.plugins import BasePlugin
from crystallize.datasources import Artifact
from .experiment import Experiment


class ExperimentBuilder:
    """Fluent builder for :class:`Experiment`."""

    def __init__(self, name: Optional[str] = None) -> None:
        self._name = name
        self._datasource: Optional[DataSource] = None
        self._steps: List[PipelineStep] = []
        self._pipeline: Optional[Pipeline] = None
        self._plugins: List[BasePlugin] = []
        self._treatments: List[Treatment] = []
        self._hypotheses: List[Hypothesis] = []
        self._replicates: int = 1
        self._description: Optional[str] = None
        self._initial_ctx: Dict[str, Any] = {}
        self._outputs: List[Artifact] = []

    # ------------------------------------------------------------------ #

    def datasource(self, datasource: DataSource) -> "ExperimentBuilder":
        self._datasource = datasource
        return self

    def pipeline(self, pipeline: Pipeline) -> "ExperimentBuilder":
        self._pipeline = pipeline
        return self

    def add_step(self, step: PipelineStep) -> "ExperimentBuilder":
        self._steps.append(step)
        return self

    def plugins(self, plugins: List[BasePlugin]) -> "ExperimentBuilder":
        self._plugins = plugins
        return self

    def treatments(self, treatments: List[Treatment]) -> "ExperimentBuilder":
        self._treatments = treatments
        return self

    def hypotheses(self, hypotheses: List[Hypothesis]) -> "ExperimentBuilder":
        self._hypotheses = hypotheses
        return self

    def replicates(self, replicates: int) -> "ExperimentBuilder":
        self._replicates = replicates
        return self

    def description(self, description: str) -> "ExperimentBuilder":
        self._description = description
        return self

    def initial_ctx(self, initial_ctx: Dict[str, Any]) -> "ExperimentBuilder":
        self._initial_ctx = initial_ctx
        return self

    def outputs(self, outputs: List[Artifact]) -> "ExperimentBuilder":
        self._outputs = outputs
        return self

    def build(self) -> Experiment:
        if self._datasource is None:
            raise ValueError("datasource must be provided")
        pipeline = self._pipeline or Pipeline(self._steps)
        return Experiment(
            datasource=self._datasource,
            pipeline=pipeline,
            plugins=self._plugins,
            description=self._description,
            name=self._name,
            initial_ctx=self._initial_ctx or None,
            outputs=self._outputs,
            treatments=self._treatments,
            hypotheses=self._hypotheses,
            replicates=self._replicates,
        )
