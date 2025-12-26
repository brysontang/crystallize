"""Tests for cli.screens.load_error module."""

import pytest
from textual.app import App

from cli.screens.load_error import LoadErrorScreen


class TestLoadErrorScreen:
    """Tests for the LoadErrorScreen modal."""

    def test_screen_initializes_with_message(self) -> None:
        """Test that LoadErrorScreen stores the message correctly."""
        screen = LoadErrorScreen(message="Something went wrong")
        assert screen._message == "Something went wrong"

    def test_action_close_calls_dismiss(self) -> None:
        """Test that action_close dismisses the screen."""
        screen = LoadErrorScreen(message="Error")
        dismissed = []

        def mock_dismiss(value):
            dismissed.append(value)

        screen.dismiss = mock_dismiss
        screen.action_close()
        assert dismissed == [None]

    def test_bindings_configured(self) -> None:
        """Test that expected keybindings are configured."""
        screen = LoadErrorScreen(message="Error")
        binding_keys = [b[0] for b in screen.BINDINGS]
        assert "ctrl+c" in binding_keys
        assert "escape" in binding_keys
        assert "q" in binding_keys

    @pytest.mark.asyncio
    async def test_close_button_dismisses(self) -> None:
        """Test that clicking Close button dismisses the screen."""

        class TestApp(App):
            def __init__(self):
                super().__init__()
                self.dismissed = False

            def on_mount(self):
                screen = LoadErrorScreen(message="Test error message")
                self.push_screen(screen, self.handle_dismiss)

            def handle_dismiss(self, value):
                self.dismissed = True
                self.exit()

        app = TestApp()
        async with app.run_test() as pilot:
            for _ in range(5):
                await pilot.pause()
                try:
                    await pilot.click("#close")
                    break
                except Exception:
                    pass

        assert app.dismissed is True

    @pytest.mark.asyncio
    async def test_escape_key_dismisses(self) -> None:
        """Test that pressing Escape dismisses the screen."""

        class TestApp(App):
            def __init__(self):
                super().__init__()
                self.dismissed = False

            def on_mount(self):
                screen = LoadErrorScreen(message="Test error")
                self.push_screen(screen, self.handle_dismiss)

            def handle_dismiss(self, value):
                self.dismissed = True
                self.exit()

        app = TestApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            await pilot.press("escape")
            await pilot.pause()

        assert app.dismissed is True

    @pytest.mark.asyncio
    async def test_q_key_dismisses(self) -> None:
        """Test that pressing 'q' dismisses the screen."""

        class TestApp(App):
            def __init__(self):
                super().__init__()
                self.dismissed = False

            def on_mount(self):
                screen = LoadErrorScreen(message="Test error")
                self.push_screen(screen, self.handle_dismiss)

            def handle_dismiss(self, value):
                self.dismissed = True
                self.exit()

        app = TestApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            await pilot.press("q")
            await pilot.pause()

        assert app.dismissed is True

    @pytest.mark.asyncio
    async def test_displays_error_message(self) -> None:
        """Test that the error message is stored and accessible."""
        error_msg = "Failed to load experiment: invalid config"

        class TestApp(App):
            def on_mount(self):
                screen = LoadErrorScreen(message=error_msg)
                self.push_screen(screen)

        app = TestApp()
        async with app.run_test() as pilot:
            await pilot.pause()

            # Check the screen has the message
            screen = app.screen
            assert screen._message == error_msg

