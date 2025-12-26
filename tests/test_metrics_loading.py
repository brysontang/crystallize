"""Tests for crystallize.plugins.artifacts load_metrics and load_all_metrics."""

import json
from pathlib import Path

from crystallize.plugins.artifacts import load_metrics, load_all_metrics
from crystallize.utils.constants import BASELINE_CONDITION


def create_results_json(path: Path, metrics: dict) -> None:
    """Helper to create a results.json file with given metrics."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump({"metrics": metrics}, f)


class TestLoadMetrics:
    """Tests for load_metrics()."""

    def test_empty_directory(self, tmp_path: Path) -> None:
        """Test loading from an empty directory."""
        version, baseline, treatments = load_metrics(tmp_path)
        assert version == -1
        assert baseline == {}
        assert treatments == {}

    def test_single_version_baseline_only(self, tmp_path: Path) -> None:
        """Test loading baseline metrics from a single version."""
        create_results_json(
            tmp_path / "v0" / BASELINE_CONDITION / "results.json",
            {"accuracy": 0.95, "loss": 0.05},
        )

        version, baseline, treatments = load_metrics(tmp_path)

        assert version == 0
        assert baseline == {"accuracy": 0.95, "loss": 0.05}
        assert treatments == {}

    def test_single_version_with_treatments(self, tmp_path: Path) -> None:
        """Test loading baseline and treatment metrics."""
        create_results_json(
            tmp_path / "v0" / BASELINE_CONDITION / "results.json",
            {"accuracy": 0.90},
        )
        create_results_json(
            tmp_path / "v0" / "treatment_a" / "results.json",
            {"accuracy": 0.92},
        )
        create_results_json(
            tmp_path / "v0" / "treatment_b" / "results.json",
            {"accuracy": 0.94},
        )

        version, baseline, treatments = load_metrics(tmp_path)

        assert version == 0
        assert baseline == {"accuracy": 0.90}
        assert treatments == {
            "treatment_a": {"accuracy": 0.92},
            "treatment_b": {"accuracy": 0.94},
        }

    def test_multiple_versions_loads_latest(self, tmp_path: Path) -> None:
        """Test that the latest version is loaded when version is None."""
        create_results_json(
            tmp_path / "v0" / BASELINE_CONDITION / "results.json",
            {"accuracy": 0.80},
        )
        create_results_json(
            tmp_path / "v1" / BASELINE_CONDITION / "results.json",
            {"accuracy": 0.85},
        )
        create_results_json(
            tmp_path / "v2" / BASELINE_CONDITION / "results.json",
            {"accuracy": 0.90},
        )

        version, baseline, treatments = load_metrics(tmp_path)

        assert version == 2
        assert baseline == {"accuracy": 0.90}

    def test_specific_version(self, tmp_path: Path) -> None:
        """Test loading a specific version."""
        create_results_json(
            tmp_path / "v0" / BASELINE_CONDITION / "results.json",
            {"accuracy": 0.80},
        )
        create_results_json(
            tmp_path / "v1" / BASELINE_CONDITION / "results.json",
            {"accuracy": 0.90},
        )

        version, baseline, treatments = load_metrics(tmp_path, version=0)

        assert version == 0
        assert baseline == {"accuracy": 0.80}

    def test_missing_baseline_file(self, tmp_path: Path) -> None:
        """Test handling when baseline results.json is missing."""
        (tmp_path / "v0" / BASELINE_CONDITION).mkdir(parents=True)
        create_results_json(
            tmp_path / "v0" / "treatment_a" / "results.json",
            {"accuracy": 0.95},
        )

        version, baseline, treatments = load_metrics(tmp_path)

        assert version == 0
        assert baseline == {}
        assert treatments == {"treatment_a": {"accuracy": 0.95}}

    def test_missing_treatment_results(self, tmp_path: Path) -> None:
        """Test handling when treatment directory has no results.json."""
        create_results_json(
            tmp_path / "v0" / BASELINE_CONDITION / "results.json",
            {"accuracy": 0.90},
        )
        # Create treatment directory without results.json
        (tmp_path / "v0" / "empty_treatment").mkdir(parents=True)

        version, baseline, treatments = load_metrics(tmp_path)

        assert version == 0
        assert baseline == {"accuracy": 0.90}
        assert treatments == {}  # empty_treatment should be skipped

    def test_ignores_non_version_directories(self, tmp_path: Path) -> None:
        """Test that non-version directories are ignored."""
        create_results_json(
            tmp_path / "v0" / BASELINE_CONDITION / "results.json",
            {"accuracy": 0.90},
        )
        # Create some non-version directories
        (tmp_path / "metadata").mkdir()
        (tmp_path / "cache").mkdir()
        (tmp_path / "versionless").mkdir()

        version, baseline, treatments = load_metrics(tmp_path)

        assert version == 0
        assert baseline == {"accuracy": 0.90}

    def test_treatments_sorted_by_name(self, tmp_path: Path) -> None:
        """Test that treatments are returned in sorted order."""
        create_results_json(
            tmp_path / "v0" / BASELINE_CONDITION / "results.json", {}
        )
        create_results_json(
            tmp_path / "v0" / "zebra" / "results.json", {"m": 3}
        )
        create_results_json(
            tmp_path / "v0" / "alpha" / "results.json", {"m": 1}
        )
        create_results_json(
            tmp_path / "v0" / "beta" / "results.json", {"m": 2}
        )

        version, baseline, treatments = load_metrics(tmp_path)

        # Dict should maintain insertion order (sorted)
        assert list(treatments.keys()) == ["alpha", "beta", "zebra"]

    def test_empty_metrics_in_results(self, tmp_path: Path) -> None:
        """Test handling of results.json with no metrics key."""
        path = tmp_path / "v0" / BASELINE_CONDITION / "results.json"
        path.parent.mkdir(parents=True)
        with open(path, "w") as f:
            json.dump({}, f)

        version, baseline, treatments = load_metrics(tmp_path)

        assert version == 0
        assert baseline == {}


class TestLoadAllMetrics:
    """Tests for load_all_metrics()."""

    def test_empty_directory(self, tmp_path: Path) -> None:
        """Test loading from an empty directory."""
        version, baseline, treatments = load_all_metrics(tmp_path)
        assert version == -1
        assert baseline == {}
        assert treatments == {}

    def test_single_version(self, tmp_path: Path) -> None:
        """Test loading from a single version."""
        create_results_json(
            tmp_path / "v0" / BASELINE_CONDITION / "results.json",
            {"accuracy": 0.90},
        )
        create_results_json(
            tmp_path / "v0" / "treatment_a" / "results.json",
            {"accuracy": 0.92},
        )

        version, baseline, treatments = load_all_metrics(tmp_path)

        assert version == 0
        assert baseline == {"accuracy": 0.90}
        assert treatments == {"treatment_a": (0, {"accuracy": 0.92})}

    def test_treatments_from_multiple_versions(self, tmp_path: Path) -> None:
        """Test collecting treatments across multiple versions."""
        # v0 has treatment_a
        create_results_json(
            tmp_path / "v0" / BASELINE_CONDITION / "results.json",
            {"accuracy": 0.80},
        )
        create_results_json(
            tmp_path / "v0" / "treatment_a" / "results.json",
            {"accuracy": 0.82},
        )

        # v1 has treatment_b (and also treatment_a, but v1 takes precedence)
        create_results_json(
            tmp_path / "v1" / BASELINE_CONDITION / "results.json",
            {"accuracy": 0.85},
        )
        create_results_json(
            tmp_path / "v1" / "treatment_a" / "results.json",
            {"accuracy": 0.87},
        )
        create_results_json(
            tmp_path / "v1" / "treatment_b" / "results.json",
            {"accuracy": 0.88},
        )

        version, baseline, treatments = load_all_metrics(tmp_path)

        assert version == 1
        assert baseline == {"accuracy": 0.85}
        # treatment_a from v1 takes precedence over v0
        assert treatments["treatment_a"] == (1, {"accuracy": 0.87})
        assert treatments["treatment_b"] == (1, {"accuracy": 0.88})

    def test_older_treatments_not_in_latest(self, tmp_path: Path) -> None:
        """Test that treatments only in older versions are included."""
        # v0 has old_treatment
        create_results_json(
            tmp_path / "v0" / BASELINE_CONDITION / "results.json",
            {"accuracy": 0.80},
        )
        create_results_json(
            tmp_path / "v0" / "old_treatment" / "results.json",
            {"accuracy": 0.82},
        )

        # v1 only has new_treatment
        create_results_json(
            tmp_path / "v1" / BASELINE_CONDITION / "results.json",
            {"accuracy": 0.90},
        )
        create_results_json(
            tmp_path / "v1" / "new_treatment" / "results.json",
            {"accuracy": 0.92},
        )

        version, baseline, treatments = load_all_metrics(tmp_path)

        assert version == 1
        assert baseline == {"accuracy": 0.90}
        # Both treatments included
        assert treatments["new_treatment"] == (1, {"accuracy": 0.92})
        assert treatments["old_treatment"] == (0, {"accuracy": 0.82})

    def test_specific_version_limit(self, tmp_path: Path) -> None:
        """Test limiting to a specific version."""
        create_results_json(
            tmp_path / "v0" / BASELINE_CONDITION / "results.json",
            {"accuracy": 0.80},
        )
        create_results_json(
            tmp_path / "v0" / "treatment" / "results.json",
            {"accuracy": 0.82},
        )
        create_results_json(
            tmp_path / "v1" / BASELINE_CONDITION / "results.json",
            {"accuracy": 0.90},
        )
        create_results_json(
            tmp_path / "v1" / "treatment" / "results.json",
            {"accuracy": 0.92},
        )

        version, baseline, treatments = load_all_metrics(tmp_path, version=0)

        assert version == 0
        assert baseline == {"accuracy": 0.80}
        assert treatments == {"treatment": (0, {"accuracy": 0.82})}

    def test_missing_baseline_in_latest(self, tmp_path: Path) -> None:
        """Test handling when baseline is missing in the latest version."""
        (tmp_path / "v0" / BASELINE_CONDITION).mkdir(parents=True)
        create_results_json(
            tmp_path / "v0" / "treatment" / "results.json",
            {"accuracy": 0.90},
        )

        version, baseline, treatments = load_all_metrics(tmp_path)

        assert version == 0
        assert baseline == {}
        assert treatments == {"treatment": (0, {"accuracy": 0.90})}

    def test_skips_nonexistent_version_directories(self, tmp_path: Path) -> None:
        """Test that nonexistent version directories are handled."""
        create_results_json(
            tmp_path / "v0" / BASELINE_CONDITION / "results.json",
            {"accuracy": 0.90},
        )
        # v1 doesn't exist
        create_results_json(
            tmp_path / "v2" / BASELINE_CONDITION / "results.json",
            {"accuracy": 0.95},
        )

        version, baseline, treatments = load_all_metrics(tmp_path)

        assert version == 2
        assert baseline == {"accuracy": 0.95}

    def test_version_numbers_non_sequential(self, tmp_path: Path) -> None:
        """Test with non-sequential version numbers."""
        create_results_json(
            tmp_path / "v0" / BASELINE_CONDITION / "results.json",
            {"accuracy": 0.80},
        )
        create_results_json(
            tmp_path / "v5" / BASELINE_CONDITION / "results.json",
            {"accuracy": 0.90},
        )
        create_results_json(
            tmp_path / "v10" / BASELINE_CONDITION / "results.json",
            {"accuracy": 0.95},
        )

        version, baseline, treatments = load_all_metrics(tmp_path)

        assert version == 10
        assert baseline == {"accuracy": 0.95}

    def test_skips_files_in_version_directory(self, tmp_path: Path) -> None:
        """Test that files (not directories) in version dir are ignored."""
        create_results_json(
            tmp_path / "v0" / BASELINE_CONDITION / "results.json",
            {"accuracy": 0.90},
        )
        # Create a file that's not a directory
        (tmp_path / "v0" / "not_a_treatment.txt").write_text("ignore me")

        version, baseline, treatments = load_all_metrics(tmp_path)

        assert version == 0
        assert baseline == {"accuracy": 0.90}
        assert treatments == {}

    def test_respects_version_order(self, tmp_path: Path) -> None:
        """Test that newer versions take precedence for same treatment."""
        # v0: treatment with older metrics
        create_results_json(
            tmp_path / "v0" / BASELINE_CONDITION / "results.json", {}
        )
        create_results_json(
            tmp_path / "v0" / "shared" / "results.json",
            {"value": "old"},
        )
        create_results_json(
            tmp_path / "v0" / "only_v0" / "results.json",
            {"value": "v0_only"},
        )

        # v1: treatment with newer metrics
        create_results_json(
            tmp_path / "v1" / BASELINE_CONDITION / "results.json", {}
        )
        create_results_json(
            tmp_path / "v1" / "shared" / "results.json",
            {"value": "new"},
        )
        create_results_json(
            tmp_path / "v1" / "only_v1" / "results.json",
            {"value": "v1_only"},
        )

        version, baseline, treatments = load_all_metrics(tmp_path)

        assert version == 1
        # "shared" should have v1's value
        assert treatments["shared"] == (1, {"value": "new"})
        # Both unique treatments should be present
        assert treatments["only_v0"] == (0, {"value": "v0_only"})
        assert treatments["only_v1"] == (1, {"value": "v1_only"})
