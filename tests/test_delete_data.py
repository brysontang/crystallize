"""Tests for cli.screens.delete_data module."""

from pathlib import Path

import pytest
from textual.app import App

from cli.screens.delete_data import ConfirmScreen


class TestConfirmScreen:
    """Tests for the ConfirmScreen modal."""

    def test_screen_initializes_with_paths(self, tmp_path: Path) -> None:
        """Test that ConfirmScreen stores paths correctly."""
        paths = [tmp_path / "file1.txt", tmp_path / "file2.txt"]
        screen = ConfirmScreen(paths_to_delete=paths)
        assert screen._paths == paths

    def test_screen_initializes_with_empty_paths(self) -> None:
        """Test that ConfirmScreen handles empty path list."""
        screen = ConfirmScreen(paths_to_delete=[])
        assert screen._paths == []

    def test_action_confirm_and_exit_calls_dismiss_with_true(self) -> None:
        """Test that action_confirm_and_exit dismisses with True."""
        screen = ConfirmScreen(paths_to_delete=[])
        dismissed_value = None

        def mock_dismiss(value):
            nonlocal dismissed_value
            dismissed_value = value

        screen.dismiss = mock_dismiss
        screen.action_confirm_and_exit()
        assert dismissed_value is True

    def test_action_cancel_and_exit_calls_dismiss_with_false(self) -> None:
        """Test that action_cancel_and_exit dismisses with False."""
        screen = ConfirmScreen(paths_to_delete=[])
        dismissed_value = None

        def mock_dismiss(value):
            nonlocal dismissed_value
            dismissed_value = value

        screen.dismiss = mock_dismiss
        screen.action_cancel_and_exit()
        assert dismissed_value is False

    def test_bindings_configured(self) -> None:
        """Test that expected keybindings are configured."""
        screen = ConfirmScreen(paths_to_delete=[])
        binding_keys = [b.key for b in screen.BINDINGS]
        assert "y" in binding_keys
        assert "escape" in binding_keys
        assert "n" in binding_keys
        assert "q" in binding_keys
        assert "ctrl+c" in binding_keys

    @pytest.mark.asyncio
    async def test_yes_button_press_dismisses_with_true(self, tmp_path: Path) -> None:
        """Test that Yes button press results in True."""
        paths = [tmp_path / "file.txt"]

        class TestApp(App):
            def __init__(self):
                super().__init__()
                self.result = None

            def on_mount(self):
                screen = ConfirmScreen(paths_to_delete=paths)
                self.push_screen(screen, self.handle_result)

            def handle_result(self, value):
                self.result = value
                self.exit()

        app = TestApp()
        async with app.run_test() as pilot:
            # Wait for mount and try clicking Yes
            for _ in range(5):
                await pilot.pause()
                try:
                    await pilot.click("#yes")
                    break
                except Exception:
                    pass

        assert app.result is True

    @pytest.mark.asyncio
    async def test_no_button_press_dismisses_with_false(self, tmp_path: Path) -> None:
        """Test that No button press results in False."""
        paths = [tmp_path / "file.txt"]

        class TestApp(App):
            def __init__(self):
                super().__init__()
                self.result = None

            def on_mount(self):
                screen = ConfirmScreen(paths_to_delete=paths)
                self.push_screen(screen, self.handle_result)

            def handle_result(self, value):
                self.result = value
                self.exit()

        app = TestApp()
        async with app.run_test() as pilot:
            for _ in range(5):
                await pilot.pause()
                try:
                    await pilot.click("#no")
                    break
                except Exception:
                    pass

        assert app.result is False

    @pytest.mark.asyncio
    async def test_y_key_confirms(self, tmp_path: Path) -> None:
        """Test that pressing 'y' confirms."""
        paths = [tmp_path / "file.txt"]

        class TestApp(App):
            def __init__(self):
                super().__init__()
                self.result = None

            def on_mount(self):
                screen = ConfirmScreen(paths_to_delete=paths)
                self.push_screen(screen, self.handle_result)

            def handle_result(self, value):
                self.result = value
                self.exit()

        app = TestApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            await pilot.press("y")
            await pilot.pause()

        assert app.result is True

    @pytest.mark.asyncio
    async def test_escape_cancels(self, tmp_path: Path) -> None:
        """Test that pressing Escape cancels."""
        paths = [tmp_path / "file.txt"]

        class TestApp(App):
            def __init__(self):
                super().__init__()
                self.result = None

            def on_mount(self):
                screen = ConfirmScreen(paths_to_delete=paths)
                self.push_screen(screen, self.handle_result)

            def handle_result(self, value):
                self.result = value
                self.exit()

        app = TestApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            await pilot.press("escape")
            await pilot.pause()

        assert app.result is False
