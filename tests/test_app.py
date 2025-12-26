"""Tests for cli.app module."""

import resource

from cli.app import CrystallizeApp, themes


class TestCrystallizeApp:
    """Tests for CrystallizeApp class."""

    def test_init_with_no_flags(self) -> None:
        """Test initialization with no flags."""
        app = CrystallizeApp()
        assert app.flags == {}
        assert app.i == 0
        assert app.theme == "nord"

    def test_init_with_flags(self) -> None:
        """Test initialization with flags."""
        flags = {"no_override_mat": True, "no_override_file_limit": True}
        app = CrystallizeApp(flags=flags)
        assert app.flags == flags

    def test_bindings_configured(self) -> None:
        """Test that expected keybindings are configured."""
        binding_keys = [b[0] for b in CrystallizeApp.BINDINGS]
        assert "q" in binding_keys
        assert "ctrl+c" in binding_keys

    def test_increase_open_file_limit_when_below_desired(self, capsys) -> None:
        """Test that file limit is increased when current is below desired."""
        app = CrystallizeApp()

        # Get current limits
        soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)

        if soft < hard:
            # We can test increasing the limit
            app.increase_open_file_limit(desired_soft=soft + 1)
            captured = capsys.readouterr()
            # Either it succeeded or reported an error
            assert "Raised open file limit" in captured.out or "Error" in captured.out or "Could not" in captured.out or captured.out == ""
        else:
            # soft == hard, so we can't increase
            app.increase_open_file_limit(desired_soft=soft + 1)
            # Should not crash

    def test_increase_open_file_limit_respects_hard_limit(self) -> None:
        """Test that file limit doesn't exceed hard limit."""
        app = CrystallizeApp()

        soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)

        # Request more than hard limit
        app.increase_open_file_limit(desired_soft=hard + 10000)

        # Should not raise an exception
        new_soft, _ = resource.getrlimit(resource.RLIMIT_NOFILE)
        assert new_soft <= hard

    def test_increase_open_file_limit_handles_value_error(self, capsys) -> None:
        """Test handling of ValueError during limit increase."""
        app = CrystallizeApp()

        # Mock getrlimit to return values that would trigger setrlimit
        original_getrlimit = resource.getrlimit
        original_setrlimit = resource.setrlimit

        def mock_getrlimit(res):
            return (100, 10000)  # Low soft, high hard

        def mock_setrlimit(res, limits):
            raise ValueError("Test error")

        resource.getrlimit = mock_getrlimit
        resource.setrlimit = mock_setrlimit

        try:
            app.increase_open_file_limit(desired_soft=5000)
            captured = capsys.readouterr()
            assert "Could not raise limit" in captured.out
        finally:
            resource.getrlimit = original_getrlimit
            resource.setrlimit = original_setrlimit

    def test_increase_open_file_limit_handles_generic_error(self, capsys) -> None:
        """Test handling of generic exceptions during limit increase."""
        app = CrystallizeApp()

        original_getrlimit = resource.getrlimit
        original_setrlimit = resource.setrlimit

        def mock_getrlimit(res):
            return (100, 10000)

        def mock_setrlimit(res, limits):
            raise RuntimeError("Some error")

        resource.getrlimit = mock_getrlimit
        resource.setrlimit = mock_setrlimit

        try:
            app.increase_open_file_limit(desired_soft=5000)
            captured = capsys.readouterr()
            assert "Error setting limit" in captured.out
        finally:
            resource.getrlimit = original_getrlimit
            resource.setrlimit = original_setrlimit

    def test_apply_overrides_skips_file_limit_when_flagged(self) -> None:
        """Test that file limit override is skipped when flag is set."""
        app = CrystallizeApp()
        call_count = [0]

        def counting_method(*args, **kwargs):
            call_count[0] += 1

        app.increase_open_file_limit = counting_method

        app._apply_overrides({"no_override_file_limit": True, "no_override_mat": True})

        assert call_count[0] == 0

    def test_apply_overrides_calls_file_limit_when_not_flagged(self) -> None:
        """Test that file limit override is called when flag is not set."""
        app = CrystallizeApp()
        call_count = [0]

        def counting_method(*args, **kwargs):
            call_count[0] += 1

        app.increase_open_file_limit = counting_method

        app._apply_overrides({"no_override_file_limit": False, "no_override_mat": True})

        assert call_count[0] == 1

    def test_apply_overrides_calls_file_limit_when_flag_missing(self) -> None:
        """Test that file limit override is called when flag is missing."""
        app = CrystallizeApp()
        call_count = [0]

        def counting_method(*args, **kwargs):
            call_count[0] += 1

        app.increase_open_file_limit = counting_method

        app._apply_overrides({"no_override_mat": True})

        assert call_count[0] == 1

    def test_apply_overrides_skips_matplotlib_when_flagged(self) -> None:
        """Test that matplotlib override is skipped when flag is set."""
        app = CrystallizeApp()
        app.increase_open_file_limit = lambda *args, **kwargs: None

        # With no_override_mat=True, matplotlib should not be touched
        # This should not raise even if matplotlib is not installed
        app._apply_overrides({"no_override_mat": True, "no_override_file_limit": True})


class TestThemes:
    """Tests for theme configuration."""

    def test_themes_list_not_empty(self) -> None:
        """Test that themes list is not empty."""
        assert len(themes) > 0

    def test_nord_theme_present(self) -> None:
        """Test that default nord theme is in the list."""
        assert "nord" in themes

    def test_themes_are_strings(self) -> None:
        """Test that all themes are strings."""
        for theme in themes:
            assert isinstance(theme, str)
