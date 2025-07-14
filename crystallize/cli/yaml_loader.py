from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any, Callable, List, Mapping

try:  # Prefer PyYAML if available
    import yaml  # type: ignore

    def _yaml_load(content: str) -> Any:
        return yaml.safe_load(content)

except Exception:  # pragma: no cover - fallback when PyYAML missing

    def _yaml_load(content: str) -> Any:
        return json.loads(content)


from crystallize.core.execution import ParallelExecution, SerialExecution
from crystallize.core.plugins import LoggingPlugin, SeedPlugin
from crystallize.core.experiment import Experiment
from crystallize.core.hypothesis import Hypothesis
from crystallize.core.pipeline import Pipeline
from crystallize.core.pipeline_step import PipelineStep
from crystallize.core.treatment import Treatment


def _load_attr(path: str) -> Any:
    module_name, attr_name = path.rsplit(".", 1)
    module = importlib.import_module(module_name)
    return getattr(module, attr_name)


def _instantiate(spec: Mapping[str, Any]) -> Any:
    target = spec["target"]
    params = spec.get("params", {})
    obj = _load_attr(target)
    return obj(**params)


def _build_apply_fn(spec: Mapping[str, Any]) -> Callable[[Any], None]:
    fn = _load_attr(spec["target"])
    params = spec.get("params", {})

    def apply(ctx: Any) -> None:
        fn(ctx, **params)

    return apply


def load_experiment(config: Mapping[str, Any]) -> Experiment:
    datasource = _instantiate(config["datasource"])

    steps: List[PipelineStep] = [
        _instantiate(step_spec) for step_spec in config.get("pipeline", [])
    ]
    pipeline = Pipeline(steps)

    hypotheses: List[Hypothesis] = []
    if "hypotheses" in config:
        hyp_specs = config["hypotheses"]
    else:
        hyp_specs = [config["hypothesis"]]

    for spec in hyp_specs:
        verifier_fn = _instantiate(spec["verifier"])
        ranker_fn = _load_attr(spec["ranker"])
        hypotheses.append(
            Hypothesis(
                verifier=verifier_fn,
                metrics=spec.get("metrics", spec.get("metric")),
                ranker=ranker_fn,
                name=spec.get("name"),
            )
        )

    treatments = []
    for t_spec in config.get("treatments", []):
        apply_fn = _build_apply_fn(t_spec["apply"])
        treatments.append(Treatment(t_spec["name"], apply_fn))

    replicates = int(config.get("replicates", 1))

    parallel = bool(config.get("parallel", False))
    max_workers = config.get("max_workers")
    if max_workers is not None:
        max_workers = int(max_workers)
    executor_type = config.get("executor_type", "thread")
    if parallel:
        exec_plugin = ParallelExecution(max_workers=max_workers, executor_type=executor_type)
    else:
        exec_plugin = SerialExecution()

    seed = config.get("seed")
    auto_seed = bool(config.get("auto_seed", True))
    seed_fn_path = config.get("seed_fn")
    seed_fn = _load_attr(seed_fn_path) if seed_fn_path else None
    seed_plugin = SeedPlugin(seed=seed, auto_seed=auto_seed, seed_fn=seed_fn)

    verbose = bool(config.get("verbose", False))
    log_level = config.get("log_level", "INFO")
    log_plugin = LoggingPlugin(verbose=verbose, log_level=log_level)

    exp = Experiment(
        datasource=datasource,
        pipeline=pipeline,
        treatments=treatments,
        hypotheses=hypotheses,
        replicates=replicates,
        plugins=[exec_plugin, seed_plugin, log_plugin],
    )
    return exp


def load_experiment_from_file(path: str | Path) -> Experiment:
    with Path(path).open() as f:
        config = _yaml_load(f.read())
    if not isinstance(config, Mapping):
        raise ValueError("YAML root must be a mapping")
    return load_experiment(config)
