from pathlib import Path
import yaml
import pytest
from textual.app import App

from cli.widgets.config_editor import AddNode, ConfigEditorWidget


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
    cfg.write_text(
        yaml.safe_dump({"name": "e", "steps": ["a"], "datasource": {"x": "ds"}})
    )
    async with App().run_test() as pilot:
        widget = ConfigEditorWidget(cfg)
        await pilot.app.mount(widget)
        steps_node = next(
            child
            for child in widget.cfg_tree.root.children
            if str(child.label) == "steps"
        )
        labels = [str(c.label) for c in steps_node.children]
        assert any(label.startswith("+ add") for label in labels)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "add_type,result,fname,fragment",
    [
        ("steps", {"name": "mystep"}, "steps.py", "def mystep("),
        (
            "datasource",
            {"data_key": "d", "method": "get_data"},
            "datasources.py",
            "def get_data(",
        ),
        (
            "outputs",
            {"alias": "out", "file_name": "out.txt", "loader": "load"},
            "outputs.py",
            "def load(",
        ),
        (
            "hypotheses",
            {"name": "h", "verifier": "check", "metrics": "m"},
            "verifiers.py",
            "def check(",
        ),
    ],
)
async def test_add_placeholders(
    tmp_path: Path, add_type: str, result: dict, fname: str, fragment: str
) -> None:
    cfg = tmp_path / "config.yaml"
    cfg.write_text(yaml.safe_dump({"name": "e"}))
    async with App().run_test() as pilot:
        widget = ConfigEditorWidget(cfg)
        await pilot.app.mount(widget)
        await pilot.pause(0.1)

        async def fake_push(screen, cb):
            cb(result)

        widget.app.push_screen = fake_push  # type: ignore[assignment]
        node = AddNode(widget.cfg_tree, widget.cfg_tree.root, "", add_type)
        await widget._open_add_screen(node)

        text = (tmp_path / fname).read_text()
        assert fragment in text


@pytest.mark.asyncio
async def test_add_treatment(tmp_path: Path) -> None:
    cfg = tmp_path / "config.yaml"
    cfg.write_text(yaml.safe_dump({"name": "e"}))
    async with App().run_test() as pilot:
        widget = ConfigEditorWidget(cfg)
        await pilot.app.mount(widget)
        await pilot.pause(0.1)

        async def fake_push(screen, cb):
            cb({"name": "tr", "context_field": "dose", "value": "1"})

        widget.app.push_screen = fake_push  # type: ignore[assignment]
        node = AddNode(widget.cfg_tree, widget.cfg_tree.root, "", "treatments")
        await widget._open_add_screen(node)

        data = yaml.safe_load(cfg.read_text())
        assert data["treatments"]["tr"]["dose"] == 1


@pytest.mark.asyncio
async def test_edit_updates_file(tmp_path: Path) -> None:
    cfg = tmp_path / "config.yaml"
    cfg.write_text(yaml.safe_dump({"name": "e", "steps": ["a"]}))
    async with App().run_test() as pilot:
        widget = ConfigEditorWidget(cfg)
        await pilot.app.mount(widget)
        await pilot.pause(0.1)

        steps_node = next(
            child for child in widget.cfg_tree.root.children if str(child.label) == "steps"
        )
        leaf = steps_node.children[0]
        widget.cfg_tree._cursor_node = leaf  # type: ignore[attr-defined]

        async def fake_push(screen, cb):
            cb("b")

        widget.app.push_screen = fake_push  # type: ignore[assignment]
        await widget.action_edit()
        data = yaml.safe_load(cfg.read_text())
        assert data["steps"] == ["b"]


@pytest.mark.asyncio
async def test_edit_with_no_selection(tmp_path: Path) -> None:
    cfg = tmp_path / "config.yaml"
    cfg.write_text(yaml.safe_dump({}))
    async with App().run_test() as pilot:
        widget = ConfigEditorWidget(cfg)
        await pilot.app.mount(widget)
        await pilot.pause(0.1)
        await widget.action_edit()


@pytest.mark.asyncio
async def test_add_treatment_numeric_value(tmp_path: Path) -> None:
    cfg = tmp_path / "config.yaml"
    cfg.write_text(yaml.safe_dump({"name": "e"}))
    async with App().run_test() as pilot:
        widget = ConfigEditorWidget(cfg)
        await pilot.app.mount(widget)
        await pilot.pause(0.1)

        async def fake_push(screen, cb):
            cb({"name": "tr", "context_field": "dose", "value": "2"})

        widget.app.push_screen = fake_push  # type: ignore[assignment]
        node = AddNode(widget.cfg_tree, widget.cfg_tree.root, "", "treatments")
        await widget._open_add_screen(node)

        data = yaml.safe_load(cfg.read_text())
        assert data["treatments"]["tr"]["dose"] == 2
