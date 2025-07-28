CSS = """
#prepare-run-container {
    layout: vertical;
    width: 70%;
    height: auto;
    border: round $primary-darken-1;
    background: $panel-darken-1;
    align: center middle;
    box-sizing: border-box;
}

#modal-title {
    content-align: center middle;
    text-style: bold;
    color: $accent;
    margin-bottom: 1;
}

SelectionList {
    margin: 0 0 1 0;
    width: 100%;
}

#run-method {
    height: auto;
}

#delete-info {
    height: auto;
}

.button-row {
    align-horizontal: center;
    margin-top: 2;
    height: auto;
}

Button {
    width: auto;
    margin: 0 1;
}

Button:hover {
    background: $accent;
}

#run-feedback {
    height: 1;
    color: $text-muted;
}
"""