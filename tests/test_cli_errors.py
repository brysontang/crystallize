"""Tests for cli.errors module."""

from pathlib import Path

import yaml

from cli.errors import ExperimentLoadError, format_load_error


class TestExperimentLoadError:
    """Tests for ExperimentLoadError exception."""

    def test_is_exception(self) -> None:
        """Test that ExperimentLoadError is an Exception."""
        err = ExperimentLoadError("test message")
        assert isinstance(err, Exception)

    def test_stores_message(self) -> None:
        """Test that the message is stored correctly."""
        err = ExperimentLoadError("custom error message")
        assert str(err) == "custom error message"


class TestFormatLoadError:
    """Tests for format_load_error()."""

    def test_formats_yaml_error(self, tmp_path: Path) -> None:
        """Test formatting of YAML parsing errors."""
        path = tmp_path / "config.yaml"
        yaml_error = yaml.YAMLError("invalid syntax at line 5")

        result = format_load_error(path, yaml_error)

        assert isinstance(result, ExperimentLoadError)
        assert "Invalid YAML" in str(result)
        assert str(path) in str(result)
        assert "invalid syntax" in str(result)

    def test_formats_file_not_found_error(self, tmp_path: Path) -> None:
        """Test formatting of FileNotFoundError."""
        path = tmp_path / "config.yaml"
        missing_file = tmp_path / "missing.py"
        fnf_error = FileNotFoundError(2, "No such file", str(missing_file))

        result = format_load_error(path, fnf_error)

        assert isinstance(result, ExperimentLoadError)
        assert "was not found" in str(result)
        assert str(missing_file) in str(result)
        assert str(path) in str(result)

    def test_formats_file_not_found_without_filename(self, tmp_path: Path) -> None:
        """Test formatting of FileNotFoundError without filename attribute."""
        path = tmp_path / "config.yaml"
        fnf_error = FileNotFoundError("some file is missing")

        result = format_load_error(path, fnf_error)

        assert isinstance(result, ExperimentLoadError)
        assert "was not found" in str(result)

    def test_formats_attribute_error(self, tmp_path: Path) -> None:
        """Test formatting of AttributeError (invalid module reference)."""
        path = tmp_path / "config.yaml"
        attr_error = AttributeError("module 'foo' has no attribute 'bar'")

        result = format_load_error(path, attr_error)

        assert isinstance(result, ExperimentLoadError)
        assert str(path) in str(result)
        assert "has no attribute" in str(result)
        assert "valid modules and attributes" in str(result)

    def test_formats_key_error(self, tmp_path: Path) -> None:
        """Test formatting of KeyError (missing config key)."""
        path = tmp_path / "config.yaml"
        key_error = KeyError("datasource")

        result = format_load_error(path, key_error)

        assert isinstance(result, ExperimentLoadError)
        assert "Missing required configuration key" in str(result)
        assert "'datasource'" in str(result)
        assert str(path) in str(result)

    def test_formats_generic_exception(self, tmp_path: Path) -> None:
        """Test formatting of generic exceptions."""
        path = tmp_path / "config.yaml"
        generic_error = RuntimeError("something went wrong")

        result = format_load_error(path, generic_error)

        assert isinstance(result, ExperimentLoadError)
        assert str(path) in str(result)
        assert "something went wrong" in str(result)

    def test_formats_value_error(self, tmp_path: Path) -> None:
        """Test formatting of ValueError."""
        path = tmp_path / "config.yaml"
        value_error = ValueError("invalid value for parameter")

        result = format_load_error(path, value_error)

        assert isinstance(result, ExperimentLoadError)
        assert str(path) in str(result)
        assert "invalid value for parameter" in str(result)

    def test_formats_type_error(self, tmp_path: Path) -> None:
        """Test formatting of TypeError."""
        path = tmp_path / "config.yaml"
        type_error = TypeError("expected str, got int")

        result = format_load_error(path, type_error)

        assert isinstance(result, ExperimentLoadError)
        assert str(path) in str(result)
        assert "expected str, got int" in str(result)

    def test_handles_yaml_scanner_error(self, tmp_path: Path) -> None:
        """Test formatting of yaml.scanner.ScannerError (subclass of YAMLError)."""
        path = tmp_path / "config.yaml"
        scanner_error = yaml.scanner.ScannerError(
            "while scanning", None, "found unexpected ':'", None
        )

        result = format_load_error(path, scanner_error)

        assert isinstance(result, ExperimentLoadError)
        assert "Invalid YAML" in str(result)
