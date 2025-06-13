# src/callbacks/process_callbacks.py

from dash import Input, Output, callback

@callback(
    Output("terminal-output", "children"),  # Just to trigger the callback; can be no-update
    Input("process-step-btn", "n_clicks"),
    prevent_initial_call=True
)
def process_step(n_clicks):
    print("Hello")
    return f"Step {n_clicks} processed."  # D