"""Pipeline steps composing the agentic harness."""

from __future__ import annotations

import ast
import builtins as py_builtins
import copy
import hashlib
import json
import logging
import multiprocessing as mp
import textwrap
import uuid
from dataclasses import asdict
from multiprocessing.connection import Connection
from typing import Any, Callable, Dict, Iterable, Mapping, MutableMapping, Optional, Tuple

from crystallize import FrozenContext, pipeline_step

from .schema import Claim, Spec

_logger = logging.getLogger(__name__)

# Normalises import lists into deterministic tuples so repeated guards don't
# rebuild set/tuple structures on every invocation.
def _normalise_allowed_imports(allowed_imports: Iterable[str]) -> Tuple[str, ...]:
    """Normalise an iterable of modules into a stable tuple."""

    normalised = {
        module.strip(): None
        for module in allowed_imports
        if isinstance(module, str) and module.strip()
    }
    return tuple(sorted(normalised))


SAFE_BUILTINS: Dict[str, Any] = {
    "len": len,
    "range": range,
    "sum": sum,
    "min": min,
    "max": max,
    "enumerate": enumerate,
    "zip": zip,
    "abs": abs,
    "sorted": sorted,
    "map": map,
    "filter": filter,
    "all": all,
    "any": any,
    "dict": dict,
    "list": list,
    "tuple": tuple,
    "set": set,
    "float": float,
    "int": int,
    "str": str,
    "bool": bool,
    "print": print,
    "Exception": Exception,
    "ValueError": ValueError,
}

LLMCallable = Callable[[Claim, Any, FrozenContext], Any]

FORBIDDEN_DUNDER_NAMES = {
    "__class__",
    "__mro__",
    "__subclasses__",
    "__getattribute__",
    "__getattr__",
    "__dict__",
    "__bases__",
    "__base__",
    "__globals__",
    "__reduce__",
    "__reduce_ex__",
}


def record_llm_call(
    ctx: FrozenContext,
    call: Mapping[str, Any],
    *,
    prefix: str = "llm_call",
) -> str:
    """Persist metadata about an LLM invocation in the immutable context."""

    key = f"{prefix}_{uuid.uuid4().hex}"
    ctx.add(key, dict(call))
    return key


def _coerce_claim(claim: Claim | Mapping[str, Any]) -> Claim:
    if isinstance(claim, Claim):
        return claim
    return Claim(**dict(claim))


def _coerce_spec(payload: Spec | Mapping[str, Any]) -> Spec:
    if isinstance(payload, Spec):
        return payload
    return Spec(**dict(payload))


def _parse_llm_response(
    response: Any,
) -> Tuple[Any, Optional[Mapping[str, Any]]]:
    if isinstance(response, tuple) and len(response) == 2:
        return response[0], response[1]
    return response, None


def _build_import_guard(allowed_imports: Iterable[str]) -> Callable[..., Any]:
    allowed = _normalise_allowed_imports(allowed_imports)
    original_import = py_builtins.__import__

    def guarded_import(name: str, globals=None, locals=None, fromlist=(), level: int = 0):
        if level != 0:
            raise BoundedExecutionError("Relative imports are not supported")
        target = name
        if not any(target == mod or target.startswith(f"{mod}.") for mod in allowed):
            raise BoundedExecutionError(f"Import not allowed: {target}")
        return original_import(name, globals, locals, fromlist, level)

    return guarded_import


@pipeline_step()
def specify_claim(
    data: Any,
    ctx: FrozenContext,
    *,
    claim: Claim | Mapping[str, Any],
) -> Tuple[Tuple[Claim, Any], Dict[str, Any]]:
    claim_obj = _coerce_claim(claim)
    ctx.add("claim", claim_obj)
    ctx.add("raw_data", data)
    return (claim_obj, data), {"claim_id": claim_obj.id}


