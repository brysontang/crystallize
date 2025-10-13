"""Pipeline steps composing the agentic harness."""

from __future__ import annotations

import ast
import builtins as py_builtins
import hashlib
import json
import multiprocessing as mp
import textwrap
import uuid
from dataclasses import asdict
from multiprocessing.connection import Connection
from typing import Any, Callable, Dict, Iterable, Mapping, MutableMapping, Optional, Tuple

from crystallize import FrozenContext, pipeline_step

from .schema import Claim, Spec

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
    "Exception": Exception,
    "ValueError": ValueError,
}

LLMCallable = Callable[[Claim, Any, FrozenContext], Any]


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
    allowed = tuple(set(allowed_imports))
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


def _ast_allowlisted(tree: ast.AST, allowed_imports: Iterable[str]) -> None:
    allowed = set(allowed_imports)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            module_names = {alias.name for alias in node.names}
            if isinstance(node, ast.ImportFrom) and node.module:
                module_names.add(node.module)
            for name in module_names:
                if not any(name == mod or name.startswith(f"{mod}.") for mod in allowed):
                    raise BoundedExecutionError(f"Import not allowed: {name}")
        if isinstance(node, (ast.Global, ast.Nonlocal, ast.With, ast.Try, ast.AsyncWith, ast.AsyncFor)):
            raise BoundedExecutionError(f"Forbidden syntax: {type(node).__name__}")
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in {"eval", "exec", "__import__", "open"}:
                raise BoundedExecutionError(f"Forbidden call: {node.func.id}")


def _capsule_worker(
    conn: Connection,
    code_str: str,
    func_name: str,
    payload: Any,
    time_limit: int,
    memory_limit: int,
    allowed_imports: Iterable[str],
) -> None:
    try:
        try:
            import resource

            soft = hard = memory_limit * 1024 * 1024
            resource.setrlimit(resource.RLIMIT_AS, (soft, hard))
            resource.setrlimit(resource.RLIMIT_CPU, (time_limit, time_limit))
        except Exception:
            pass
        safe_builtins = SAFE_BUILTINS.copy()
        safe_builtins["__import__"] = _build_import_guard(allowed_imports)
        namespace: Dict[str, Any] = {"__builtins__": safe_builtins}
        exec(code_str, namespace)
        func = namespace.get(func_name)
        if not callable(func):
            raise BoundedExecutionError(
                f"Entrypoint '{func_name}' missing or not callable"
            )
        result = func(payload)
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
            list(allowed_imports),
        ),
    )
    process.start()
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
    if not any(
        isinstance(node, ast.FunctionDef) and node.name == entrypoint
        for node in tree.body
    ):
        raise BoundedExecutionError(
            f"Generated code must define the entrypoint '{entrypoint}'"
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
