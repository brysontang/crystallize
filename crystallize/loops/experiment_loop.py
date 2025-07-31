from __future__ import annotations

import importlib.util
import operator
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any, Dict, List, Callable, Awaitable

import yaml

from crystallize.experiments.experiment_graph import ExperimentGraph
from crystallize.plugins.plugins import ArtifactPlugin
from crystallize.utils.context import FrozenContext
from crystallize.utils.constants import BASELINE_CONDITION


OP_MAP = {
    ">": operator.gt,
    ">=": operator.ge,
    "<": operator.lt,
    "<=": operator.le,
    "==": operator.eq,
    "!=": operator.ne,
}


@dataclass
class ConvergenceCondition:
    experiment: str
    metric: str
    condition: str
    operator: str
    threshold: float
    patience: int = 1


@dataclass
class MutationSpec:
    experiment: str
    treatment: str
    replace_context_key: str
    from_artifact: str
    loader: str


class ExperimentLoop:
    """Run a DAG of experiments iteratively with mutation between runs."""

    def __init__(
        self,
        graph: ExperimentGraph,
        eval_experiment: str,
        max_iters: int,
        converge_when: List[ConvergenceCondition],
        mutate: List[MutationSpec],
        loader_module: ModuleType,
    ) -> None:
        self.graph = graph
        self.eval_experiment = eval_experiment
        self.max_iters = max_iters
        self.converge_when = converge_when
        self.mutate = mutate
        self.loader_module = loader_module
        self._patience: Dict[int, int] = {id(c): 0 for c in converge_when}

    @classmethod
    def from_yaml(
        cls, config_path: str | Path
    ) -> "ExperimentLoop":  # pragma: no cover - convenience loader
        path = Path(config_path)
        with open(path) as f:
            cfg = yaml.safe_load(f) or {}
        base = path.parent
        eval_exp = cfg["eval_experiment"]
        graph = ExperimentGraph.from_yaml(base / eval_exp / "config.yaml")
        conditions = [
            ConvergenceCondition(
                experiment=c["experiment"],
                metric=c["metric"],
                condition=c.get("condition", BASELINE_CONDITION),
                operator=c["operator"],
                threshold=float(c["threshold"]),
                patience=int(c.get("patience", 1)),
            )
            for c in cfg.get("converge_when", [])
        ]
        mutations = [
            MutationSpec(
                experiment=m["experiment"],
                treatment=m["treatment"],
                replace_context_key=m["replace_context_key"],
                from_artifact=m["from_artifact"],
                loader=m["loader"],
            )
            for m in cfg.get("mutate", [])
        ]
        loader_mod = cls._load_loader_module(base)
        max_iters = int(cfg.get("max_iters", 1))
        return cls(graph, eval_exp, max_iters, conditions, mutations, loader_mod)

    @staticmethod
    def _load_loader_module(
        base: Path,
    ) -> ModuleType:  # pragma: no cover - convenience loader
        mod_path = base / "loaders.py"
        spec = importlib.util.spec_from_file_location("loop_loaders", mod_path)
        module = ModuleType("loop_loaders")
        if spec and spec.loader and mod_path.exists():
            spec.loader.exec_module(module)  # type: ignore[arg-type]
        return module

    def _set_versions(self, iteration: int) -> None:
        for node in self.graph._graph.nodes:
            exp = self.graph._graph.nodes[node]["experiment"]
            plugin = exp.get_plugin(ArtifactPlugin)
            if plugin is not None:
                plugin.versioned = True
                plugin.version_override = iteration

    def _apply_mutations(self, iteration: int) -> None:
        for m in self.mutate:
            src_exp_name, art_name = m.from_artifact.split("#", 1)
            src_exp = self.graph._graph.nodes[src_exp_name]["experiment"]
            src_plugin = src_exp.get_plugin(ArtifactPlugin)
            if src_plugin is None:
                continue
            base = (
                Path(src_plugin.root_dir)
                / (src_exp.name or src_exp.id)
                / f"v{iteration}"
            )
            matches = list(base.rglob(art_name))
            if not matches:
                continue
            art_path = matches[0]
            loader_fn = getattr(self.loader_module, m.loader)
            new_val = loader_fn(art_path)
            tgt_exp = self.graph._graph.nodes[m.experiment]["experiment"]
            if m.treatment == BASELINE_CONDITION:
                data = dict(tgt_exp._setup_ctx.as_dict())
                data[m.replace_context_key] = new_val
                tgt_exp._setup_ctx = FrozenContext(data)
            else:
                for t in tgt_exp.treatments:
                    if t.name == m.treatment and hasattr(t._apply_fn, "items"):
                        t._apply_fn.items[m.replace_context_key] = new_val
                        break

    def _check_convergence(self, results: Dict[str, Any]) -> bool:
        all_met = True
        for cond in self.converge_when:
            res = results.get(cond.experiment)
            if res is None:
                all_met = False
                continue
            metrics = res.metrics
            if cond.condition == BASELINE_CONDITION:
                vals = metrics.baseline.metrics.get(cond.metric, [])
            else:
                vals = metrics.treatments.get(cond.condition, {}).metrics.get(
                    cond.metric, []
                )
            if not vals:
                met = False
            else:
                val = vals[-1]
                op_fn = OP_MAP.get(cond.operator, operator.eq)
                met = op_fn(val, cond.threshold)
            key = id(cond)
            if met:
                self._patience[key] += 1
            else:
                self._patience[key] = 0
                all_met = False
                continue
            if self._patience[key] < cond.patience:
                all_met = False
        return all_met

    async def arun(
        self,
        *,
        strategy: str = "rerun",
        replicates: int | None = None,
        progress_callback: Callable[[str, str], Awaitable[None]] | None = None,
    ) -> Dict[str, Any]:
        iteration = 0
        results: Dict[str, Any] = {}
        while iteration < self.max_iters:
            self._set_versions(iteration)
            results = await self.graph.arun(
                strategy="rerun",
                replicates=replicates,
                progress_callback=progress_callback,
            )
            if self._check_convergence(results):
                break
            if iteration + 1 >= self.max_iters:
                break
            self._apply_mutations(iteration)
            iteration += 1
        return results
