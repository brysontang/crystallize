import pytest
from crystallize.cli import main


def test_cli_missing_file(tmp_path):
    bad = tmp_path / "missing.yaml"
    with pytest.raises(FileNotFoundError):
        main.main(["run", str(bad)])


def test_cli_invalid_yaml(tmp_path):
    cfg = tmp_path / "bad.yaml"
    cfg.write_text("::invalid::yaml::")
    with pytest.raises(Exception):
        main.main(["run", str(cfg)])
