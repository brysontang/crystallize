from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

from cli.screens.selection import SelectionScreen


def test_get_experiment_status_without_data(monkeypatch, tmp_path: Path) -> None:
    screen = SelectionScreen()
    monkeypatch.chdir(tmp_path)

    status, last_run = screen._get_experiment_status("demo")

    assert status == "⚪"
    assert last_run == "Never"


def test_get_experiment_status_uses_latest_version(monkeypatch, tmp_path: Path) -> None:
    screen = SelectionScreen()
    monkeypatch.chdir(tmp_path)

    base = tmp_path / "data" / "demo"
    (base / "v1").mkdir(parents=True)
    (base / "v3").mkdir()
    meta_old = base / "v1" / "metadata.json"
    meta_new = base / "v3" / "metadata.json"
    meta_old.write_text("{}")
    meta_new.write_text("{}")
    ts = datetime(2024, 1, 2, 3, 4, 5).timestamp()
    os.utime(meta_new, (ts, ts))

    status, last_run = screen._get_experiment_status("demo")

    assert status == "🟢"
    assert last_run == datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")


def test_get_experiment_status_without_metadata(monkeypatch, tmp_path: Path) -> None:
    screen = SelectionScreen()
    monkeypatch.chdir(tmp_path)

    base = tmp_path / "data" / "demo"
    (base / "v2").mkdir(parents=True)

    status, last_run = screen._get_experiment_status("demo")

    assert status == "⚪"
    assert last_run == "Never"
