import os
from pathlib import Path
import yaml
import pytest
from textual.app import App

from cli.screens.create_experiment import CreateExperimentScreen, OutputTree


@pytest.mark.asyncio
async def test_output_tree(tmp_path: Path) -> None:
    base = tmp_path / "experiments"
    base.mkdir()
    e1 = base / "exp1"
    e1.mkdir()
    (e1 / "config.yaml").write_text(yaml.safe_dump({"outputs": {"out1": {}}}))
    e2 = base / "exp2"
    e2.mkdir()
    (e2 / "config.yaml").write_text(yaml.safe_dump({"outputs": {"out2": {}}}))

    cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        async with App().run_test() as pilot:
            screen = CreateExperimentScreen()
            await pilot.app.push_screen(screen)
            tree = screen.query_one("#out-tree", OutputTree)
            labels = {str(child.label) for child in tree.root.children}
            assert labels == {"exp1", "exp2"}
    finally:
        os.chdir(cwd)