@pipeline_step()
def generate_spec(
    data: Tuple[Claim, Any],
    ctx: FrozenContext,
    *,
    llm: Optional[LLMCallable] = None,
    spec: Optional[Spec | Mapping[str, Any]] = None,
) -> Tuple[Tuple[Claim, Spec, Any], Dict[str, Any]]:
    claim_obj, raw = data
    if spec is None and llm is None:
        raise ValueError("Either a spec or an llm callable must be provided.")
    if spec is None and llm is not None:
        response = llm(claim_obj, raw, ctx)
        payload, metadata = _parse_llm_response(response)
        spec = _coerce_spec(payload)
        if metadata is not None:
            if "llm_call" in metadata and isinstance(metadata["llm_call"], Mapping):
                record_llm_call(ctx, metadata["llm_call"])
            elif "llm_calls" in metadata and isinstance(
                metadata["llm_calls"], Iterable
            ):
                for idx, item in enumerate(metadata["llm_calls"]):
                    if isinstance(item, Mapping):
                        record_llm_call(ctx, item, prefix=f"llm_call_{idx}")
    assert spec is not None
    spec_obj = _coerce_spec(spec)
    ctx.add("spec", spec_obj)
    metadata = {"spec_json": json.dumps(asdict(spec_obj), sort_keys=True)}
    return (claim_obj, spec_obj, raw), metadata


class BoundedExecutionError(RuntimeError):
    """Raised when bounded synthesis or execution fails validation."""


def _module_allowed(name: str, allowed: Iterable[str]) -> bool:
    for mod in allowed:
        if name == mod or name.startswith(f"{mod}."):
            return True
    return False


