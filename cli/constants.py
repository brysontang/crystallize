"""Constants used across the CLI."""

from __future__ import annotations

from pathlib import Path

from crystallize.experiments.experiment import Experiment
from crystallize.experiments.experiment_graph import ExperimentGraph

OBJ_TYPES = {
    "experiment": Experiment,
    "graph": ExperimentGraph,
}

ASCII_ART = r"""
   *           *      _        _ _ *
   ___ _*__ _   _ ___| |_ __ *| | (_)_______ *
  * __| ' _| | | / *_| __/ _` | | | |_* / _ \
 | (__| |* | |_| \__ \ ||*(_| | * | |/ /  __/ *
  \___|_|   *__, |___/\__\__,_|_|_|_/___\___|
    *       |___/ *              *
"""

ASCII_ART_2 = r"""
 ▗▄▄▖▗▄▄▖▗▖  ▗▖▗▄▄▖▗▄▄▄▖▗▄▖ ▗▖   ▗▖   ▗▄▄▄▖▗▄▄▄▄▖▗▄▄▄▖
▐▌   ▐▌ ▐▌▝▚▞▘▐▌     █ ▐▌ ▐▌▐▌   ▐▌     █     ▗▞▘▐▌
▐▌   ▐▛▀▚▖ ▐▌  ▝▀▚▖  █ ▐▛▀▜▌▐▌   ▐▌     █   ▗▞▘  ▐▛▀▀▘
▝▚▄▄▖▐▌ ▐▌ ▐▌ ▗▄▄▞▘  █ ▐▌ ▐▌▐▙▄▄▖▐▙▄▄▖▗▄█▄▖▐▙▄▄▄▖▐▙▄▄▖
"""

ASCII_ART_3 = r"""
┌─┐┬─┐┬ ┬┌─┐┌┬┐┌─┐┬  ┬  ┬┌─┐┌─┐
│  ├┬┘└┬┘└─┐ │ ├─┤│  │  │┌─┘├┤
└─┘┴└─ ┴ └─┘ ┴ ┴ ┴┴─┘┴─┘┴└─┘└─┘
"""

ASCII_ART_4 = r"""
  ___  ____  _  _  ____  ____  __   __    __    __  ____  ____
 / __)(  _ \( \/ )/ ___)(_  _)/ _\ (  )  (  )  (  )(__  )(  __)
( (__  )   / )  / \___ \  )( /    \/ (_/\/ (_/\ )(  / _/  ) _)
 \___)(__\_)(__/  (____/ (__)\_/\_/\____/\____/(__)(____)(____)
"""

# ASCII_ART_ARRAY = [ASCII_ART, ASCII_ART_2, ASCII_ART_3, ASCII_ART_4]
ASCII_ART_ARRAY = [ASCII_ART]

CSS_PATH = str(Path(__file__).with_name("style") / "app.tcss")
