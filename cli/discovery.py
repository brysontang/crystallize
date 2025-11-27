"""Object discovery utilities for the CLI."""

from __future__ import annotations

import importlib
import importlib.util
import inspect
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Type

import yaml

from crystallize.experiments.experiment_graph import ExperimentGraph
from .errors import ExperimentLoadError, format_load_error


def _import_module(
    file_path: Path, root_path: Path
) -> Tuple[Optional[Any], Optional[BaseException]]:
    """Import ``file_path`` as a module relative to ``root_path``.

    Returns a tuple of the imported module (or ``None`` if import failed) and
    the exception raised during import, if any.
    """
    try:
        relative_path = file_path.relative_to(root_path)
    except ValueError:
        spec = importlib.util.spec_from_file_location(file_path.stem, file_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            try:
                spec.loader.exec_module(module)  # type: ignore[arg-type]
                return module, None
            except BaseException as exc:  # noqa: BLE001
                return None, exc
        return None, RuntimeError("Could not create module spec")

    module_name = ".".join(relative_path.with_suffix("").parts)

    try:
        if str(root_path) not in sys.path:
            sys.path.insert(0, str(root_path))

        if module_name in sys.modules:
            # If module is already imported, reload it to pick up changes
            return importlib.reload(sys.modules[module_name]), None
        else:
            # Otherwise, import it for the first time
            return importlib.import_module(module_name), None
    except BaseException as exc:  # noqa: BLE001
        return None, exc


def _ensure_extras_step_available(step_name: str) -> None:
    """Ensure crystallize-extras is installed when a step references it."""
    message = (
        f"You are trying to use {step_name} but 'crystallize-extras' is not installed. "
        "Please run pip install crystallize-extras."
    )
    try:
        importlib.import_module(step_name)
    except ImportError as exc:
        module_path, _, _ = step_name.rpartition(".")
        if module_path:
            try:
                importlib.import_module(module_path)
                return
            except ImportError as nested_exc:  # pragma: no cover - defensive fallback
                raise RuntimeError(message) from nested_exc
        raise RuntimeError(message) from exc


def _iter_step_names(steps_cfg: list[Any]) -> list[str]:
    """Normalize step definitions to a list of step names."""
    names: list[str] = []
    for step in steps_cfg:
        if isinstance(step, str):
            names.append(step)
        elif isinstance(step, dict):
            names.extend(step.keys())
    return names


def discover_objects(
    directory: Path, obj_type: Type[Any]
) -> Tuple[Dict[str, Any], Dict[str, BaseException]]:
    """Recursively discover objects of ``obj_type`` within ``directory``.

    Returns a mapping of discovered objects and a mapping of file paths to
    import errors for modules that failed to load.
    """
    abs_directory = directory.resolve()
    root_path = Path.cwd()
    found: Dict[str, Any] = {}
    errors: Dict[str, BaseException] = {}
    for file in abs_directory.rglob("*.py"):
        mod, err = _import_module(file, root_path)
        if err is not None:
            errors[str(file)] = err
        if not mod:
            continue
        for name, obj in inspect.getmembers(mod, lambda x: isinstance(x, obj_type)):
            try:
                rel = file.relative_to(root_path)
            except ValueError:
                rel = file
            found[f"{rel}:{name}"] = obj
    return found, errors


def discover_configs(
    directory: Path,
) -> Tuple[
    Dict[str, Dict[str, Any]],
    Dict[str, Dict[str, Any]],
    Dict[str, ExperimentLoadError],
]:
    """Discover experiments and graphs defined via ``config.yaml``."""

    def _has_ref(val: Any) -> bool:
        if isinstance(val, str):
            return "#" in val
        if isinstance(val, dict):
            return any(_has_ref(v) for v in val.values())
        if isinstance(val, list):
            return any(_has_ref(v) for v in val)
        return False

    graphs: Dict[str, Dict[str, Any]] = {}
    experiments: Dict[str, Dict[str, Any]] = {}
    errors: Dict[str, ExperimentLoadError] = {}

    abs_directory = directory.resolve()
    cwd = Path.cwd()

    for cfg in abs_directory.rglob("config.yaml"):
        try:
            with cfg.open() as f:
                data = yaml.safe_load(f) or {}
            name = data.get("name", cfg.parent.name)
            desc = data.get("description", "")
            repl = data.get("replicates", 1)
            cli_cfg = data.get("cli", {}) or {}
            steps_cfg = data.get("steps", []) or []

            for step_name in _iter_step_names(steps_cfg):
                if step_name.startswith("crystallize_extras"):
                    _ensure_extras_step_available(step_name)

            is_graph = _has_ref(data.get("datasource"))

            if cli_cfg.get("hidden"):
                continue

            try:
                rel = cfg.parent.relative_to(cwd)
            except ValueError:
                rel = cfg.parent
            label = f"{rel} - {name}"

            cli_defaults = {
                "group": "Graphs" if is_graph else "Experiments",
                "priority": 999,
                "icon": "📈" if is_graph else "🧪",
                "color": None,
                "hidden": False,
            }
            cli_info = {**cli_defaults, **cli_cfg}

            info = {
                "path": cfg,
                "description": desc,
                "replicates": repl,
                "label": label,
                "cli": cli_info,
            }

            if is_graph:
                graphs[label] = info
            else:
                experiments[label] = info
        except BaseException as exc:  # noqa: BLE001
            errors[str(cfg)] = format_load_error(cfg, exc)

    return graphs, experiments, errors


async def _run_object(obj: Any, strategy: str | None, replicates: Optional[int]) -> Any:
    """Run an ``Experiment`` or ``ExperimentGraph`` asynchronously."""
    if isinstance(obj, ExperimentGraph):
        return await obj.arun(strategy=strategy, replicates=replicates)
    return await obj.arun(
        strategy=strategy,
        replicates=None,
        treatments=getattr(obj, "treatments", None),
        hypotheses=getattr(obj, "hypotheses", None),
    )
