"""Object discovery utilities for the CLI."""
from __future__ import annotations

import importlib.util
import inspect
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Type

from crystallize.experiments.experiment_graph import ExperimentGraph


def _import_module(file_path: Path, root_path: Path) -> Optional[Any]:
    """Import ``file_path`` as a module relative to ``root_path``."""
    try:
        relative_path = file_path.relative_to(root_path)
    except ValueError:
        spec = importlib.util.spec_from_file_location(file_path.stem, file_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            try:
                spec.loader.exec_module(module)  # type: ignore[arg-type]
                return module
            except Exception:
                return None
        return None

    module_name = ".".join(relative_path.with_suffix("").parts)

    try:
        if str(root_path) not in sys.path:
            sys.path.insert(0, str(root_path))
        return importlib.import_module(module_name)
    except Exception:
        return None


def discover_objects(directory: Path, obj_type: Type[Any]) -> Dict[str, Any]:
    """Recursively discover objects of ``obj_type`` within ``directory``."""
    abs_directory = directory.resolve()
    root_path = Path.cwd()
    found: Dict[str, Any] = {}
    for file in abs_directory.rglob("*.py"):
        mod = _import_module(file, root_path)
        if not mod:
            continue
        for name, obj in inspect.getmembers(mod, lambda x: isinstance(x, obj_type)):
            try:
                rel = file.relative_to(root_path)
            except ValueError:
                rel = file
            found[f"{rel}:{name}"] = obj
    return found


async def _run_object(obj: Any, strategy: str, replicates: Optional[int]) -> Any:
    """Run an ``Experiment`` or ``ExperimentGraph`` asynchronously."""
    if isinstance(obj, ExperimentGraph):
        return await obj.arun(strategy=strategy, replicates=replicates)
    return await obj.arun(
        strategy=strategy,
        replicates=None,
        treatments=getattr(obj, "treatments", None),
        hypotheses=getattr(obj, "hypotheses", None),
    )
