# src/callbacks/process_callbacks.py

from dash import Input, Output, State, callback


@callback(
    Output("terminal-output", "children"),  # Just to trigger the callback; can be no-update
    Input("process-step-btn", "n_clicks"),
    State("directions-df", "data"),
    State("initial-node-input", "value"),
    prevent_initial_call=True
)
def process_step(n_clicks, table_data, start_node):
    # Check if the data has been uploaded
    if n_clicks is None or not table_data:
        return "No data available."
    
        
    # Call LLM model
    
    
    # Call the mapping function
    
    
    # Update map object
    
    return f"Step {n_clicks} processed. Initial node is {start_node}"  # D

# from dash import Input, Output, State, callback, no_update

# @callback(
#     Output("directions-df", "data"),
#     Output("terminal-output", "children"),
#     Input("process-step-btn", "n_clicks"),
#     State("directions-df", "data"),
#     prevent_initial_call=True
# )
# def process_step(n_clicks, table_data):
#     if n_clicks is None or not table_data:
#         return no_update, "No data available."

#     step_idx = n_clicks - 1
#     if step_idx >= len(table_data):
#         return no_update, "All steps processed."

#     table_data[step_idx]["Tool Call"] = f"LLM call for step {step_idx + 1}"

#     return table_data, f"> Processed step {step_idx + 1}"