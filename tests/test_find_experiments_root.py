from pathlib import Path
import logging

import pytest

from crystallize.experiments.experiment_graph import find_experiments_root


def test_find_experiments_root_finds_existing(tmp_path: Path) -> None:
    root = tmp_path / "experiments"
    root.mkdir()
    subdir = root / "a" / "b"
    subdir.mkdir(parents=True)
    assert find_experiments_root(subdir) == root


def test_find_experiments_root_raises_when_missing(tmp_path: Path) -> None:
    start = tmp_path / "a" / "b"
    start.mkdir(parents=True)
    with pytest.raises(FileNotFoundError):
        find_experiments_root(start)


def test_find_experiments_root_warns_and_returns_start_when_non_strict(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    start = tmp_path / "a" / "b"
    start.mkdir(parents=True)
    with caplog.at_level(logging.WARNING):
        result = find_experiments_root(start, strict=False)
    assert result == start
    assert "Could not locate 'experiments' dir" in caplog.text
