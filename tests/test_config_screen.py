from pathlib import Path
import yaml
import pytest
from textual.app import App

from cli.screens.config_editor import ConfigEditorScreen


@pytest.mark.asyncio
async def test_config_tree(tmp_path: Path) -> None:
    cfg = tmp_path / "config.yaml"
    cfg.write_text(yaml.safe_dump({"name": "e", "steps": ["a", "b"], "replicates": 1}))
    async with App().run_test() as pilot:
        screen = ConfigEditorScreen(cfg)
        await pilot.app.push_screen(screen)
        labels = {str(child.label) for child in screen.cfg_tree.root.children}
        assert {"name", "steps", "replicates"} <= labels
