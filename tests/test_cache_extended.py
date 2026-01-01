"""Extended tests for cache module functions."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from crystallize.utils.cache import (
    _code_fingerprint,
    cache_path,
    compute_hash,
    load_cache,
    store_cache,
)


class TestCodeFingerprint:
    """Tests for _code_fingerprint function."""

    def test_fingerprint_regular_function(self):
        def my_function(x):
            return x + 1

        fp = _code_fingerprint(my_function)
        assert isinstance(fp, str)
        assert len(fp) == 64  # SHA256 hex

    def test_fingerprint_lambda(self):
        fp = _code_fingerprint(lambda x: x * 2)
        assert isinstance(fp, str)
        assert len(fp) == 64

    def test_fingerprint_different_functions_differ(self):
        def fn1(x):
            return x + 1

        def fn2(x):
            return x + 2

        fp1 = _code_fingerprint(fn1)
        fp2 = _code_fingerprint(fn2)
        assert fp1 != fp2

    def test_fingerprint_same_function_consistent(self):
        def fn1(x):
            return x * 10

        # Same function should have consistent hash
        fp1 = _code_fingerprint(fn1)
        fp2 = _code_fingerprint(fn1)
        assert fp1 == fp2

    def test_fingerprint_includes_function_name(self):
        # getsource includes the def line with function name, so two
        # identically-bodied functions with different names will differ
        def fn1(x):
            return x * 10

        def fn2(x):
            return x * 10

        fp1 = _code_fingerprint(fn1)
        fp2 = _code_fingerprint(fn2)
        # These will differ because function names are part of source
        assert fp1 != fp2

    def test_fingerprint_method(self):
        class MyClass:
            def method(self, x):
                return x

        obj = MyClass()
        fp = _code_fingerprint(obj.method)
        assert isinstance(fp, str)
        assert len(fp) == 64

    def test_fingerprint_builtin_uses_bytecode(self):
        # Built-in functions don't have source, fallback to bytecode
        # We use a class method that we define to simulate this
        # since actual builtins may vary
        def wrapper():
            pass

        # Patch getsource to raise OSError
        with patch(
            "crystallize.utils.cache.inspect.getsource", side_effect=OSError
        ):
            fp = _code_fingerprint(wrapper)
            assert isinstance(fp, str)
            assert len(fp) == 64


class TestComputeHash:
    """Tests for compute_hash function."""

    def test_hash_dict(self):
        obj = {"a": 1, "b": [2, 3]}
        h = compute_hash(obj)
        assert isinstance(h, str)
        assert len(h) == 64

    def test_hash_same_object_same_result(self):
        obj = {"key": "value", "list": [1, 2, 3]}
        h1 = compute_hash(obj)
        h2 = compute_hash(obj)
        assert h1 == h2

    def test_hash_different_objects_differ(self):
        h1 = compute_hash({"a": 1})
        h2 = compute_hash({"a": 2})
        assert h1 != h2

    def test_hash_list(self):
        h = compute_hash([1, 2, 3, "string", {"nested": True}])
        assert len(h) == 64

    def test_hash_primitives(self):
        assert len(compute_hash(42)) == 64
        assert len(compute_hash("string")) == 64
        assert len(compute_hash(3.14)) == 64
        assert len(compute_hash(True)) == 64
        assert len(compute_hash(None)) == 64


class TestCachePath:
    """Tests for cache_path function."""

    def test_cache_path_creates_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("crystallize.utils.cache.CACHE_DIR", Path(tmpdir) / "cache"):
                step_hash = "abc123"
                input_hash = "def456"
                path = cache_path(step_hash, input_hash)

                assert path.parent.exists()
                assert path.parent.name == step_hash
                assert path.name == f"{input_hash}.pkl"

    def test_cache_path_nested_structure(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("crystallize.utils.cache.CACHE_DIR", Path(tmpdir) / "cache"):
                path = cache_path("step_abc", "input_xyz")
                assert "step_abc" in str(path)
                assert "input_xyz.pkl" in str(path)

    def test_cache_path_with_long_hashes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("crystallize.utils.cache.CACHE_DIR", Path(tmpdir) / "cache"):
                long_step = "a" * 64
                long_input = "b" * 64
                path = cache_path(long_step, long_input)
                assert path.exists() is False  # Just path, not file
                assert path.parent.exists()


class TestLoadStoreCache:
    """Tests for load_cache and store_cache functions."""

    def test_store_and_load_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("crystallize.utils.cache.CACHE_DIR", Path(tmpdir) / "cache"):
                data = {"result": [1, 2, 3], "nested": {"key": "value"}}
                step_hash = "step123"
                input_hash = "input456"

                store_cache(step_hash, input_hash, data)
                loaded = load_cache(step_hash, input_hash)

                assert loaded == data

    def test_load_cache_missing_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("crystallize.utils.cache.CACHE_DIR", Path(tmpdir) / "cache"):
                with pytest.raises(FileNotFoundError):
                    load_cache("nonexistent", "also_nonexistent")

    def test_store_cache_creates_nested_dirs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("crystallize.utils.cache.CACHE_DIR", Path(tmpdir) / "deep" / "cache"):
                store_cache("new_step", "new_input", {"data": True})
                path = cache_path("new_step", "new_input")
                assert path.exists()

    def test_store_cache_does_not_overwrite(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("crystallize.utils.cache.CACHE_DIR", Path(tmpdir) / "cache"):
                step_hash = "step"
                input_hash = "input"

                store_cache(step_hash, input_hash, {"version": 1})
                store_cache(step_hash, input_hash, {"version": 2})

                # Should still have version 1 (first write wins)
                loaded = load_cache(step_hash, input_hash)
                assert loaded["version"] == 1

    def test_cache_complex_objects(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("crystallize.utils.cache.CACHE_DIR", Path(tmpdir) / "cache"):
                import numpy as np

                data = {
                    "array": np.array([1, 2, 3]),
                    "list": [1, 2, 3],
                    "tuple": (4, 5, 6),
                    "nested": {"a": {"b": {"c": 1}}},
                }

                store_cache("complex", "data", data)
                loaded = load_cache("complex", "data")

                assert np.array_equal(loaded["array"], data["array"])
                assert loaded["list"] == data["list"]
                assert loaded["tuple"] == data["tuple"]
