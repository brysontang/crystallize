"""Orchestrator for chaining multiple experiments via a DAG."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import networkx as nx

from crystallize.datasources.artifacts import Artifact
from crystallize.datasources.datasource import ExperimentInput
from crystallize.plugins.plugins import ArtifactPlugin
from crystallize.utils.constants import BASELINE_CONDITION

from .experiment import Experiment
from .result import Result
from .treatment import Treatment


class ExperimentGraph:
    """Manage and run a directed acyclic graph of experiments."""

    def __init__(self) -> None:
        self._graph = nx.DiGraph()
        self._results: Dict[str, Result] = {}

    # ------------------------------------------------------------------ #
    @classmethod
    def from_experiments(cls, experiments: List[Experiment]) -> "ExperimentGraph":
        """Construct a graph automatically from experiment dependencies.

        Parameters
        ----------
        experiments:
            List of all experiments that form the workflow.

        Returns
        -------
        ExperimentGraph
            Fully built and validated experiment graph.
        """
        artifact_map: Dict[Artifact, Experiment] = {}
        graph = nx.DiGraph()

        for exp in experiments:
            name = getattr(exp, "name", None)
            if not name:
                raise ValueError("Experiment must have a name")
            graph.add_node(name, experiment=exp)
            for art in exp.outputs.values():
                if art in artifact_map and artifact_map[art] is not exp:
                    raise ValueError(
                        f"Artifact '{art.name}' produced by multiple experiments"
                    )
                artifact_map[art] = exp

        for exp in experiments:
            ds = exp.datasource
            if isinstance(ds, ExperimentInput):
                for art in getattr(ds, "required_outputs", []):
                    parent = artifact_map.get(art)
                    if parent is None:
                        raise ValueError(
                            f"Artifact '{art.name}' has no producing experiment"
                        )
                    graph.add_edge(parent.name, exp.name)

        if not nx.is_directed_acyclic_graph(graph):
            raise ValueError("Experiment graph contains cycles")

        components = list(nx.weakly_connected_components(graph))
        if len(components) > 1:
            largest = max(components, key=len)
            unused = sorted(
                set(node for c in components if c is not largest for node in c)
            )
            raise ValueError(
                "Unused experiments detected: " + ", ".join(str(u) for u in unused)
            )

        obj = cls()
        obj._graph = graph
        return obj

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
        strategy: str = "rerun",
    ) -> Dict[str, Result]:
        """Execute all experiments respecting dependency order."""
        if not nx.is_directed_acyclic_graph(self._graph):
            raise ValueError("Experiment graph contains cycles")

        order = list(nx.topological_sort(self._graph))
        self._results.clear()

        for name in order:
            exp: Experiment = self._graph.nodes[name]["experiment"]
            run_strategy = strategy
            if strategy == "resume":
                plugin = exp.get_plugin(ArtifactPlugin)
                if plugin is not None:
                    base = Path(plugin.root_dir) / (exp.name or exp.id) / "v0"
                    all_done = True
                    for cond in [BASELINE_CONDITION] + [t.name for t in exp.treatments]:
                        if not (base / cond / ".crystallize_complete").exists():
                            all_done = False
                            break
                    if all_done:
                        succ = getattr(self._graph, "_succ", {})
                        entry = succ.get(name, {})
                        downstream = list(
                            entry.keys() if isinstance(entry, dict) else entry
                        )
                        skip = True
                        for dn in downstream:
                            dn_exp: Experiment = self._graph.nodes[dn]["experiment"]
                            reqs = getattr(dn_exp.datasource, "required_outputs", [])
                            req_names = {r.name for r in reqs}
                            if not req_names:
                                continue
                            if not req_names.issubset(set(exp.outputs)):
                                continue
                            for out_name in req_names:
                                if not list(base.rglob(out_name)):
                                    skip = False
                                    break
                            if not skip:
                                break
                        if skip:
                            continue
                        run_strategy = "rerun"
            result = exp.run(
                treatments=treatments,
                hypotheses=getattr(exp, "hypotheses", []),
                replicates=replicates or getattr(exp, "replicates", 1),
                strategy=run_strategy,
            )
            self._results[name] = result

        return self._results
