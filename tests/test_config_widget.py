from pathlib import Path
import yaml
import pytest
from textual.app import App

from cli.widgets.config_editor import ConfigEditorWidget


@pytest.mark.asyncio
async def test_config_tree(tmp_path: Path) -> None:
    cfg = tmp_path / "config.yaml"
    cfg.write_text(yaml.safe_dump({"name": "e", "steps": ["a", "b"], "replicates": 1}))
    async with App().run_test() as pilot:
        widget = ConfigEditorWidget(cfg)
        await pilot.app.mount(widget)
        labels = {str(child.label) for child in widget.cfg_tree.root.children}
        assert {"name", "steps", "replicates"} <= labels


@pytest.mark.asyncio
async def test_add_nodes_present(tmp_path: Path) -> None:
    cfg = tmp_path / "config.yaml"
    cfg.write_text(yaml.safe_dump({"name": "e", "steps": ["a"], "datasource": {"x": "ds"}}))
    async with App().run_test() as pilot:
        widget = ConfigEditorWidget(cfg)
        await pilot.app.mount(widget)
        steps_node = next(child for child in widget.cfg_tree.root.children if str(child.label) == "steps")
        labels = [str(c.label) for c in steps_node.children]
        assert any(label.startswith("+ add") for label in labels)
