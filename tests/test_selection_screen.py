import os
from pathlib import Path
import yaml
import pytest
from textual.app import App

from cli.screens.selection import SelectionScreen
from cli.widgets.config_editor import ConfigEditorWidget


@pytest.mark.asyncio
async def test_update_details_mounts_widget(tmp_path: Path) -> None:
    exp_dir = tmp_path / "exp"
    exp_dir.mkdir()
    cfg = exp_dir / "config.yaml"
    cfg.write_text(
        yaml.safe_dump(
            {"name": "e", "cli": {"icon": "🔬", "group": "test", "priority": 1}}
        )
    )

    cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        async with App().run_test() as pilot:
            screen = SelectionScreen()
            await pilot.app.push_screen(screen)
            await pilot.pause(1)

            data = {
                "path": str(cfg),
                "label": "test",
                "type": "Experiment",
                "doc": "test doc",
            }
            await screen._update_details(data)

            container = screen.query_one("#config-container")
            assert any(
                isinstance(child, ConfigEditorWidget) for child in container.children
            )
    finally:
        os.chdir(cwd)
