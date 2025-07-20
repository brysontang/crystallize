"""Orchestrator for chaining multiple experiments via a DAG."""

from __future__ import annotations

from typing import Dict, List

import networkx as nx

from .experiment import Experiment
from .result import Result
from .treatment import Treatment


class ExperimentGraph:
    """Manage and run a directed acyclic graph of experiments."""

    def __init__(self) -> None:
        self._graph = nx.DiGraph()
        self._results: Dict[str, Result] = {}

    # ------------------------------------------------------------------ #
    def add_experiment(self, experiment: Experiment) -> None:
        """Add an experiment node to the graph."""
        name = getattr(experiment, "name", None)
        if not name:
            raise ValueError("Experiment must have a name")
        self._graph.add_node(name, experiment=experiment)

    # ------------------------------------------------------------------ #
    def add_dependency(self, downstream: Experiment, upstream: Experiment) -> None:
        """Add an edge from ``upstream`` to ``downstream``."""
        down_name = getattr(downstream, "name", None)
        up_name = getattr(upstream, "name", None)
        if not down_name or not up_name:
            raise ValueError("Both experiments must have a name")
        if down_name not in self._graph or up_name not in self._graph:
            raise ValueError("Experiments must be added to the graph first")
        self._graph.add_edge(up_name, down_name)

    # ------------------------------------------------------------------ #
    def run(
        self,
        treatments: List[Treatment] | None = None,
        replicates: int | None = None,
    ) -> Dict[str, Result]:
        """Execute all experiments respecting dependency order."""
        if not nx.is_directed_acyclic_graph(self._graph):
            raise ValueError("Experiment graph contains cycles")

        order = list(nx.topological_sort(self._graph))
        self._results.clear()

        for name in order:
            exp: Experiment = self._graph.nodes[name]["experiment"]
            result = exp.run(treatments=treatments, replicates=replicates)
            self._results[name] = result

        return self._results
