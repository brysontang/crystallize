"""Constants used across the CLI."""

from __future__ import annotations

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

CSS = """
App {
    background: $background;
}

Header {
    content-align: center middle;
}

Static#title {
    content-align: center middle;
    text-style: bold;
    color: $primary;
}

ListView {
    background: $panel;
    border: tall $secondary;
    height: 1fr;
}

ListItem {
    padding: 1;
}

ListItem > Static {
    color: $text;
}

ListItem:hover {
    background: $accent;
}

ListItem.selected {
    background: $success;
}

.experiment-item > Static {
}

.graph-item > Static {
    text-style: bold italic;
}

ModalScreen {
    background: $background 50%;
    align: center middle;
}

.confirm-delete-container {
    width: 80%;
    height: auto;
    max-height: 80%;
    border: round $error;
    background: $panel;
    padding: 1;
}

.create-exp-container {
    width: 60%;
    height: auto;
    border: round $primary;
    background: $panel;
    padding: 1;
}

.path-list {
    background: $surface;
    border: round $primary;
    margin: 1 0;
    padding: 1;
    height: auto;
    max-height: 10; /* Makes the list scrollable if it's long */
}

SelectionList {
    height: 1fr;
    width: 100%;
}

#dag-display {
    height: auto;
    border: round $primary;
    padding: 0 1;
}

#output-tabs {
    margin-top: 1;
}

RichLog {
    height: 1fr;
    width: 100%;
    background: $panel;
    border: tall $secondary;
}

Button {
    margin: 1 0;
}

Button#confirm {
    background: $error;
}

Button#yes {
    background: $success;
}

Button#no {
    background: $error;
}

.button-row {
    align-horizontal: center;
}

LoadingIndicator {
    color: $accent;
}

#main-container {
    layout: vertical;
    padding: 1;
}

.left-panel {
    width: 50%;
    height: 1fr;
    border-right: solid $secondary;
    padding-right: 1;
}

.right-panel {
    width: 50%;
    padding-left: 1;
    height: 1fr;

}

.details-panel {
    background: $panel-darken-1;
    border: round $secondary;
    padding: 1;
    height: auto;
    content-align: left top;
    overflow: auto;
}
#config-widget {
    background: $panel-darken-1;
    border: round $secondary;
    padding: 1;
    height: 1fr;
    content-align: left top;
    overflow: auto;
}


TabbedContent {
    height: 1fr;
}

TabPane {
    height: 1fr;
    padding: 1;
}

ListView {
    border: solid $secondary;
    height: 1fr;
}

ListItem {
    padding: 1;
    layout: vertical;
}

.item-doc {
    color: $text-muted;
}

ListItem:hover {
    background: $accent-lighten-1;
}

.experiment-item:hover, .graph-item:hover {
    background: $accent-lighten-1;
}

#error-msg {
    color: $error;
    margin-top: 1;
}

Input {
    border: tall $secondary;
    margin-bottom: 1;
    width: 100%;
}


Input:focus {
    border: tall $accent;
}

.invisible {
    display: none;
}

#button-container {
    height: auto;
    layout: horizontal;
    margin: 1 0;
    align-vertical: middle;
}

#select-button-container {
    height: auto;
    layout: horizontal;
    align-vertical: middle;
}

#run-btn {
    align-vertical: middle;
    margin-top: 0;
}
"""
