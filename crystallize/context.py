"""Execution context for Crystallize experiments.

Provides ctx.record() for metrics and ctx.http for instrumented HTTP calls.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union

from .http import InstrumentedHTTP, NoAuditHTTP


@dataclass
class Context:
    """Execution context for recording metrics and making audited HTTP calls.

    Attributes
    ----------
    replicate : int
        Current replicate index (0-based within this run)
    config_name : str
        Name of the current config
    config_fingerprint : str, optional
        Fingerprint of the current config
    seed : int, optional
        Random seed for this replicate
    replicate_id : str, optional
        Global replicate ID (from ledger)

    Example
    -------
    >>> def my_experiment(config, ctx):
    ...     # Record metrics
    ...     ctx.record("accuracy", 0.95)
    ...     ctx.record("latency", 120, tags={"unit": "ms"})
    ...
    ...     # Make audited HTTP calls
    ...     response = ctx.http.post(
    ...         "https://api.example.com/chat",
    ...         json={"model": config["model"], "prompt": "Hello"}
    ...     )
    ...     return response.json()
    """

    replicate: int
    config_name: str
    config_fingerprint: str = ""  # Optional for backwards compat
    seed: Optional[int] = None
    replicate_id: Optional[str] = None

    # Internal storage
    _metrics: Dict[str, List[Any]] = field(default_factory=dict)
    _tags: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)
    _http: Optional[Union[InstrumentedHTTP, NoAuditHTTP]] = field(
        default=None, repr=False
    )

    def record(
        self,
        name: str,
        value: Any,
        tags: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record a metric value.

        Parameters
        ----------
        name : str
            Metric name (e.g., "accuracy", "win_rate", "latency")
        value : Any
            The value to record (typically numeric)
        tags : dict, optional
            Additional metadata for this measurement
        """
        if name not in self._metrics:
            self._metrics[name] = []
            self._tags[name] = []
        self._metrics[name].append(value)
        self._tags[name].append(tags or {})

    @property
    def metrics(self) -> Dict[str, List[Any]]:
        """Access recorded metrics (copy)."""
        return self._metrics.copy()

    @property
    def http(self) -> Union[InstrumentedHTTP, NoAuditHTTP]:
        """Access the instrumented HTTP client.

        Use this for making HTTP calls with provenance tracking.

        Raises
        ------
        RuntimeError
            If http was not configured (audit='none')
        """
        if self._http is None:
            raise RuntimeError(
                "ctx.http is not available. This typically means the experiment "
                "was run with audit='none'. Use audit='calls' to enable HTTP tracking."
            )
        return self._http

    def _get_protocol_events(self) -> List[Any]:
        """Get protocol events from the HTTP client (internal)."""
        if isinstance(self._http, InstrumentedHTTP):
            return self._http.events
        return []


def create_context(
    replicate: int,
    config_name: str,
    config_fingerprint: str,
    config: Dict[str, Any],
    seed: Optional[int] = None,
    replicate_id: Optional[str] = None,
    audit: str = "calls",
) -> Context:
    """Create a new context for a replicate.

    Parameters
    ----------
    replicate : int
        Replicate index
    config_name : str
        Name of the config
    config_fingerprint : str
        Fingerprint of the config
    config : dict
        The config dictionary (for HTTP provenance checking)
    seed : int, optional
        Random seed
    replicate_id : str, optional
        Global replicate ID
    audit : str
        Audit level: "calls" or "none"

    Returns
    -------
    Context
        New context instance
    """
    ctx = Context(
        replicate=replicate,
        config_name=config_name,
        config_fingerprint=config_fingerprint,
        seed=seed,
        replicate_id=replicate_id,
    )

    # Set up HTTP client based on audit level
    if audit == "calls":
        ctx._http = InstrumentedHTTP(
            config=config,
            config_name=config_name,
            config_fingerprint=config_fingerprint,
        )
    else:
        ctx._http = NoAuditHTTP()

    return ctx
