"""Tests for cli.yaml_edit module."""

from pathlib import Path

from cli.yaml_edit import (
    find_treatment_line,
    ensure_new_treatment_placeholder,
    find_treatment_apply_line,
)


class TestFindTreatmentLine:
    """Tests for find_treatment_line()."""

    def test_finds_treatment_in_simple_yaml(self, tmp_path: Path) -> None:
        """Test finding a treatment in a simple YAML file."""
        yaml_content = """\
name: test
treatments:
  treatment_a:
    param: 1
  treatment_b:
    param: 2
"""
        path = tmp_path / "config.yaml"
        path.write_text(yaml_content)

        assert find_treatment_line(path, "treatment_a") == 3
        assert find_treatment_line(path, "treatment_b") == 5

    def test_returns_1_for_missing_treatment(self, tmp_path: Path) -> None:
        """Test that missing treatment returns line 1."""
        yaml_content = """\
treatments:
  treatment_a:
    param: 1
"""
        path = tmp_path / "config.yaml"
        path.write_text(yaml_content)

        assert find_treatment_line(path, "nonexistent") == 1

    def test_returns_1_for_no_treatments_block(self, tmp_path: Path) -> None:
        """Test that missing treatments block returns line 1."""
        yaml_content = """\
name: test
datasource:
  type: dummy
"""
        path = tmp_path / "config.yaml"
        path.write_text(yaml_content)

        assert find_treatment_line(path, "treatment_a") == 1

    def test_returns_1_for_nonexistent_file(self, tmp_path: Path) -> None:
        """Test that nonexistent file returns line 1."""
        path = tmp_path / "nonexistent.yaml"
        assert find_treatment_line(path, "treatment_a") == 1

    def test_handles_indented_treatments_block(self, tmp_path: Path) -> None:
        """Test finding treatment with indented treatments block."""
        yaml_content = """\
experiment:
  treatments:
    my_treatment:
      value: 10
"""
        path = tmp_path / "config.yaml"
        path.write_text(yaml_content)

        assert find_treatment_line(path, "my_treatment") == 3

    def test_stops_at_end_of_treatments_block(self, tmp_path: Path) -> None:
        """Test that search stops when leaving treatments block."""
        yaml_content = """\
treatments:
  treatment_a:
    param: 1
other_section:
  treatment_a:
    param: 2
"""
        path = tmp_path / "config.yaml"
        path.write_text(yaml_content)

        # Should find the one in treatments block
        assert find_treatment_line(path, "treatment_a") == 2

    def test_handles_empty_file(self, tmp_path: Path) -> None:
        """Test handling of empty file."""
        path = tmp_path / "empty.yaml"
        path.write_text("")

        assert find_treatment_line(path, "treatment") == 1

    def test_handles_treatments_block_at_end(self, tmp_path: Path) -> None:
        """Test treatments block at the end of file."""
        yaml_content = """\
name: test
treatments:
  final_treatment:
    value: 1
"""
        path = tmp_path / "config.yaml"
        path.write_text(yaml_content)

        assert find_treatment_line(path, "final_treatment") == 3


class TestEnsureNewTreatmentPlaceholder:
    """Tests for ensure_new_treatment_placeholder()."""

    def test_adds_placeholder_after_existing_treatments(self, tmp_path: Path) -> None:
        """Test adding placeholder after existing treatments."""
        yaml_content = """\
treatments:
  existing:
    value: 1
"""
        path = tmp_path / "config.yaml"
        path.write_text(yaml_content)

        line = ensure_new_treatment_placeholder(path)

        result = path.read_text()
        assert "# new treatment" in result
        assert line == 4  # After the existing treatment

    def test_adds_treatments_block_if_missing(self, tmp_path: Path) -> None:
        """Test creating treatments block if it doesn't exist."""
        yaml_content = """\
name: test
datasource: {}
"""
        path = tmp_path / "config.yaml"
        path.write_text(yaml_content)

        ensure_new_treatment_placeholder(path)

        result = path.read_text()
        assert "treatments:" in result
        assert "# new treatment" in result

    def test_preserves_trailing_newline(self, tmp_path: Path) -> None:
        """Test that trailing newline is preserved."""
        yaml_content = "treatments:\n  existing:\n    value: 1\n"
        path = tmp_path / "config.yaml"
        path.write_text(yaml_content)

        ensure_new_treatment_placeholder(path)

        result = path.read_text()
        assert result.endswith("\n")

    def test_no_trailing_newline_preserved(self, tmp_path: Path) -> None:
        """Test that absence of trailing newline is preserved."""
        yaml_content = "treatments:\n  existing:\n    value: 1"
        path = tmp_path / "config.yaml"
        path.write_text(yaml_content)

        ensure_new_treatment_placeholder(path)

        result = path.read_text()
        assert not result.endswith("\n")

    def test_inserts_before_next_section(self, tmp_path: Path) -> None:
        """Test that placeholder is inserted before next section."""
        yaml_content = """\
treatments:
  existing:
    value: 1
other_section:
  key: value
"""
        path = tmp_path / "config.yaml"
        path.write_text(yaml_content)

        ensure_new_treatment_placeholder(path)

        result = path.read_text()
        lines = result.splitlines()
        # Placeholder should be before "other_section"
        placeholder_idx = next(
            i for i, line in enumerate(lines) if "# new treatment" in line
        )
        other_idx = next(i for i, line in enumerate(lines) if "other_section" in line)
        assert placeholder_idx < other_idx

    def test_handles_indented_treatments_block(self, tmp_path: Path) -> None:
        """Test with indented treatments block."""
        yaml_content = """\
experiment:
  treatments:
    existing:
      value: 1
"""
        path = tmp_path / "config.yaml"
        path.write_text(yaml_content)

        ensure_new_treatment_placeholder(path)

        result = path.read_text()
        assert "# new treatment" in result