def _ast_allowlisted(tree: ast.AST, allowed_imports: Iterable[str]) -> None:
    allowed = _normalise_allowed_imports(allowed_imports)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if not _module_allowed(alias.name, allowed):
                    raise BoundedExecutionError(f"Import not allowed: {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            if node.level and node.level != 0:
                raise BoundedExecutionError("Relative imports are not supported")
            module_name = node.module or ""
            if module_name and not _module_allowed(module_name, allowed):
                raise BoundedExecutionError(f"Import not allowed: {module_name}")
        if isinstance(node, (ast.Global, ast.Nonlocal, ast.With, ast.Try, ast.AsyncWith, ast.AsyncFor)):
            raise BoundedExecutionError(f"Forbidden syntax: {type(node).__name__}")
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in {"eval", "exec", "__import__", "open"}:
                raise BoundedExecutionError(f"Forbidden call: {node.func.id}")
        if isinstance(node, ast.Attribute) and node.attr in FORBIDDEN_DUNDER_NAMES:
            raise BoundedExecutionError(f"Forbidden attribute: {node.attr}")
        if isinstance(node, ast.Name) and node.id in FORBIDDEN_DUNDER_NAMES:
            raise BoundedExecutionError(f"Forbidden name: {node.id}")


def _capsule_worker(
    conn: Connection,
    code_str: str,
    func_name: str,
    payload: Any,
    time_limit: int,
    memory_limit: int,
    allowed_imports: Iterable[str],
) -> None:
    allowed_modules = _normalise_allowed_imports(allowed_imports)
    try:
        try:
            import resource

            soft = hard = memory_limit * 1024 * 1024
            resource.setrlimit(resource.RLIMIT_AS, (soft, hard))
            resource.setrlimit(resource.RLIMIT_CPU, (time_limit, time_limit))
            if hasattr(resource, "RLIMIT_FSIZE"):
                fsize = 2 * 1024 * 1024
                resource.setrlimit(resource.RLIMIT_FSIZE, (fsize, fsize))
        except Exception:
            pass
        safe_builtins = SAFE_BUILTINS.copy()
        safe_builtins["__import__"] = _build_import_guard(allowed_modules)
        namespace: Dict[str, Any] = {"__builtins__": safe_builtins}
        import sys
        import importlib

        original_import_module = importlib.import_module

        def guarded_import_module(name: str, package: Optional[str] = None):
            if not _module_allowed(name, allowed_modules):
                raise BoundedExecutionError(f"Import not allowed: {name}")
            return original_import_module(name, package)

        importlib.import_module = guarded_import_module  # type: ignore[assignment]

        mods_before = set(sys.modules.keys())
        exec(code_str, namespace)
        func = namespace.get(func_name)
        if not callable(func):
            raise BoundedExecutionError(
                f"Entrypoint '{func_name}' missing or not callable"
            )
        result = func(payload)
        mods_after = set(sys.modules.keys())
        new_modules = mods_after - mods_before
        builtin_roots = set(sys.builtin_module_names)
        runtime_allowed = set(allowed_modules) | builtin_roots | {"encodings"}

        def _module_is_allowed(name: str) -> bool:
            if _module_allowed(name, runtime_allowed):
                return True
            root = name.split(".", 1)[0]
            if root in runtime_allowed:
                return True
            return name == root and any(
                mod.startswith(f"{root}.") or mod == root for mod in runtime_allowed
            )

        suspicious = [
            name
            for name in new_modules
            if name
            and not _module_is_allowed(name)
            and not name.startswith("multiprocessing")
        ]
        if suspicious:
            raise BoundedExecutionError(
                f"Loaded disallowed modules: {sorted(suspicious)}"
            )
        conn.send(("ok", result))
    except BaseException as exc:  # pragma: no cover - defensive
        conn.send(("err", {"type": type(exc).__name__, "message": str(exc)}))
    finally:
        conn.close()


def _run_in_capsule(
    code_str: str,
    entrypoint: str,
    payload: Any,
    *,
    time_limit: int,
    memory_limit: int,
    allowed_imports: Iterable[str],
    ) -> Dict[str, Any]:
    ctx = mp.get_context("spawn")
    parent_conn, child_conn = ctx.Pipe(duplex=False)
    process = ctx.Process(
        target=_capsule_worker,
        args=(
            child_conn,
            code_str,
            entrypoint,
            payload,
            time_limit,
            memory_limit,
            _normalise_allowed_imports(allowed_imports),
        ),
    )
    process.daemon = True
    try:
        process.start()
    except Exception:
        child_conn.close()
        parent_conn.close()
        raise
    child_conn.close()
    process.join(time_limit + 2)
    if process.is_alive():
        process.terminate()
        process.join()
        parent_conn.close()
        return {"status": "timeout"}
    status: str
    value: Any
    if parent_conn.poll():
        status, value = parent_conn.recv()
    else:
        status, value = "err", {"type": "RuntimeError", "message": "no result"}
    parent_conn.close()
    return {"status": status, "value": value}


@pipeline_step()
def bounded_synthesis(
    data: Tuple[Claim, Spec, Any],
    ctx: FrozenContext,
    *,
    llm: Optional[LLMCallable] = None,
    code: Optional[str] = None,
    entrypoint: str = "fit_and_eval",
) -> Tuple[Tuple[Claim, Spec, str, Any], Dict[str, Any]]:
    claim_obj, spec_obj, raw = data
    if code is None and llm is None:
        raise ValueError("Either code or an llm callable must be provided.")
    if code is None and llm is not None:
        response = llm(claim_obj, spec_obj, ctx)
        payload, metadata = _parse_llm_response(response)
        if metadata is not None:
            if "llm_call" in metadata and isinstance(metadata["llm_call"], Mapping):
                record_llm_call(ctx, metadata["llm_call"])
            elif "llm_calls" in metadata and isinstance(
                metadata["llm_calls"], Iterable
            ):
                for idx, item in enumerate(metadata["llm_calls"]):
                    if isinstance(item, Mapping):
                        record_llm_call(ctx, item, prefix=f"llm_call_{idx}")
        code = str(payload)
    assert code is not None
    code_str = textwrap.dedent(code)
    tree = ast.parse(code_str)
    _ast_allowlisted(tree, spec_obj.allowed_imports)
    entrypoint_node = next(
        (
            node
            for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == entrypoint
        ),
        None,
    )
    if entrypoint_node is None:
        raise BoundedExecutionError(
            f"Generated code must define the entrypoint '{entrypoint}'"
        )
    if isinstance(entrypoint_node, ast.AsyncFunctionDef):
        raise BoundedExecutionError(
            f"Entrypoint '{entrypoint}' must be a sync function, not async"
        )
    ctx.add("generated_code", code_str)
    code_hash = hashlib.sha256(code_str.encode("utf-8")).hexdigest()
    metadata = {"code_sha": code_hash}
    return (claim_obj, spec_obj, code_str, raw), metadata


@pipeline_step()
def execute_capsule(
    data: Tuple[Claim, Spec, str, Any],
    ctx: FrozenContext,
    *,
    entrypoint: str = "fit_and_eval",
) -> Tuple[Tuple[Claim, Spec, Dict[str, Any]], Dict[str, Any]]:
    claim_obj, spec_obj, code_str, raw = data
    limits = spec_obj.resources or {}
    result = _run_in_capsule(
        code_str,
        entrypoint,
        raw,
        time_limit=limits.get("time_s", 10),
        memory_limit=limits.get("mem_mb", 1024),
        allowed_imports=spec_obj.allowed_imports,
    )
    if result.get("status") != "ok":
        raise BoundedExecutionError(f"Execution failed: {result}")
    capsule_output = result["value"]
    if not isinstance(capsule_output, MutableMapping):
        raise BoundedExecutionError(
            "Capsule execution must return a mapping of metrics"
        )
    ctx.add("capsule_output", dict(capsule_output))
    metadata = {k: v for k, v in capsule_output.items() if isinstance(v, (int, float))}
    return (claim_obj, spec_obj, dict(capsule_output)), metadata


def _permute_rows(payload: Any) -> Any:
    if isinstance(payload, tuple):
        return tuple(_permute_rows(item) for item in payload)
    if isinstance(payload, list):
        return list(reversed(payload))
    try:
        import numpy as np  # type: ignore

        if isinstance(payload, np.ndarray):  # pragma: no cover - optional
            return payload[::-1]
    except Exception:  # pragma: no cover - optional import
        pass
    try:
        return payload[::-1]
    except Exception:
        return payload


def _permute_rows_aligned(payload: Any) -> Any:
    if isinstance(payload, tuple) and payload:
        try:
            length = len(payload[0])
        except Exception:
            _logger.debug("Cannot determine length of first tuple element; falling back to _permute_rows")
            return _permute_rows(payload)
        if length == 0:
            return payload
        indices = list(range(length))[::-1]
        permuted_items = []
        for idx_item, item in enumerate(payload):
            try:
                import numpy as np  # type: ignore  # pragma: no cover - optional

                if isinstance(item, np.ndarray):
                    permuted_items.append(item[indices])
                    continue
            except Exception:  # pragma: no cover - numpy optional
                pass
            try:
                permuted_items.append(type(item)(item[idx] for idx in indices))
                continue
            except Exception:
                _logger.debug(
                    "Could not reconstruct type %s for item %d; trying list fallback",
                    type(item).__name__,
                    idx_item,
                )
            try:
                permuted_items.append([item[idx] for idx in indices])
                continue
            except Exception:
                _logger.debug(
                    "Could not index item %d of type %s; leaving unchanged",
                    idx_item,
                    type(item).__name__,
                )
                permuted_items.append(item)
        return tuple(permuted_items)
    return _permute_rows(payload)


DEFAULT_TRANSFORMS: Dict[str, Callable[[Any], Any]] = {
    "permute_rows": _permute_rows,
    "permute_rows_aligned": _permute_rows_aligned,
    "identity": lambda payload: payload,
}


def _extract_transform_name(property_spec: Mapping[str, Any]) -> Optional[str]:
    transform = property_spec.get("transform")
    if isinstance(transform, str) and transform.strip():
        return transform.strip()
    metamorphic = property_spec.get("metamorphic")
    if isinstance(metamorphic, str) and metamorphic.strip():
        token = metamorphic.strip().split("(", 1)[0]
        return token.strip()
    return None


def _compare_metric(
    base: Mapping[str, Any],
    treatment: Mapping[str, Any],
    *,
    metric: Optional[str],
    tolerance: float,
) -> bool:
    if metric is not None:
        base_val = base.get(metric)
        treatment_val = treatment.get(metric)
        if isinstance(base_val, (int, float)) and isinstance(treatment_val, (int, float)):
            return abs(float(base_val) - float(treatment_val)) <= tolerance
        return base_val == treatment_val
    numeric_keys = [
        key
        for key, base_val in base.items()
        if isinstance(base_val, (int, float))
        and isinstance(treatment.get(key), (int, float))
    ]
    for key in numeric_keys:
        base_val = float(base[key])
        treatment_val = float(treatment[key])
        if abs(base_val - treatment_val) > tolerance:
            return False
    return True


@pipeline_step()
def run_metamorphic_tests(
    data: Tuple[Claim, Spec, Dict[str, Any]],
    ctx: FrozenContext,
    *,
    entrypoint: str = "fit_and_eval",
    transforms: Optional[Mapping[str, Callable[[Any], Any]]] = None,
    tolerance: float = 1e-6,
) -> Tuple[Tuple[Claim, Spec, Dict[str, Any]], Dict[str, Any]]:
    claim_obj, spec_obj, base_metrics = data
    if not spec_obj.properties:
        return data, {}
    code_str = ctx.get("generated_code")
    raw_payload = ctx.get("raw_data")
    if code_str is None or raw_payload is None:
        raise BoundedExecutionError(
            "Metamorphic tests require generated code and raw data in context"
        )
    metadata: Dict[str, Any] = {}
    for property_spec in spec_obj.properties:
        if not isinstance(property_spec, Mapping):
            continue
        name = property_spec.get("name")
        transform_name = _extract_transform_name(property_spec)
        if not name or not transform_name:
            continue
        custom_transforms = transforms or {}
        transform_fn = custom_transforms.get(transform_name) or DEFAULT_TRANSFORMS.get(
            transform_name
        )
        if transform_fn is None:
            raise BoundedExecutionError(
                f"Unknown metamorphic transform '{transform_name}'"
            )
        try:
            payload_copy = copy.deepcopy(raw_payload)
        except Exception:
            payload_copy = raw_payload
        transformed_payload = transform_fn(payload_copy)
        limits = spec_obj.resources or {}
        result = _run_in_capsule(
            code_str,
            entrypoint,
            transformed_payload,
            time_limit=limits.get("time_s", 10),
            memory_limit=limits.get("mem_mb", 1024),
            allowed_imports=spec_obj.allowed_imports,
        )
        if result.get("status") != "ok":
            raise BoundedExecutionError(
                f"Metamorphic transform '{transform_name}' failed: {result}"
            )
        transformed_metrics = result["value"]
        if not isinstance(transformed_metrics, Mapping):
            raise BoundedExecutionError(
                "Metamorphic execution must return a mapping of metrics"
            )
        metric_key = property_spec.get("metric")
        if metric_key is not None and not isinstance(metric_key, str):
            metric_key = None
        prop_tolerance = float(property_spec.get("tolerance", tolerance))
        passed = _compare_metric(
            base_metrics,
            transformed_metrics,
            metric=metric_key,
            tolerance=prop_tolerance,
        )
        metadata[f"{name}_pass"] = bool(passed)
        ctx.add(
            f"metamorphic_{name}_result",
            {
                "transform": transform_name,
                "passed": bool(passed),
                "metrics": dict(transformed_metrics),
            },
        )
    return (claim_obj, spec_obj, base_metrics), metadata
