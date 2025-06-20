import math
from collections import deque

import dash_leaflet as dl
import networkx as nx
import osmnx as ox


def get_continuing_road_path(
    G, current_road_name: str, next_road_name: str, current_node: int
):
    """
    Finds the next node along a continuous path where the road changes name without an actual turn.

    This function is used in cases where the current road flows directly into another road
    with a different name (e.g., "becomes") and no significant
    intersection or turn is involved. It identifies the natural continuation of the current
    trajectory within the road network graph.

    Args:
        G (networkx.MultiDiGraph): The road network graph, typically from OSMNX.
        current_road_name (str): The name of the current road being traveled.
        next_road_name (str): The name of the road that the current road continues into.
        current_node (str or int): The current node ID within the road network graph.

    Returns:
        list: A list of the nodes IDs from the current node to the first node on the road after change of name.

    Raises:
        ValueError: If a continuation path matching the new road name cannot be found.
        TypeError: If any of the inputs are of invalid type or structure.

    Example:
        >>> get_continuing_road_path(G, "Main Street", "Broadway", 456789)
        [456789, 456790, 334561, 1220001]
    """

    current_node = int(current_node)

    visited = set()
    path = [current_node]

    while True:
        node = path[-1]
        visited.add(node)
        successors = [n for n in G.successors(node) if n not in visited]
        if not successors:
            raise ValueError("No further successors from current node")

        next_node = None
        for succ in successors:
            edge_data = G.get_edge_data(node, succ)
            for _, data in edge_data.items():
                road_name = data.get("name")
                if (current_road_name in road_name) or (next_road_name in road_name):
                    next_node = succ
                    break
            if next_node:
                break

        if not next_node:
            raise ValueError(
                f"Couldn't find continuation \
                from {current_road_name} to {next_road_name}"
            )

        path.append(next_node)

        # Check if we've arrived on the next road
        edge_data = G.get_edge_data(node, next_node)
        for _, data in edge_data.items():
            if data.get("name") == next_road_name:
                return path


def get_nodes_on_road(G, road_name: str) -> set:
    """_summary_
    Given a collection of nodes via a
    networkx.classes.multidigraph.MultiDiGraph find
    all of the nodes on a given road

    Args:
        G (OSMNX digraph): Collection of nodes to investigate
        road_name (str): Road name

    Returns:
        set: set of all osmnx nodes on a road
    """
    nodes = set()
    for u, v, data in G.edges(data=True):
        # u is the start node, v is the edge node, data is edge data
        if data.get("name") == road_name:
            nodes.add(u)
            nodes.add(v)
    return nodes


# Function to get the angle of turn nodes
def turn_angle(current_node: dict, shared_node: dict, neighbour_node: dict):
    """_summary_

    Args:
        current_node (dict): _description_
        shared_node (dict): _description_
        neighbour_node (dict): _description_

    Returns:
        _type_: _description_
    """
    x1 = shared_node["x"] - current_node["x"]
    y1 = shared_node["y"] - current_node["y"]
    x2 = neighbour_node["x"] - shared_node["x"]
    y2 = neighbour_node["y"] - shared_node["y"]

    # print(f'x1: {x1}, y1: {y1}' )
    # print(f'x2: {x2}, y2: {y2}' )

    angle1 = math.atan2(y1, x1)
    angle2 = math.atan2(y2, x2)

    # Signed angle difference
    angle_deg = math.degrees(angle1 - angle2)

    return angle_deg + 180


