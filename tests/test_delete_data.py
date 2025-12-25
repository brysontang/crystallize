"""Tests for cli.screens.delete_data module."""

from pathlib import Path

import pytest
from textual.app import App
from textual.widgets import Button

from cli.screens.delete_data import ConfirmScreen


class TestConfirmScreen:
    """Tests for the ConfirmScreen modal."""

    @pytest.mark.asyncio
    async def test_displays_paths_to_delete(self, tmp_path: Path) -> None:
        """Test that paths are displayed in the confirmation screen."""
        paths = [tmp_path / "file1.txt", tmp_path / "file2.txt"]

        async with App().run_test() as pilot:
            screen = ConfirmScreen(paths_to_delete=paths)
            await pilot.app.push_screen(screen)
            await pilot.pause()

            # Check that both paths are displayed
            text = screen.query("Static")
            rendered_text = " ".join(str(s.renderable) for s in text)
            assert "file1.txt" in rendered_text
            assert "file2.txt" in rendered_text

    @pytest.mark.asyncio
    async def test_displays_nothing_selected_for_empty_paths(self) -> None:
        """Test that empty path list shows '(Nothing selected)'."""
        async with App().run_test() as pilot:
            screen = ConfirmScreen(paths_to_delete=[])
            await pilot.app.push_screen(screen)
            await pilot.pause()

            text = screen.query("Static")
            rendered_text = " ".join(str(s.renderable) for s in text)
            assert "(Nothing selected)" in rendered_text

    @pytest.mark.asyncio
    async def test_no_button_focused_on_mount(self) -> None:
        """Test that the 'No' button is focused by default for safety."""
        async with App().run_test() as pilot:
            screen = ConfirmScreen(paths_to_delete=[])
            await pilot.app.push_screen(screen)
            await pilot.pause()

            no_button = screen.query_one("#no", Button)
            assert no_button.has_focus

    @pytest.mark.asyncio
    async def test_yes_button_dismisses_with_true(self, tmp_path: Path) -> None:
        """Test that clicking Yes dismisses with True."""
        paths = [tmp_path / "file.txt"]
        result = None

        async with App().run_test() as pilot:
            screen = ConfirmScreen(paths_to_delete=paths)

            def capture_result(value):
                nonlocal result
                result = value

            screen._dismiss_callback = capture_result
            await pilot.app.push_screen(screen)
            await pilot.pause()

            yes_button = screen.query_one("#yes", Button)
            await pilot.click(yes_button)
            await pilot.pause()

        assert result is True

    @pytest.mark.asyncio
    async def test_no_button_dismisses_with_false(self, tmp_path: Path) -> None:
        """Test that clicking No dismisses with False."""
        paths = [tmp_path / "file.txt"]
        result = None

        async with App().run_test() as pilot:
            screen = ConfirmScreen(paths_to_delete=paths)

            def capture_result(value):
                nonlocal result
                result = value

            screen._dismiss_callback = capture_result
            await pilot.app.push_screen(screen)
            await pilot.pause()

            no_button = screen.query_one("#no", Button)
            await pilot.click(no_button)
            await pilot.pause()

        assert result is False

    @pytest.mark.asyncio
    async def test_escape_key_dismisses_with_false(self, tmp_path: Path) -> None:
        """Test that pressing Escape dismisses with False."""
        paths = [tmp_path / "file.txt"]
        result = None

        async with App().run_test() as pilot:
            screen = ConfirmScreen(paths_to_delete=paths)

            def capture_result(value):
                nonlocal result
                result = value

            screen._dismiss_callback = capture_result
            await pilot.app.push_screen(screen)
            await pilot.pause()

            await pilot.press("escape")
            await pilot.pause()

        assert result is False

    @pytest.mark.asyncio
    async def test_y_key_confirms(self, tmp_path: Path) -> None:
        """Test that pressing 'y' confirms and dismisses with True."""
        paths = [tmp_path / "file.txt"]
        result = None

        async with App().run_test() as pilot:
            screen = ConfirmScreen(paths_to_delete=paths)

            def capture_result(value):
                nonlocal result
                result = value

            screen._dismiss_callback = capture_result
            await pilot.app.push_screen(screen)
            await pilot.pause()

            await pilot.press("y")
            await pilot.pause()

        assert result is True

    @pytest.mark.asyncio
    async def test_n_key_cancels(self, tmp_path: Path) -> None:
        """Test that pressing 'n' cancels and dismisses with False."""
        paths = [tmp_path / "file.txt"]
        result = None

        async with App().run_test() as pilot:
            screen = ConfirmScreen(paths_to_delete=paths)

            def capture_result(value):
                nonlocal result
                result = value

            screen._dismiss_callback = capture_result
            await pilot.app.push_screen(screen)
            await pilot.pause()

            await pilot.press("n")
            await pilot.pause()

        assert result is False

    @pytest.mark.asyncio
    async def test_q_key_cancels(self, tmp_path: Path) -> None:
        """Test that pressing 'q' cancels and dismisses with False."""
        paths = [tmp_path / "file.txt"]
        result = None

        async with App().run_test() as pilot:
            screen = ConfirmScreen(paths_to_delete=paths)

            def capture_result(value):
                nonlocal result
                result = value

            screen._dismiss_callback = capture_result
            await pilot.app.push_screen(screen)
            await pilot.pause()

            await pilot.press("q")
            await pilot.pause()

        assert result is False

    @pytest.mark.asyncio
    async def test_displays_warning_message(self) -> None:
        """Test that the warning message is displayed."""
        async with App().run_test() as pilot:
            screen = ConfirmScreen(paths_to_delete=[])
            await pilot.app.push_screen(screen)
            await pilot.pause()

            text = screen.query("Static")
            rendered_text = " ".join(str(s.renderable) for s in text)
            assert "permanently deleted" in rendered_text
            assert "Are you sure" in rendered_text
