"""Domain objects that flow through the agentic harness pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass(frozen=True)
class Claim:
    """Statement describing the desired improvement or behaviour to verify."""

    id: str
    text: str
    acceptance: Dict[str, Any]


@dataclass(frozen=True)
class Spec:
    """Execution constraints generated before synthesis begins."""

    allowed_imports: List[str] = field(default_factory=list)
    properties: List[Dict[str, Any]] = field(default_factory=list)
    contracts: List[str] = field(default_factory=list)
    resources: Dict[str, int] = field(
        default_factory=lambda: {"time_s": 10, "mem_mb": 1024}
    )
