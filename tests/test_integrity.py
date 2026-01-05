"""Tests for integrity status computation."""

from crystallize.integrity import (
    IntegrityStatus,
    compute_integrity,
    format_integrity_header,
)
from crystallize.protocol import HiddenVariable, HiddenVariablesReport


class TestComputeIntegrity:
    """Tests for compute_integrity()."""

    def test_valid_when_all_conditions_met(self):
        """Returns VALID when all conditions are met."""
        status, flags = compute_integrity(
            prereg_exists=True,
            replicates_fresh=True,
            hidden_vars=HiddenVariablesReport(items=[], audit_evidence_level="calls"),
            audit_sufficient=True,
            fn_changed=False,
        )

        assert status == IntegrityStatus.VALID
        assert not flags or flags == []

    def test_no_prereg(self):
        """Returns NO_PREREG when prereg is missing."""
        status, flags = compute_integrity(
            prereg_exists=False,
            replicates_fresh=True,
            hidden_vars=None,
            audit_sufficient=True,
            fn_changed=False,
        )

        assert status == IntegrityStatus.NO_PREREG
        assert "NO_PREREG" in flags

    def test_reused_data(self):
        """Returns REUSED_DATA when replicates not fresh."""
        status, flags = compute_integrity(
            prereg_exists=True,
            replicates_fresh=False,
            hidden_vars=None,
            audit_sufficient=True,
            fn_changed=False,
        )

        assert status == IntegrityStatus.REUSED_DATA
        assert "REUSED_DATA" in flags

    def test_reused_data_with_override(self):
        """REUSED_DATA can be overridden with allow_reuse."""
        status, flags = compute_integrity(
            prereg_exists=True,
            replicates_fresh=False,
            hidden_vars=None,
            audit_sufficient=True,
            fn_changed=False,
            overrides=["allow_reuse"],
        )

        assert status == IntegrityStatus.VALID
        assert "REUSED_DATA" not in flags

    def test_confounded_with_high_risk(self):
        """Returns CONFOUNDED when high risk hidden vars present."""
        hidden_vars = HiddenVariablesReport(
            items=[
                HiddenVariable(
                    field="temperature",
                    value=0.7,
                    source="hardcoded",
                    risk="HIGH",
                    why="temperature affects model behavior",
                    seen_in=["config_a"],
                )
            ],
            audit_evidence_level="calls",
        )

        status, flags = compute_integrity(
            prereg_exists=True,
            replicates_fresh=True,
            hidden_vars=hidden_vars,
            audit_sufficient=True,
            fn_changed=False,
        )

        assert status == IntegrityStatus.CONFOUNDED
        assert "CONFOUNDED" in flags

    def test_confounded_with_override(self):
        """CONFOUNDED can be overridden with allow_confounds."""
        hidden_vars = HiddenVariablesReport(
            items=[
                HiddenVariable(
                    field="temperature",
                    value=0.7,
                    source="hardcoded",
                    risk="HIGH",
                    why="temperature affects model behavior",
                    seen_in=["config_a"],
                )
            ],
            audit_evidence_level="calls",
        )

        status, flags = compute_integrity(
            prereg_exists=True,
            replicates_fresh=True,
            hidden_vars=hidden_vars,
            audit_sufficient=True,
            fn_changed=False,
            overrides=["allow_confounds"],
        )

        assert status == IntegrityStatus.VALID

    def test_no_audit(self):
        """Returns NO_AUDIT when audit is insufficient."""
        status, flags = compute_integrity(
            prereg_exists=True,
            replicates_fresh=True,
            hidden_vars=None,
            audit_sufficient=False,
            fn_changed=False,
        )

        assert status == IntegrityStatus.NO_AUDIT
        assert "NO_AUDIT" in flags

    def test_fn_changed(self):
        """Returns FN_CHANGED when function changed."""
        status, flags = compute_integrity(
            prereg_exists=True,
            replicates_fresh=True,
            hidden_vars=None,
            audit_sufficient=True,
            fn_changed=True,
        )

        assert status == IntegrityStatus.FN_CHANGED
        assert "FN_CHANGED" in flags

    def test_multiple_issues_returns_invalid(self):
        """Returns INVALID when multiple blocking issues present."""
        status, flags = compute_integrity(
            prereg_exists=False,
            replicates_fresh=False,
            hidden_vars=None,
            audit_sufficient=False,
            fn_changed=True,
        )

        assert status == IntegrityStatus.INVALID
        assert len([f for f in flags if f not in ("CONFOUNDED_MED", "LOW_N")]) > 1

    def test_low_sample_size_warning(self):
        """LOW_N flag added when sample size is small."""
        status, flags = compute_integrity(
            prereg_exists=True,
            replicates_fresh=True,
            hidden_vars=None,
            audit_sufficient=True,
            fn_changed=False,
            sample_size=5,
        )

        # LOW_N is a warning, doesn't change status
        assert status == IntegrityStatus.VALID
        assert "LOW_N" in flags


class TestFormatIntegrityHeader:
    """Tests for format_integrity_header()."""

    def test_valid_status(self):
        """VALID status has checkmark."""
        header = format_integrity_header(IntegrityStatus.VALID, [])
        assert "✓" in header
        assert "VALID" in header

    def test_invalid_status(self):
        """INVALID status has X mark."""
        header = format_integrity_header(
            IntegrityStatus.INVALID, ["NO_PREREG", "NO_AUDIT"]
        )
        assert "✗" in header
        assert "INVALID" in header
        assert "Flags:" in header

    def test_flags_included(self):
        """Flags are listed in header."""
        header = format_integrity_header(IntegrityStatus.CONFOUNDED, ["CONFOUNDED"])
        assert "CONFOUNDED" in header