class TestFindTreatmentApplyLine:
    """Tests for find_treatment_apply_line()."""

    def test_finds_key_in_treatment(self, tmp_path: Path) -> None:
        """Test finding a key within a treatment."""
        yaml_content = """\
treatments:
  my_treatment:
    param1: value1
    param2: value2
"""
        path = tmp_path / "config.yaml"
        path.write_text(yaml_content)

        assert find_treatment_apply_line(path, "my_treatment", "param1") == 3
        assert find_treatment_apply_line(path, "my_treatment", "param2") == 4

    def test_returns_1_for_missing_key(self, tmp_path: Path) -> None:
        """Test that missing key returns line 1."""
        yaml_content = """\
treatments:
  my_treatment:
    param1: value1
"""
        path = tmp_path / "config.yaml"
        path.write_text(yaml_content)

        assert find_treatment_apply_line(path, "my_treatment", "missing") == 1

    def test_returns_1_for_missing_treatment(self, tmp_path: Path) -> None:
        """Test that missing treatment returns line 1."""
        yaml_content = """\
treatments:
  other_treatment:
    param: value
"""
        path = tmp_path / "config.yaml"
        path.write_text(yaml_content)

        assert find_treatment_apply_line(path, "nonexistent", "param") == 1

    def test_returns_1_for_no_treatments_block(self, tmp_path: Path) -> None:
        """Test that missing treatments block returns line 1."""
        yaml_content = """\
name: test
"""
        path = tmp_path / "config.yaml"
        path.write_text(yaml_content)

        assert find_treatment_apply_line(path, "treatment", "key") == 1

    def test_returns_1_for_nonexistent_file(self, tmp_path: Path) -> None:
        """Test that nonexistent file returns line 1."""
        path = tmp_path / "nonexistent.yaml"
        assert find_treatment_apply_line(path, "treatment", "key") == 1

    def test_stays_within_treatment_block(self, tmp_path: Path) -> None:
        """Test that search stays within the specified treatment block."""
        yaml_content = """\
treatments:
  treatment_a:
    key_a: 1
  treatment_b:
    key_b: 2
"""
        path = tmp_path / "config.yaml"
        path.write_text(yaml_content)

        # Should find key_a in treatment_a
        assert find_treatment_apply_line(path, "treatment_a", "key_a") == 3
        # Should NOT find key_b in treatment_a (it's in treatment_b)
        assert find_treatment_apply_line(path, "treatment_a", "key_b") == 1

    def test_handles_nested_structure(self, tmp_path: Path) -> None:
        """Test with deeply nested structure."""
        yaml_content = """\
treatments:
  my_treatment:
    apply:
      nested_key: value
"""
        path = tmp_path / "config.yaml"
        path.write_text(yaml_content)

        assert find_treatment_apply_line(path, "my_treatment", "apply") == 3

    def test_stops_at_end_of_treatment(self, tmp_path: Path) -> None:
        """Test that search stops at the end of treatment block."""
        yaml_content = """\
treatments:
  treatment_a:
    key: value
other_section:
  key: other_value
"""
        path = tmp_path / "config.yaml"
        path.write_text(yaml_content)

        # Should find key in treatment_a
        assert find_treatment_apply_line(path, "treatment_a", "key") == 3

    def test_handles_empty_file(self, tmp_path: Path) -> None:
        """Test handling of empty file."""
        path = tmp_path / "empty.yaml"
        path.write_text("")

        assert find_treatment_apply_line(path, "treatment", "key") == 1
