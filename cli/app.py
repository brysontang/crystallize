from __future__ import annotations

import argparse
import os
import resource
import logging
import yaml
import dotenv

dotenv.load_dotenv()


from textual.app import App

from .constants import CSS
from .discovery import _import_module, _run_object, discover_objects
from .utils import _build_experiment_table, _write_experiment_summary, _write_summary
from .screens.selection import SelectionScreen

themes = [
    "nord",
    "textual-dark",
    "textual-light",
    "gruvbox",
    "catppuccin-mocha",
    "textual-ansi",
    "dracula",
    "tokyo-night",
    "monokai",
    "flexoki",
    "catppuccin-latte",
    "solarized-light",
]

# Export these for backward compatibility
__all__ = [
    "CrystallizeApp",
    "run",
    "_import_module",
    "discover_objects",
    "_run_object",
    "_build_experiment_table",
    "_write_experiment_summary",
    "_write_summary",
]


class CrystallizeApp(App):
    """Textual application for running crystallize objects."""

    CSS = CSS

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("ctrl+c", "quit", "Quit"),
        # ("[", "toggle_theme_prev", "Previous Theme"),
        # ("]", "toggle_theme_next", "Next Theme"),
    ]

    def __init__(self, flags: dict = None, **kwargs):
        super().__init__(**kwargs)
        self.flags = flags or {}
        self.i = 0
        self.theme = "nord"

    def on_mount(self) -> None:

        self._apply_overrides(self.flags)
        self.push_screen(SelectionScreen())

    def _apply_overrides(self, flags: dict):
        if not flags.get("no_override_file_limit", False):
            self.increase_open_file_limit()

        if not flags.get("no_override_mat", False):
            import matplotlib

            current_backend = matplotlib.get_backend()
            if current_backend != "Agg":
                try:
                    matplotlib.use("Agg")
                    logging.getLogger("crystallize.cli").info(
                        f"Switched Matplotlib backend from '{current_backend}' to 'Agg'."
                    )
                except Exception as exc:  # pragma: no cover - backend failures are environment-specific
                    logging.getLogger("crystallize.cli").warning(
                        f"Could not switch Matplotlib backend: {exc}"
                    )

    def increase_open_file_limit(self, desired_soft=10240):
        """Raise soft open file limit programmatically."""
        try:
            soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
            new_soft = min(desired_soft, hard)
            if new_soft > soft:
                resource.setrlimit(resource.RLIMIT_NOFILE, (new_soft, hard))
                print(f"Raised open file limit: {soft} -> {new_soft} (hard: {hard})")
        except ValueError as e:
            print(f"Could not raise limit (hard too low?): {e}. Using {soft}.")
        except Exception as e:
            print(f"Error setting limit: {e}")

    # def action_toggle_theme_next(self) -> None:
    #     self.i += 1
    #     num_themes = len(themes)
    #     self.theme = themes[self.i % num_themes]

    # def action_toggle_theme_prev(self) -> None:
    #     self.i -= 1
    #     num_themes = len(themes)
    #     self.theme = themes[self.i % num_themes]


def run() -> None:
    parser = argparse.ArgumentParser(description="Crystallize Framework CLI")
    parser.add_argument(
        "--no-override-mat",
        action="store_true",
        help="Disable forcing Matplotlib 'Agg' backend.",
    )
    parser.add_argument(
        "--no-override-file-limit",
        action="store_true",
        help="Disable auto-raising open file limit.",
    )

    args = parser.parse_args()
    flags = vars(args)

    # Load optional config.yaml (overrides defaults, but CLI flags win)
    config_path = "config.yaml"  # Or ~/.crystallize/config.yaml for global
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            config = yaml.safe_load(f) or {}
        # Merge: Config sets if not in flags
        for key in ["no_override_mat", "no_override_file_limit"]:
            if key not in flags and key in config:
                flags[key] = config[key]

    import sys

    if "--serve" in sys.argv:
        from textual_serve.server import Server

        server = Server("crystallize")
        server.serve()
        return

    app = CrystallizeApp(flags=flags)
    app.run()