def get_turn_path(
    G, current_road_name: str, next_road_name: str, current_node: int, direction: str
):
    """
    Determines the OSMNX nodes in the path from the users current node on their current road to the node after the
    junction that the user is turning onto

    Args:
        G (networkx.MultiDiGraph): The road network graph from OSMNX.
        current_road_name (str): The name of the road that the user is currently on.
        next_road_name (str): The name of the road that the user is turning on to.
        current_node (str): The ID of the current node (as a string).
        direction (str): Direction of the turn (will be one of, "left", "right", "straight").

    Returns:
        list: list of the nodes IDs from the current node to the first node on the next road after the junction.

    Example:
        >>> get_turn_path(G, "High Street", "Elm Road", 123456, left)
        [123456, 123789, 23374, 1505050]
    """
    
    current_node = int(current_node)
    
    # 1) Get the nodes on the current road
    curr_road_nodes = get_nodes_on_road(G, current_road_name)
    # 2) Get the nodes on the next road
    next_road_nodes = get_nodes_on_road(G, next_road_name)
    # 3) Find the nodes common to both to get junction nodes
    junc_node = list(
        curr_road_nodes.intersection(next_road_nodes)
    )  # get nodes in both roads
    if len(junc_node) == 1:
        junc_node = list(curr_road_nodes.intersection(next_road_nodes))[0]
    elif len(junc_node) > 1:
        # Check if the nodes have neighbours which are not shared
        next_node_not_shared = next_road_nodes.difference(set(junc_node))
        # check for nodes on next road not in current
        junc_node = {
            node
            for node in junc_node
            if len({n for n in G.neighbors(node)}.intersection(next_node_not_shared))
        }

        # Check if there is one node left, otherwise use networkx to get shortest distance
        if len(junc_node) == 1:
            junc_node = list(junc_node)[0]
        else:
            junc_node = min(
                junc_node,
                key=lambda node: nx.shortest_path_length(
                    G, current_node, node, weight="length"
                ),
            )

    else:
        raise ValueError("No shared nodes between the two roads!")
    # 4) Get neighbours of common node
    junc_node_neighbours = [
        neighbour
        for neighbour in G.neighbors(junc_node)
        if (neighbour in next_road_nodes and neighbour not in curr_road_nodes)
    ]
    # 5) Get angles of the turns
    neigbour_angles = [
        turn_angle(G.nodes[current_node], G.nodes[junc_node], G.nodes[x])
        for x in junc_node_neighbours
    ]
    # 7) Select Neighbour node dependent on turn direction
    if direction == "left":
        final_node = junc_node_neighbours[neigbour_angles.index(min(neigbour_angles))]
    elif direction == "right":
        final_node = junc_node_neighbours[neigbour_angles.index(max(neigbour_angles))]
    elif direction == "straight":
        junc_node_neighbours[
            min(
                enumerate([abs(180 - (n)) for n in neigbour_angles]), key=lambda x: x[1]
            )[0]
        ]
    else:
        pass  # may need to add this??
    # 7) Get the route from current node to final node
    current_node_to_junction_pth = nx.shortest_path(
        G, source=current_node, target=junc_node
    )
    junction_to_turn_pth = nx.shortest_path(G, junc_node, final_node)

    return current_node_to_junction_pth[:-1] + junction_to_turn_pth


