CSS = """
#config-container {
    layout: vertical;
    width: 80%;
    height: auto;
    border: round $primary-darken-1;
    background: $panel-darken-1;
    padding: 2;
    align: center middle;
    box-sizing: border-box;
}

#edit-container {
    layout: vertical;
    width: 60%;
    height: auto;
    background: $panel-darken-1;
    padding: 2;
    align: center middle;
    box-sizing: border-box;
}

#modal-title {
    content-align: center middle;
    text-style: bold;
    color: $accent;
    margin-bottom: 1;
}

Input {
    border: tall $secondary;
    margin: 1 0;
    width: 100%;
}

Input:focus {
    border: tall $accent;
}

.button-row {
    height: auto;
    align-horizontal: right;
    margin-top: 1;
}

Button {
    width: auto;
    margin: 0 1;
}

Button:hover {
    background: $accent;
}
"""