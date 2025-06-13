# src/callbacks/process_callbacks.py

import os
import sys

from dash import Input, Output, State, callback

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from graph_data import G
from routing import (
    get_markers_and_polylines,
    tool_dict,
)


@callback(
    Output(
        "terminal-output", "children"
    ),  # Just to trigger the callback; can be no-update
    Output("route-layer", "children"),
    Output("route_nodes", "data"),
    Output("route_markers", "data"),
    Input("process-step-btn", "n_clicks"),
    State("directions-df", "data"),
    State("initial-node-input", "value"),
    prevent_initial_call=True,
)
def process_step(n_clicks, table_data, start_node):
    # Check if the data has been uploaded
    if n_clicks is None or not table_data:
        return "No data available.", []

    if start_node is None:
        return "No start node set", []

    markers = []
    polylines = []
    route_nodes = dict()
    # Call LLM model
    for dx in [2]:  # range(len(table_data)):
        # Call the model

        # Call the mapping function
        args = {
            "current_node": 23780711,
            "current_road_name": "Douglas Road",
            "direction": "left",
            "next_road_name": "Ewell Road",
        }
        tool = "get_turn_path"
        function_to_call = tool_dict.get(tool)  # .function.name)

        nodes = function_to_call(G=G, **args)  # run_tool(llm_response, tool_dict, G)
        
        # Add the nodes to the route nodes dict
        route_nodes[f'Step {dx + 1}'] = nodes

        # Make the new markers
        markers1, polylines1 = get_markers_and_polylines(
            G, nodes, edge_color="red" if dx % 2 else "green", step=dx + 1
        )

        markers = markers + markers1
        polylines = polylines + polylines1

    # Update map object

    return (
        f"Step {n_clicks} processed. Initial node is {start_node}",
        markers + polylines,
        route_nodes, markers + polylines
    )


# from dash import Input, Output, State, callback, no_update
