"""Integrity status computation for Crystallize.

Determines the integrity status of a confirm run based on various factors.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Tuple

from .protocol import HiddenVariablesReport


class IntegrityStatus(str, Enum):
    """Integrity status levels for confirm runs.

    VALID: All conditions met for a valid experiment
    CONFOUNDED: Hidden variables detected that could affect results
    REUSED_DATA: Replicates were not fresh (data was reused)
    NO_PREREG: Pre-registration artifact is missing
    NO_AUDIT: No audit trail (ctx.http not used)
    FN_CHANGED: Function changed between explore and confirm
    INVALID: Multiple issues or unrecoverable problem
    """

    VALID = "VALID"
    CONFOUNDED = "CONFOUNDED"
    REUSED_DATA = "REUSED_DATA"
    NO_PREREG = "NO_PREREG"
    NO_AUDIT = "NO_AUDIT"
    FN_CHANGED = "FN_CHANGED"
    INVALID = "INVALID"


@dataclass
class IntegrityFlag:
    """A single integrity issue."""

    code: str
    message: str
    severity: str  # "blocking", "warning"
    overridable: bool
    override_param: Optional[str] = None


# Flag definitions
FLAGS = {
    "no_prereg": IntegrityFlag(
        code="NO_PREREG",
        message="Pre-registration artifact is missing",
        severity="blocking",
        overridable=False,
    ),
    "reused_data": IntegrityFlag(
        code="REUSED_DATA",
        message="Replicates were not fresh (data reused from previous runs)",
        severity="blocking",
        overridable=True,
        override_param="allow_reuse",
    ),
    "high_risk_hidden_vars": IntegrityFlag(
        code="CONFOUNDED",
        message="HIGH risk hidden variables detected",
        severity="blocking",
        overridable=True,
        override_param="allow_confounds",
    ),
    "med_risk_hidden_vars": IntegrityFlag(
        code="CONFOUNDED_MED",
        message="MEDIUM risk hidden variables detected",
        severity="warning",
        overridable=True,
        override_param="allow_confounds",
    ),
    "no_audit": IntegrityFlag(
        code="NO_AUDIT",
        message="No audit trail (ctx.http not used)",
        severity="blocking",
        overridable=True,
        override_param="allow_no_audit",
    ),
    "fn_changed": IntegrityFlag(
        code="FN_CHANGED",
        message="Function changed between explore and confirm runs",
        severity="blocking",
        overridable=True,
        override_param="allow_fn_change",
    ),
    "low_sample_size": IntegrityFlag(
        code="LOW_N",
        message="Sample size may be too small for reliable results",
        severity="warning",
        overridable=False,
    ),
}


def compute_integrity(
    prereg_exists: bool,
    replicates_fresh: bool,
    hidden_vars: Optional[HiddenVariablesReport],
    audit_sufficient: bool,
    fn_changed: bool,
    overrides: Optional[List[str]] = None,
    sample_size: int = 0,
) -> Tuple[IntegrityStatus, List[str]]:
    """Compute integrity status and flags.

    Parameters
    ----------
    prereg_exists : bool
        Whether pre-registration artifact was written
    replicates_fresh : bool
        Whether all replicates used fresh indices
    hidden_vars : HiddenVariablesReport, optional
        Report of hidden variables
    audit_sufficient : bool
        Whether audit trail is sufficient (ctx.http used)
    fn_changed : bool
        Whether function changed between explore and confirm
    overrides : list, optional
        List of allow_* flags that were set
    sample_size : int
        Total sample size

    Returns
    -------
    tuple
        (IntegrityStatus, list of flag codes)
    """
    overrides = overrides or []
    flags: List[str] = []

    # Check each condition
    if not prereg_exists:
        flags.append("NO_PREREG")

    if not replicates_fresh and "allow_reuse" not in overrides:
        flags.append("REUSED_DATA")

    if hidden_vars:
        if hidden_vars.has_high_risk() and "allow_confounds" not in overrides:
            flags.append("CONFOUNDED")
        elif any(item.risk == "MED" for item in hidden_vars.items):
            flags.append("CONFOUNDED_MED")

    if not audit_sufficient and "allow_no_audit" not in overrides:
        flags.append("NO_AUDIT")

    if fn_changed and "allow_fn_change" not in overrides:
        flags.append("FN_CHANGED")

    if sample_size > 0 and sample_size < 10:
        flags.append("LOW_N")

    # Determine overall status
    if not flags or (flags == ["CONFOUNDED_MED"]) or (flags == ["LOW_N"]):
        return (IntegrityStatus.VALID, flags)

    # Check for specific single-issue statuses
    blocking_flags = [f for f in flags if f not in ("CONFOUNDED_MED", "LOW_N")]

    if len(blocking_flags) == 1:
        if blocking_flags[0] == "NO_PREREG":
            return (IntegrityStatus.NO_PREREG, flags)
        elif blocking_flags[0] == "REUSED_DATA":
            return (IntegrityStatus.REUSED_DATA, flags)
        elif blocking_flags[0] == "CONFOUNDED":
            return (IntegrityStatus.CONFOUNDED, flags)
        elif blocking_flags[0] == "NO_AUDIT":
            return (IntegrityStatus.NO_AUDIT, flags)
        elif blocking_flags[0] == "FN_CHANGED":
            return (IntegrityStatus.FN_CHANGED, flags)

    # Multiple blocking issues
    return (IntegrityStatus.INVALID, flags)


def get_flag_info(code: str) -> Optional[IntegrityFlag]:
    """Get flag info by code.

    Parameters
    ----------
    code : str
        Flag code (e.g., "NO_PREREG", "CONFOUNDED")

    Returns
    -------
    IntegrityFlag or None
        Flag info if found
    """
    code_to_key = {
        "NO_PREREG": "no_prereg",
        "REUSED_DATA": "reused_data",
        "CONFOUNDED": "high_risk_hidden_vars",
        "CONFOUNDED_MED": "med_risk_hidden_vars",
        "NO_AUDIT": "no_audit",
        "FN_CHANGED": "fn_changed",
        "LOW_N": "low_sample_size",
    }
    key = code_to_key.get(code)
    return FLAGS.get(key) if key else None


def format_integrity_header(status: IntegrityStatus, flags: List[str]) -> str:
    """Format integrity status as a header for reports.

    Parameters
    ----------
    status : IntegrityStatus
        Overall status
    flags : list
        List of flag codes

    Returns
    -------
    str
        Formatted header
    """
    status_emoji = {
        IntegrityStatus.VALID: "✓",
        IntegrityStatus.CONFOUNDED: "⚠️",
        IntegrityStatus.REUSED_DATA: "⚠️",
        IntegrityStatus.NO_PREREG: "✗",
        IntegrityStatus.NO_AUDIT: "⚠️",
        IntegrityStatus.FN_CHANGED: "⚠️",
        IntegrityStatus.INVALID: "✗",
    }

    lines = [
        f"{status_emoji.get(status, '?')} Integrity: {status.value}",
    ]

    if flags:
        lines.append("Flags:")
        for code in flags:
            flag_info = get_flag_info(code)
            if flag_info:
                lines.append(f"  - {code}: {flag_info.message}")
            else:
                lines.append(f"  - {code}")

    return "\n".join(lines)


def check_blocking_conditions(
    hidden_vars: Optional[HiddenVariablesReport],
    audit_level: str,
    fn_fingerprint_match: bool,
    allow_confounds: bool = False,
    allow_no_audit: bool = False,
    allow_fn_change: bool = False,
) -> Optional[str]:
    """Check if there are any blocking conditions that prevent crystallize().

    Parameters
    ----------
    hidden_vars : HiddenVariablesReport, optional
        Hidden variables report
    audit_level : str
        Audit level ("calls" or "none")
    fn_fingerprint_match : bool
        Whether function fingerprint matches
    allow_confounds : bool
        Whether to allow confounds
    allow_no_audit : bool
        Whether to allow no audit
    allow_fn_change : bool
        Whether to allow function change

    Returns
    -------
    str or None
        Error message if blocked, None if OK to proceed
    """
    messages = []

    if hidden_vars and hidden_vars.has_high_risk() and not allow_confounds:
        high_risk_items = [item for item in hidden_vars.items if item.risk == "HIGH"]
        fields = ", ".join(item.field for item in high_risk_items)
        messages.append(
            f"HIGH risk hidden variables detected: {fields}\n"
            f"Use allow_confounds=True to proceed (result will be CONFOUNDED)"
        )

    if audit_level == "none" and not allow_no_audit:
        messages.append(
            "No audit trail (ctx.http not used)\n"
            "Use allow_no_audit=True to proceed (result will be NO_AUDIT)"
        )

    if not fn_fingerprint_match and not allow_fn_change:
        messages.append(
            "Function changed between explore and confirm runs\n"
            "Use allow_fn_change=True to proceed (result will be FN_CHANGED)"
        )

    if messages:
        return "\n\n".join(messages)
    return None
