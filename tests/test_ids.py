"""Tests for ID generation."""

from crystallize.ids import (
    generate_run_id,
    generate_lineage_id,
    config_fingerprint,
    replicate_id,
    manifest_hash,
)


class TestGenerateRunId:
    """Tests for generate_run_id()."""

    def test_explore_prefix(self):
        """Explore run IDs start with 'exp_'."""
        run_id = generate_run_id("explore")
        assert run_id.startswith("exp_")

    def test_confirm_prefix(self):
        """Confirm run IDs start with 'conf_'."""
        run_id = generate_run_id("confirm")
        assert run_id.startswith("conf_")

    def test_unique(self):
        """Generated IDs are unique."""
        ids = [generate_run_id("explore") for _ in range(100)]
        assert len(set(ids)) == 100


class TestGenerateLineageId:
    """Tests for generate_lineage_id()."""

    def test_prefix(self):
        """Lineage IDs start with 'lin_'."""
        lineage_id = generate_lineage_id()
        assert lineage_id.startswith("lin_")

    def test_unique(self):
        """Generated IDs are unique."""
        ids = [generate_lineage_id() for _ in range(100)]
        assert len(set(ids)) == 100


class TestConfigFingerprint:
    """Tests for config_fingerprint()."""

    def test_deterministic(self):
        """Same config produces same fingerprint."""
        config = {"model": "gpt-4", "temperature": 0.7}
        fp1 = config_fingerprint(config)
        fp2 = config_fingerprint(config)
        assert fp1 == fp2

    def test_different_configs_different_fingerprints(self):
        """Different configs produce different fingerprints."""
        fp1 = config_fingerprint({"model": "gpt-4"})
        fp2 = config_fingerprint({"model": "claude"})
        assert fp1 != fp2

    def test_order_independent(self):
        """Key order doesn't affect fingerprint."""
        fp1 = config_fingerprint({"a": 1, "b": 2})
        fp2 = config_fingerprint({"b": 2, "a": 1})
        assert fp1 == fp2


class TestReplicateId:
    """Tests for replicate_id()."""

    def test_format(self):
        """Replicate ID has expected format."""
        rep_id = replicate_id("lin_abc123", "cfg_def456", 42)
        assert "lin_abc123" in rep_id
        assert "cfg_def4" in rep_id  # First 8 chars
        assert "0042" in rep_id

    def test_deterministic(self):
        """Same inputs produce same replicate ID."""
        rep_id1 = replicate_id("lin_abc", "cfg_xyz", 5)
        rep_id2 = replicate_id("lin_abc", "cfg_xyz", 5)
        assert rep_id1 == rep_id2


class TestManifestHash:
    """Tests for manifest_hash()."""

    def test_deterministic(self):
        """Same manifest produces same hash."""
        manifest = {"run_id": "test", "results": [1, 2, 3]}
        hash1 = manifest_hash(manifest)
        hash2 = manifest_hash(manifest)
        assert hash1 == hash2

    def test_different_manifests_different_hashes(self):
        """Different manifests produce different hashes."""
        hash1 = manifest_hash({"run_id": "test1"})
        hash2 = manifest_hash({"run_id": "test2"})
        assert hash1 != hash2
