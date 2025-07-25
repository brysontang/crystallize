"""Orchestrator for chaining multiple experiments via a DAG."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Callable, Awaitable
import json

import networkx as nx

from crystallize.datasources.artifacts import Artifact
from crystallize.datasources.datasource import ExperimentInput
from crystallize.plugins.plugins import ArtifactPlugin
from crystallize.utils.constants import BASELINE_CONDITION

from .experiment import Experiment
from .result import Result
from .result_structs import ExperimentMetrics, TreatmentMetrics
from .treatment import Treatment


class ExperimentGraph:
    """Manage and run a directed acyclic graph of experiments."""

    def __init__(self, *experiments: Experiment, name: str | None = None) -> None:
        """Create a graph and optionally infer dependencies from experiments."""
        self._graph = nx.DiGraph()
        self._results: Dict[str, Result] = {}
        self._name = name

        if experiments:
            tmp = self.__class__.from_experiments(list(experiments))
            self._graph = tmp._graph
            if name is None:
                self._name = tmp._name

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

            required_artifacts = []
            if isinstance(ds, ExperimentInput):
                required_artifacts = getattr(ds, "required_outputs", [])
            elif isinstance(ds, Artifact):
                required_artifacts = [ds]

            for art in required_artifacts:
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

        # Infer graph name from the “final” experiment(s) — those with no successors
        final_nodes = [node for node, children in graph._succ.items() if not children]
        graph_name = final_nodes[0] if len(final_nodes) == 1 else "ExperimentGraph"

        obj = cls(name=graph_name)
        obj._graph = graph
        return obj

    # ------------------------------------------------------------------ #

    @classmethod
    def from_yaml(cls, directory: str | Path) -> "ExperimentGraph":
        """Load all experiments in ``directory`` and build a graph."""

        base = Path(directory)
        experiments: list[Experiment] = []
        artifact_map: dict[tuple[str, str], Artifact] = {}

        for exp_dir in sorted(p for p in base.iterdir() if p.is_dir()):
            cfg = exp_dir / "config.yaml"
            if not cfg.exists():
                continue  # pragma: no cover - requires malformed directory
            exp = Experiment.from_yaml(cfg)
            experiments.append(exp)
            for name, art in exp.outputs.items():
                artifact_map[(exp.name or exp_dir.name, name)] = art

        for exp in experiments:
            ds = exp.datasource
            if isinstance(ds, ExperimentInput):
                updated = {}
                for alias, art in ds._inputs.items():
                    if isinstance(art, Artifact) and hasattr(art, "_source_experiment"):
                        key = (getattr(art, "_source_experiment"), art.name)
                        updated[alias] = artifact_map[key]  # pragma: no cover - integration tested
                    else:
                        updated[alias] = art
                exp.datasource = ExperimentInput(**updated)
            elif isinstance(ds, Artifact) and hasattr(ds, "_source_experiment"):
                key = (getattr(ds, "_source_experiment"), ds.name)
                exp.datasource = artifact_map[key]  # pragma: no cover - integration tested

        return cls.from_experiments(experiments)

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
        """Synchronous wrapper for the async arun method."""
        import asyncio

        return asyncio.run(
            self.arun(treatments=treatments, replicates=replicates, strategy=strategy)
        )

    async def arun(
        self,
        treatments: List[Treatment] | None = None,
        replicates: int | None = None,
        strategy: str = "rerun",
        progress_callback: Callable[[str, str], Awaitable[None]] | None = None,
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

                    run_treatments = treatments or []
                    exp_treatments_on_obj = getattr(exp, "treatments", [])
                    if exp_treatments_on_obj:
                        existing_names = {t.name for t in run_treatments}
                        run_treatments.extend(
                            [
                                t
                                for t in exp_treatments_on_obj
                                if t.name not in existing_names
                            ]
                        )

                    conditions_to_check = [BASELINE_CONDITION] + [
                        t.name for t in run_treatments
                    ]

                    all_done = True
                    for cond in conditions_to_check:
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
                            relevant_artifacts_to_check = req_names.intersection(
                                set(exp.outputs)
                            )

                            if not relevant_artifacts_to_check:
                                continue

                            for out_name in relevant_artifacts_to_check:
                                if not list(base.rglob(out_name)):
                                    skip = False
                                    break
                        if skip:
                            loaded_baseline: Dict[str, List[Any]] = {}
                            loaded_treatments: Dict[str, Dict[str, List[Any]]] = {}
                            for cond in [BASELINE_CONDITION] + [
                                t.name for t in exp.treatments
                            ]:
                                res_path = base / cond / "results.json"
                                if not res_path.exists():
                                    continue
                                with open(res_path) as f:
                                    data = json.load(f).get("metrics", {})
                                if cond == BASELINE_CONDITION:
                                    loaded_baseline = data
                                else:
                                    loaded_treatments[cond] = data
                            metrics = ExperimentMetrics(
                                baseline=TreatmentMetrics(loaded_baseline),
                                treatments={
                                    n: TreatmentMetrics(m)
                                    for n, m in loaded_treatments.items()
                                },
                                hypotheses=exp._verify_hypotheses(
                                    loaded_baseline,
                                    loaded_treatments,
                                ),
                            )
                            self._results[name] = Result(metrics=metrics)
                            if progress_callback:
                                await progress_callback("completed", name)
                            continue
                        run_strategy = "rerun"

            if progress_callback:
                await progress_callback("running", name)

            final_treatments_for_exp = (
                treatments if treatments is not None else getattr(exp, "treatments", [])
            )

            result = await exp.arun(
                treatments=final_treatments_for_exp,
                hypotheses=getattr(exp, "hypotheses", []),
                replicates=replicates or getattr(exp, "replicates", 1),
                strategy=run_strategy,
            )

            self._results[name] = result

            if progress_callback:
                await progress_callback("completed", name)
        return self._results