def get_roundabout_path(
    G, current_road_name: str, next_road_name: str, current_node: int, exit: int
):
    """
    Determines the OSMNX nodes in the path from the users current node on their current road to the node after a
    a roundabout exit that the user is turning onto

    This function navigates the road network graph starting from the current node,
    identifying roundabout structures, and determining the correct exit to take
    based on the given natural language instruction.

    Args:
        G (networkx.MultiDiGraph): The road network graph, typically from OSMNX.
        current_road_name (str): The name of the current road before entering the roundabout.
        next_road_name (str): The name of the road to exit onto after the roundabout.
        current_node (str or int): The node ID in the graph where the vehicle currently is.
        exit (int): The exit number to take from the roundabout (e.g., 1 for first exit, 2 for second).

    Returns:
        list: A list of the node IDs on the path from the current node to the first node on the next road after the roundabout.

    Raises:
        ValueError: If a suitable roundabout or exit path cannot be found.
        TypeError: If any of the input types are incorrect or inconsistent with the graph.

    Example:
        >>> get_roundabout_path(G, "High Street", "Elm Road", 123456, 2)
        [123456, 123789, 23374, 1505050]
    """
    
    current_node = int(current_node)

    current_road_nodes = get_nodes_on_road(G, current_road_name)
    # get the nodes on the current road
    potential_roundabout_current_road_nodes = set()

    for node in current_road_nodes:  # loop through current road nodes
        for neighbour in G.successors(node):
            # get the neighbours of the current road nodes
            for _, edge_data in G.get_edge_data(node, neighbour).items():
                # get the edges of the current road nodes
                if edge_data.get("junction") == "roundabout":
                    # check if any of the edges are roundabouts
                    potential_roundabout_current_road_nodes.add(node)
                    # append these edges to a list

    roundabout_nodes_dict = dict()

    # Look at the connected nodes to find the roundabout nodes
    for node in potential_roundabout_current_road_nodes:
        queue = [node]  # intiate a queue
        visited = set([node])
        roundabout_nodes = [node]

        while queue:
            current_ra_node = queue.pop(0)
            for nd_ra in G.successors(current_ra_node):
                if nd_ra not in visited:
                    edge_ra_datas = G.get_edge_data(current_ra_node, nd_ra)
                    if edge_ra_datas:
                        for _, edge_ra_data in edge_ra_datas.items():
                            if edge_ra_data.get("junction") == "roundabout":
                                queue.append(nd_ra)
                                visited.add(nd_ra)
                                roundabout_nodes.append(nd_ra)

        roundabout_nodes_dict[node] = roundabout_nodes

    # Check for duplicated roundabouts
    unique_roundabouts = {}
    seen = set()
    for entry_node, nodes in roundabout_nodes_dict.items():
        frozen = frozenset(nodes)
        if frozen not in seen:
            seen.add(frozen)
            unique_roundabouts[entry_node] = nodes

    # Get the road names for each exit node
    roundabout_entrance_roads_dict = dict()
    for ra_key in unique_roundabouts:
        roundabout_entrance_roads = dict()
        ra = unique_roundabouts[ra_key]
        for rb_nd in ra:
            for rb_nd_neighbour in G.predecessors(rb_nd):
                if rb_nd_neighbour not in ra:
                    rd_nb_edges = G.get_edge_data(rb_nd_neighbour, rb_nd)
                    for _, data in rd_nb_edges.items():
                        roundabout_entrance_roads[rb_nd] = data.get("name")

            roundabout_entrance_roads_dict[ra_key] = roundabout_entrance_roads

    # Remove roundabouts that do not have any entrances from current road
    roundabout_entrance_roads_dict = {
        k: v
        for k, v in roundabout_entrance_roads_dict.items()
        if next_road_name in v.values()
    }

    # Get the road names for each exit node
    roundabout_exit_roads_dict = dict()
    for ra_key in unique_roundabouts:
        roundabout_exit_roads = dict()
        ra = unique_roundabouts[ra_key]
        for rb_nd in ra:
            for rb_nd_neighbour in G.successors(rb_nd):
                if rb_nd_neighbour not in ra:
                    rd_nb_edges = G.get_edge_data(rb_nd, rb_nd_neighbour)
                    for _, data in rd_nb_edges.items():
                        roundabout_exit_roads[rb_nd] = data.get("name")

            roundabout_exit_roads_dict[ra_key] = roundabout_exit_roads

    # Remove roundabouts that do not have any exits onto the road
    roundabout_exit_roads_dict = {
        k: v
        for k, v in roundabout_exit_roads_dict.items()
        if next_road_name in v.values()
    }

    # check that there is only one roundabout still left after filtering
    if len(roundabout_exit_roads_dict) > 1:
        raise ValueError("Multiple roundabouts after filtering")

    if len(roundabout_exit_roads_dict) == 0:
        raise ValueError("No roundabouts found")

    # Get the most likely entrance node using shortest distance (this will be the path to the roundabout)
    roundabout_entrance_curr_node_nodes = {
        k: ox.shortest_path(G, current_node, k, weight="length")
        for k, v in next(iter(roundabout_entrance_roads_dict.values())).items()
        if v in current_road_name
    }

    roundabout_entrance_node, roundabout_entrance_path = min(
        roundabout_entrance_curr_node_nodes.items(), key=lambda item: len(item[1])
    )

    # Get the exit node from the exit number
    roundabout_nodes = next(iter(unique_roundabouts.values()))

    # Use deque to rotate the list so that entrance_node is first
    dq = deque(roundabout_nodes)

    while dq[0] != roundabout_entrance_node:
        dq.rotate(-1)  # Move elements left until entrance_node is at front

    ordered_exit_roads = [k for k in dq if k in roundabout_exit_roads]
    ordered_exit_roads = [x for x in ordered_exit_roads if x != roundabout_entrance_node]

    roundabout_exit_node = ordered_exit_roads[exit - 1]

    # Get route between roundabout entrance and exit nodes
    roundabout_entrance_exit_path = ox.shortest_path(
        G, roundabout_entrance_node, roundabout_exit_node, weight="length"
    )

    # Get the final node on the road
    final_node = [
        nd for nd in G.successors(roundabout_exit_node) if nd not in roundabout_nodes
    ]

    # check if there aren't multiple routes off the exit node
    if len(final_node) != 1:
        raise ValueError(
            f"Multiple nodes off exit node found from node: {roundabout_exit_node}"
        )

    final_path = roundabout_entrance_path[:-1] + roundabout_entrance_exit_path + final_node

    # check if there are any nodes on the current road on roundabouts
    if not potential_roundabout_current_road_nodes:
        raise ValueError(
            f"Could not find any nodes connected \
            to roundabouts on the current road: {current_road_name}"
        )

    return final_path


