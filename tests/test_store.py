"""Tests for the filesystem store."""

import tempfile
import os

from crystallize.store import Store


class TestStore:
    """Tests for Store class."""

    def test_creates_directory_structure(self):
        """Store creates the expected directory structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            _store = Store(tmpdir)  # noqa: F841

            assert os.path.exists(os.path.join(tmpdir, "runs"))
            assert os.path.exists(os.path.join(tmpdir, "prereg"))
            assert os.path.exists(os.path.join(tmpdir, "ledger"))

    def test_read_ledger_returns_zero_for_new(self):
        """read_ledger() returns 0 for new lineage/config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = Store(tmpdir)

            idx = store.read_ledger("lin_test", "cfg_test")
            assert idx == 0

    def test_update_and_read_ledger(self):
        """Ledger can be updated and read back."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = Store(tmpdir)

            store.update_ledger("lin_test", "cfg_test", 10)
            idx = store.read_ledger("lin_test", "cfg_test")
            assert idx == 10

            store.update_ledger("lin_test", "cfg_test", 20)
            idx = store.read_ledger("lin_test", "cfg_test")
            assert idx == 20

    def test_allocate_replicates(self):
        """allocate_replicates() returns correct range and updates ledger."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = Store(tmpdir)

            start, end = store.allocate_replicates("lin_test", "cfg_test", 5)
            assert start == 0
            assert end == 4

            start2, end2 = store.allocate_replicates("lin_test", "cfg_test", 3)
            assert start2 == 5
            assert end2 == 7

    def test_write_and_read_prereg(self):
        """Pre-registration can be written and read."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = Store(tmpdir)

            data = {"hypothesis": "a > b", "configs": ["a", "b"]}
            path = store.write_prereg("conf_test", data)

            assert os.path.exists(path)

            read_data = store.read_prereg("conf_test")
            assert read_data == data

    def test_write_and_read_run_manifest(self):
        """Run manifest can be written and read."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = Store(tmpdir)

            manifest = {
                "run_id": "exp_test",
                "results": {"a": [1, 2, 3]},
                "metrics": {"a": {"score": [0.9, 0.8, 0.7]}},
            }
            path = store.write_run_manifest("exp_test", manifest)

            assert os.path.exists(path)

            read_manifest = store.read_run_manifest("exp_test")
            assert read_manifest == manifest

    def test_read_missing_prereg_returns_none(self):
        """read_prereg() returns None for missing files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = Store(tmpdir)

            result = store.read_prereg("nonexistent")
            assert result is None

    def test_read_missing_manifest_returns_none(self):
        """read_run_manifest() returns None for missing files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = Store(tmpdir)

            result = store.read_run_manifest("nonexistent")
            assert result is None
