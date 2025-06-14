# src/callbacks/process_callbacks.py

import os
import sys

from dash import Input, Output, State, callback

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from graph_data import G
from routing import (
    get_continuing_road_path,
    get_markers_and_polylines,
    get_roundabout_path,
    get_turn_path,
    run_tool,
    tool_dict,
)
from src.llm_agent import INITIAL_PROMPT, run_llm


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
        return "No data available.", [], [], []

    if start_node is None:
        return "No start node set", [], [], []

    markers = []
    polylines = []
    route_nodes = dict()
    cli_msg = ""
    # Call LLM model
    for dx, row in enumerate(table_data):
        print(f"In step {dx}")
        #row = table_data[dx]
        # Populate the node input from the data table
        node_input = {
            "current_node": start_node,
            "current_road": row["Current Road"],
            "next_road": row["Next Road"],
            "instruction": row["Instruction"],
        }
        # Call the model
        llm_response = run_llm(
            input=node_input,
            prompt=INITIAL_PROMPT,
            tools=[get_continuing_road_path, get_turn_path, get_roundabout_path],
            model_name='qwen3:8b'
        )
        
        cli_msg = cli_msg + (f"************* Step {dx + 1} ************* \n\n")
        cli_msg = cli_msg + (
            f"Input: Current Road: {row['Current Road']}, Next Road: {row['Next Road']}, Instruction: {row['Instruction']}, Start Node: {start_node}\n\n"
        )

        if llm_response.message.tool_calls:
            try:
                nodes = run_tool(llm_response, tool_dict, G)
            except ValueError as e:
                cli_msg = cli_msg + f"LLM Message: {llm_response.message.content} \n\n"
                cli_msg - cli_msg + e
                print(f"Caught value error {e}")
                return cli_msg, [], [], []
                
        else:
            print("No tool call")
            cli_msg = cli_msg + f"LLM Message: {llm_response.message.content} \n\n"
            return cli_msg, [], [], []

        # nodes = function_to_call(G=G, **args)  # run_tool(llm_response, tool_dict, G)

        # Add the nodes to the route nodes dict
        route_nodes[f"Step {dx + 1}"] = nodes

        # Make the new markers
        markers1, polylines1 = get_markers_and_polylines(
            G, nodes, edge_color="red" if dx % 2 else "blue", step=dx + 1
        )

        markers = markers + markers1
        polylines = polylines + polylines1

        # Populate the terminal string

        cli_msg = (
            cli_msg
            + f"Function called: {llm_response.message.tool_calls[0].function.name}, Args: {llm_response.message.tool_calls[0].function.arguments} \n\n"
        )
        cli_msg = cli_msg + f"LLM Message: {llm_response.message.content} \n\n"

        start_node = nodes[-1]

    return (
        # f"Step {n_clicks} processed. Initial node is {start_node}",
        cli_msg,
        markers + polylines,
        route_nodes,
        markers + polylines,
    )


# from dash import Input, Output, State, callback, no_update