def get_markers_and_polylines(G, nodes, step, edge_color = 'red'):
    ## Get markers
    node_dict = {node: G.nodes[node] for node in nodes}
    
    markers = []

    for i, node in enumerate(node_dict.keys()):
        lat, lon = node_dict[node]["y"], node_dict[node]["x"]

        # Only add tooltip to the first node
        if i == 0:
            tooltip = dl.Tooltip(
                f"Step: {step}",
                direction="left",
                offset=[-20, 0],
                permanent=True
            )
            marker = dl.Marker(position=(lat, lon), children=[tooltip])
        else:
            marker = dl.Marker(position=(lat, lon))

        markers.append(marker)
    
    # markers = [
    # dl.Marker(position=(node_dict[dx]['y'], node_dict[dx]['x']),
    #           children=[#dl.Tooltip(f'Step: {step}, ID: {dx}, x: {node_dict[dx]['x']}, y: {node_dict[dx]['y']}'),
    #                     dl.Tooltip(f'Step: {step}', direction="left", offset=[-20, 0], permanent=True)
    #                     ])
    # for dx in node_dict.keys()
    # ]
    
    ## Get polylines
    edges = [G.get_edge_data(nodes[u], nodes[u + 1])[0] for u in range(len(nodes) - 1)]

    edge_lines = []

    for idx, data in  zip(range(len(edges)), edges):
        # Some edges have multiple geometries (from OSM), handle those first
        if 'geometry' in data:
            # If geometry is a LineString, extract lat/lon pairs
            coords = [(point[1], point[0]) for point in data['geometry'].coords]
        else:
            #Otherwise use straight line between nodes
            coords = [
                markers[idx].position, 
                markers[idx + 1].position
            ]
        
        edge_lines.append(dl.Polyline(positions=coords, color=edge_color, weight=3))

    return markers, edge_lines


tool_dict = {
    "get_continuing_road_path": get_continuing_road_path,
    "get_turn_path": get_turn_path,
    "get_roundabout_path": get_roundabout_path,
}


def run_tool(response, tool_dict: dict, G):
    """_summary_

    Args:
        response (_type_): _description_
        tool_dict (dict): _description_
    """
    tool = response.message.tool_calls[0]
    function_to_call = tool_dict.get(tool.function.name)
    if function_to_call:
        print(f"Function output: {tool.function.name}, args = {tool.function.arguments}")
        args = tool.function.arguments
        args.pop('G')
        
        return function_to_call(G = G, **args)
    else:
        print("Function not found:", tool.function.name)


if __name__ == "__main__":
    import os
    import sys

    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

    from src.llm_agent import INITIAL_PROMPT, run_llm

    print("Hello")

    G = ox.graph_from_point((51.3829463, -0.2933327), dist=5000, network_type='drive')
    # print(get_nodes_on_road(G_tolworth, 'Ewell Road'))
    
    print(get_continuing_road_path(
    G, current_road_name = 'Balaclava Road', next_road_name = "Saint Mary's Road", current_node = 1397397612
))
    
    #print(get_roundabout_path(G, 'Kingsdowne Road', 'Upper Brighton Road', 1736768194, 3))
    #print(get_roundabout_path(G, 'Balaclava Road', 'Balaclava Road', 1955602497, 1))
    #print(get_roundabout_path(G, 'Balaclava Road', 'Chadwick Place', 1955602497, 2))
    # node1_2_input = {
    #     "current_node": "23780711",
    #     "current_road": "Douglas Road",
    #     "next_road": "Ewell Road",
    #     "instruction": "Take the second left",
    # }

    # llm_response = run_llm(
    #     input=node1_2_input,
    #     prompt=INITIAL_PROMPT,
    #     tools=[get_continuing_road_path, get_turn_path, get_roundabout_path],
    # )

    # func_out = run_tool(llm_response, tool_dict, G)
