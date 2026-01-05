"""Protocol tracking for Crystallize.

Captures and analyzes HTTP call provenance to detect hidden variables.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Set

# Sensitive fields that affect model behavior (hardcoded for a2, configurable in a3)
SENSITIVE_FIELDS: Set[str] = {
    "system",
    "temperature",
    "top_p",
    "max_tokens",
    "num_predict",
    "endpoint",
    "path",
    "model",
    "seed",
    "stop",
    "presence_penalty",
    "frequency_penalty",
}


@dataclass
class ProtocolEvent:
    """A single HTTP call with field provenance tracking.

    Attributes
    ----------
    type : str
        Event type (always "http_call" for now)
    ts : str
        ISO timestamp
    config_name : str
        Name of the config that triggered this call
    config_fingerprint : str
        Fingerprint of the config
    method : str
        HTTP method (GET, POST, etc.)
    url : dict
        URL components {host, path, full}
    fields : dict
        Field provenance {field_name: {value, source}}
        Source is one of: "config.<key>", "hardcoded", "implicit_default", "unknown"
    """

    type: str
    ts: str
    config_name: str
    config_fingerprint: str
    method: str
    url: Dict[str, str]
    fields: Dict[str, Dict[str, Any]]

    @classmethod
    def create(
        cls,
        config_name: str,
        config_fingerprint: str,
        method: str,
        url: str,
        fields: Dict[str, Dict[str, Any]],
    ) -> "ProtocolEvent":
        """Create a new protocol event with current timestamp."""
        from urllib.parse import urlparse

        parsed = urlparse(url)
        return cls(
            type="http_call",
            ts=datetime.utcnow().isoformat() + "Z",
            config_name=config_name,
            config_fingerprint=config_fingerprint,
            method=method.upper(),
            url={"host": parsed.netloc, "path": parsed.path, "full": url},
            fields=fields,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "type": self.type,
            "ts": self.ts,
            "config_name": self.config_name,
            "config_fingerprint": self.config_fingerprint,
            "method": self.method,
            "url": self.url,
            "fields": self.fields,
        }


@dataclass
class ProtocolSummary:
    """Summary of protocol events for a config.

    Attributes
    ----------
    config_name : str
        Config name
    api_calls : list
        List of API call summaries
    audit_evidence : dict
        Audit level info {level, instrumented_call_count}
    """

    config_name: str
    api_calls: List[Dict[str, Any]] = field(default_factory=list)
    audit_evidence: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_events(cls, config_name: str, events: List[ProtocolEvent]) -> "ProtocolSummary":
        """Create summary from a list of events."""
        api_calls = []
        for event in events:
            api_calls.append(
                {
                    "method": event.method,
                    "host": event.url.get("host"),
                    "path": event.url.get("path"),
                    "fields": event.fields,
                }
            )

        return cls(
            config_name=config_name,
            api_calls=api_calls,
            audit_evidence={
                "level": "calls" if events else "none",
                "instrumented_call_count": len(events),
            },
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "config_name": self.config_name,
            "api_calls": self.api_calls,
            "audit_evidence": self.audit_evidence,
        }


@dataclass
class HiddenVariable:
    """A detected hidden variable (parameter not controlled by config).

    Attributes
    ----------
    field : str
        Field name
    value : Any
        Observed value
    source : str
        Where it came from: "implicit_default", "hardcoded", "unknown"
    risk : str
        Risk level: "HIGH", "MED", "LOW"
    why : str
        Explanation of why this is a hidden variable
    seen_in : list
        Config names where this was observed
    """

    field: str
    value: Any
    source: str
    risk: str
    why: str
    seen_in: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "field": self.field,
            "value": self.value,
            "source": self.source,
            "risk": self.risk,
            "why": self.why,
            "seen_in": self.seen_in,
        }


def classify_risk(field_name: str, source: str) -> str:
    """Classify risk level for a hidden variable.

    Parameters
    ----------
    field_name : str
        Name of the field
    source : str
        Source classification

    Returns
    -------
    str
        Risk level: "HIGH", "MED", or "LOW"
    """
    is_sensitive = field_name.lower() in SENSITIVE_FIELDS

    if source in ("implicit_default", "unknown"):
        return "HIGH" if is_sensitive else "MED"
    elif source == "hardcoded":
        return "MED" if is_sensitive else "LOW"
    return "LOW"


def generate_why(field_name: str, source: str, value: Any) -> str:
    """Generate explanation for why this is a hidden variable.

    Parameters
    ----------
    field_name : str
        Name of the field
    source : str
        Source classification
    value : Any
        The value

    Returns
    -------
    str
        Human-readable explanation
    """
    is_sensitive = field_name.lower() in SENSITIVE_FIELDS
    sensitive_note = " (affects model behavior)" if is_sensitive else ""

    if source == "implicit_default":
        return f"'{field_name}'{sensitive_note} was not set; API will use default"
    elif source == "hardcoded":
        return f"'{field_name}'{sensitive_note} is hardcoded to {value!r}"
    elif source == "unknown":
        return f"'{field_name}'{sensitive_note} value {value!r} has unknown origin"
    return f"'{field_name}' set to {value!r}"


@dataclass
class HiddenVariablesReport:
    """Report of all hidden variables detected in an experiment.

    Attributes
    ----------
    items : list
        List of HiddenVariable instances
    audit_evidence_level : str
        Overall audit level
    instrumented_call_count : int
        Total number of instrumented calls
    """

    items: List[HiddenVariable] = field(default_factory=list)
    audit_evidence_level: str = "none"
    instrumented_call_count: int = 0

    @classmethod
    def from_protocol_summaries(
        cls, summaries: Dict[str, ProtocolSummary]
    ) -> "HiddenVariablesReport":
        """Build report from protocol summaries across configs."""
        # Aggregate all field observations
        field_observations: Dict[str, Dict[str, Any]] = {}  # field -> {values, sources, seen_in}

        total_calls = 0
        has_audit = False

        for config_name, summary in summaries.items():
            total_calls += summary.audit_evidence.get("instrumented_call_count", 0)
            if summary.audit_evidence.get("level") == "calls":
                has_audit = True

            for call in summary.api_calls:
                for field_name, field_info in call.get("fields", {}).items():
                    source = field_info.get("source", "unknown")
                    value = field_info.get("value")

                    # Skip fields that come from config
                    if source.startswith("config."):
                        continue

                    if field_name not in field_observations:
                        field_observations[field_name] = {
                            "values": set(),
                            "sources": set(),
                            "seen_in": set(),
                        }

                    # Handle unhashable values
                    try:
                        field_observations[field_name]["values"].add(value)
                    except TypeError:
                        field_observations[field_name]["values"].add(str(value))

                    field_observations[field_name]["sources"].add(source)
                    field_observations[field_name]["seen_in"].add(config_name)

        # Build hidden variable items
        items = []
        for field_name, obs in field_observations.items():
            # Take first source (they should be consistent)
            source = next(iter(obs["sources"]))
            value = next(iter(obs["values"]))
            risk = classify_risk(field_name, source)
            why = generate_why(field_name, source, value)

            items.append(
                HiddenVariable(
                    field=field_name,
                    value=value,
                    source=source,
                    risk=risk,
                    why=why,
                    seen_in=sorted(obs["seen_in"]),
                )
            )

        # Sort by risk (HIGH first)
        risk_order = {"HIGH": 0, "MED": 1, "LOW": 2}
        items.sort(key=lambda x: (risk_order.get(x.risk, 3), x.field))

        return cls(
            items=items,
            audit_evidence_level="calls" if has_audit else "none",
            instrumented_call_count=total_calls,
        )

    def has_high_risk(self) -> bool:
        """Check if there are any HIGH risk hidden variables."""
        return any(item.risk == "HIGH" for item in self.items)

    def pretty(self) -> str:
        """Generate pretty-printed report."""
        if not self.items:
            return "No hidden variables detected."

        lines = ["Hidden Variables Report", "=" * 40]

        for item in self.items:
            risk_emoji = {"HIGH": "🔴", "MED": "🟡", "LOW": "🟢"}.get(item.risk, "⚪")
            lines.append(f"\n{risk_emoji} [{item.risk}] {item.field}")
            lines.append(f"   Value: {item.value!r}")
            lines.append(f"   Source: {item.source}")
            lines.append(f"   Why: {item.why}")
            lines.append(f"   Seen in: {', '.join(item.seen_in)}")

        lines.append(f"\nAudit level: {self.audit_evidence_level}")
        lines.append(f"Instrumented calls: {self.instrumented_call_count}")

        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "items": [item.to_dict() for item in self.items],
            "audit_evidence_level": self.audit_evidence_level,
            "instrumented_call_count": self.instrumented_call_count,
        }


@dataclass
class ConfigPairDiff:
    """Diff between two configs."""

    config_a: str
    config_b: str
    declared_diffs: Dict[str, tuple]  # {field: (value_a, value_b)}
    observed_diffs: Dict[str, tuple]  # {field: (value_a, value_b)}
    confounds: List[str]  # Fields that differ but weren't declared

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "config_a": self.config_a,
            "config_b": self.config_b,
            "declared_diffs": {k: list(v) for k, v in self.declared_diffs.items()},
            "observed_diffs": {k: list(v) for k, v in self.observed_diffs.items()},
            "confounds": self.confounds,
        }


@dataclass
class ProtocolDiff:
    """Analysis of protocol differences between configs.

    Attributes
    ----------
    pairs : list
        List of ConfigPairDiff instances
    """

    pairs: List[ConfigPairDiff] = field(default_factory=list)

    @classmethod
    def from_configs_and_summaries(
        cls,
        configs: Dict[str, Dict[str, Any]],
        summaries: Dict[str, ProtocolSummary],
    ) -> "ProtocolDiff":
        """Build diff from configs and their protocol summaries."""
        config_names = sorted(configs.keys())
        pairs = []

        # Compare each pair of configs
        for i, name_a in enumerate(config_names):
            for name_b in config_names[i + 1 :]:
                # Declared diffs (from config dictionaries)
                declared = {}
                all_keys = set(configs[name_a].keys()) | set(configs[name_b].keys())
                for key in all_keys:
                    val_a = configs[name_a].get(key)
                    val_b = configs[name_b].get(key)
                    if val_a != val_b:
                        declared[key] = (val_a, val_b)

                # Observed diffs (from protocol summaries)
                observed = {}
                summary_a = summaries.get(name_a)
                summary_b = summaries.get(name_b)

                if summary_a and summary_b:
                    # Extract all observed fields from calls
                    fields_a = _extract_fields(summary_a)
                    fields_b = _extract_fields(summary_b)
                    all_observed = set(fields_a.keys()) | set(fields_b.keys())

                    for fld in all_observed:
                        val_a = fields_a.get(fld, {}).get("value")
                        val_b = fields_b.get(fld, {}).get("value")
                        if val_a != val_b:
                            observed[fld] = (val_a, val_b)

                # Confounds: observed diffs that weren't declared
                confounds = [k for k in observed if k not in declared]

                pairs.append(
                    ConfigPairDiff(
                        config_a=name_a,
                        config_b=name_b,
                        declared_diffs=declared,
                        observed_diffs=observed,
                        confounds=confounds,
                    )
                )

        return cls(pairs=pairs)

    def has_confounds(self) -> bool:
        """Check if any pair has confounds."""
        return any(pair.confounds for pair in self.pairs)

    def pretty(self) -> str:
        """Generate pretty-printed diff report."""
        if not self.pairs:
            return "No config pairs to compare."

        lines = ["Protocol Diff Report", "=" * 40]

        for pair in self.pairs:
            lines.append(f"\n{pair.config_a} vs {pair.config_b}")
            lines.append("-" * 30)

            if pair.declared_diffs:
                lines.append("Declared differences (in config):")
                for field, (val_a, val_b) in pair.declared_diffs.items():
                    lines.append(f"  {field}: {val_a!r} → {val_b!r}")

            if pair.observed_diffs:
                lines.append("Observed differences (in API calls):")
                for field, (val_a, val_b) in pair.observed_diffs.items():
                    marker = " ⚠️" if field in pair.confounds else ""
                    lines.append(f"  {field}: {val_a!r} → {val_b!r}{marker}")

            if pair.confounds:
                lines.append(f"⚠️ CONFOUNDS: {', '.join(pair.confounds)}")
                lines.append("   (These differ between configs but weren't declared)")

            if not pair.declared_diffs and not pair.observed_diffs:
                lines.append("  No differences detected")

        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {"pairs": [pair.to_dict() for pair in self.pairs]}


def _extract_fields(summary: ProtocolSummary) -> Dict[str, Dict[str, Any]]:
    """Extract all fields from a protocol summary, taking last seen value."""
    fields: Dict[str, Dict[str, Any]] = {}
    for call in summary.api_calls:
        for field_name, field_info in call.get("fields", {}).items():
            fields[field_name] = field_info
    return fields


def determine_provenance(
    field_name: str,
    value: Any,
    config: Dict[str, Any],
    present_in_request: bool = True,
) -> str:
    """Determine the provenance (source) of a field value.

    Parameters
    ----------
    field_name : str
        Name of the field
    value : Any
        The value in the request
    config : dict
        The experiment config
    present_in_request : bool
        Whether the field was present in the request

    Returns
    -------
    str
        Source: "config.<key>", "hardcoded", "implicit_default", or "unknown"
    """
    if not present_in_request:
        # Field not in request - check if it's sensitive
        if field_name.lower() in SENSITIVE_FIELDS:
            return "implicit_default"
        return "implicit_default"

    # Check if value matches any config key
    for key, config_val in config.items():
        if value == config_val:
            return f"config.{key}"

    # Value present but not from config
    return "hardcoded"
