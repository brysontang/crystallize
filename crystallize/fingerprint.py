"""Function fingerprinting for Crystallize.

Creates deterministic fingerprints of functions to detect changes between runs.
"""

from __future__ import annotations

import hashlib
import inspect
from typing import Any, Callable, Dict, Optional


def fn_fingerprint(fn: Callable[..., Any]) -> Dict[str, Any]:
    """Create a fingerprint of a function for change detection.

    Tries to get source code first, falls back to bytecode if unavailable.

    Parameters
    ----------
    fn : Callable
        The function to fingerprint

    Returns
    -------
    dict
        Fingerprint with keys:
        - method: "source" or "bytecode"
        - sha256: hash of the source/bytecode
        - source_span: tuple (start_line, end_line) if source available
        - file: source file path if available
    """
    result: Dict[str, Any] = {
        "name": getattr(fn, "__name__", "<unknown>"),
        "module": getattr(fn, "__module__", "<unknown>"),
    }

    # Try source code first
    source_info = _get_source_fingerprint(fn)
    if source_info:
        result.update(source_info)
        result["method"] = "source"
        return result

    # Fall back to bytecode
    bytecode_info = _get_bytecode_fingerprint(fn)
    if bytecode_info:
        result.update(bytecode_info)
        result["method"] = "bytecode"
        return result

    # Last resort - use repr
    result["method"] = "repr"
    result["sha256"] = hashlib.sha256(repr(fn).encode()).hexdigest()
    return result


def _get_source_fingerprint(fn: Callable[..., Any]) -> Optional[Dict[str, Any]]:
    """Try to get source-based fingerprint."""
    try:
        source_lines, start_line = inspect.getsourcelines(fn)
        source = "".join(source_lines)
        source_file = inspect.getfile(fn)

        return {
            "sha256": hashlib.sha256(source.encode()).hexdigest(),
            "source_span": (start_line, start_line + len(source_lines) - 1),
            "file": source_file,
        }
    except (OSError, TypeError):
        return None


def _get_bytecode_fingerprint(fn: Callable[..., Any]) -> Optional[Dict[str, Any]]:
    """Try to get bytecode-based fingerprint."""
    try:
        code = getattr(fn, "__code__", None)
        if code is None:
            return None

        # Hash the bytecode
        bytecode = code.co_code
        return {
            "sha256": hashlib.sha256(bytecode).hexdigest(),
        }
    except (AttributeError, TypeError):
        return None


def fingerprints_match(fp1: Dict[str, Any], fp2: Dict[str, Any]) -> bool:
    """Check if two fingerprints represent the same function.

    Parameters
    ----------
    fp1, fp2 : dict
        Fingerprints from fn_fingerprint()

    Returns
    -------
    bool
        True if fingerprints match (same sha256)
    """
    return fp1.get("sha256") == fp2.get("sha256")
