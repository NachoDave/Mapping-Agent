import math
from collections import deque

import networkx as nx
import osmnx as ox


def get_continuing_road_path(G, current_road_name: str, next_road_name: str,
                             current_node: str):
    """Find a simple continuation path from current road \
        to next road with a name change but no junction."""
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
                road_name = data.get('name')
                if (road_name == current_road_name or
                        road_name == next_road_name):
                    next_node = succ
                    break
            if next_node:
                break

        if not next_node:
            raise ValueError(f"Couldn't find continuation \
                from {current_road_name} to {next_road_name}")

        path.append(next_node)

        # Check if we've arrived on the next road
        edge_data = G.get_edge_data(node, next_node)
        for _, data in edge_data.items():
            if data.get('name') == next_road_name:
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
        if data.get('name') == road_name:
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
    x1 = shared_node['x'] - current_node['x']
    y1 = shared_node['y'] - current_node['y']
    x2 = neighbour_node['x'] - shared_node['x']
    y2 = neighbour_node['y'] - shared_node['y']

    # print(f'x1: {x1}, y1: {y1}' )
    # print(f'x2: {x2}, y2: {y2}' )

    angle1 = math.atan2(y1, x1)
    angle2 = math.atan2(y2, x2)

    # Signed angle difference
    angle_deg = math.degrees(angle1 - angle2)

    return angle_deg + 180


def get_turn_node(G, current_road_name: str, next_road_name: str, current_node: str, direction: str):
    """_summary_

    Args:
        G (_type_): _description_
        current_road_name (str): _description_
        next_road_name (str): _description_
        current_node (str): _description_
        direction (str): _description
    """
    # 1) Get the nodes on the current road
    curr_road_nodes = get_nodes_on_road(G, current_road_name)
    # 2) Get the nodes on the next road
    next_road_nodes = get_nodes_on_road(G, next_road_name)
    # 3) Find the nodes common to both to get junction nodes 
    junc_node = list(curr_road_nodes.intersection(next_road_nodes)) # get nodes in both roads
    if len(junc_node) == 1:
        junc_node = list(curr_road_nodes.intersection(next_road_nodes))[0]
    elif len(junc_node) > 1:
        # Check if the nodes have neighbours which are not shared
        next_node_not_shared = next_road_nodes.difference(set(junc_node))
        # check for nodes on next road not in current
        junc_node = {
            node for node in junc_node
            if len({
                n for n in G.neighbors(node)
                }.intersection(next_node_not_shared))
        }

        # Check if there is one node left, otherwise use networkx to get shortest distance
        if len(junc_node) == 1:
            junc_node = list(junc_node)[0]
        else:
            junc_node = min(
                junc_node, key=lambda node:
                nx.shortest_path_length(G, current_node, node, weight="length")
            )

    else:
        raise ValueError("No shared nodes between the two roads!")
    # 4) Get neighbours of common node
    junc_node_neighbours = [neighbour for neighbour in G.neighbors(junc_node) 
                            if (neighbour in next_road_nodes
                            and neighbour not in curr_road_nodes)]
    # 5) Get angles of the turns
    neigbour_angles = [
        turn_angle(
            G.nodes[current_node], G.nodes[junc_node],
            G.nodes[x]
        )
        for x in junc_node_neighbours
                       ]
    # 7) Select Neighbour node dependent on turn direction
    if direction == 'left':
        final_node = junc_node_neighbours[neigbour_angles.index(min(neigbour_angles))]
    elif direction == "right":
        final_node = junc_node_neighbours[neigbour_angles.index(max(neigbour_angles))]
    elif direction == "straight":
        junc_node_neighbours[min(enumerate([abs(180 - (n)) for n in neigbour_angles]), key=lambda x: x[1])[0]]
    else:
        pass  # may need to add this??
    # 7) Get the route from current node to final node
    current_node_to_junction_pth = nx.shortest_path(G, source=current_node, target=junc_node)
    junction_to_turn_pth = nx.shortest_path(G, junc_node, final_node)

    return current_node_to_junction_pth[:-1] + junction_to_turn_pth


def get_roundabout_path(G, current_road_name: str, next_road_name: str,
                        current_node: str, exit: int):
    """_summary_

    Args:
        G (_type_): _description_
        current_road_name (str): _description_
        next_road_name (str): _description_
        current_node (str): _description_
    """
    current_road_nodes = get_nodes_on_road(G, current_road_name) # get the nodes on the current road
    potential_roundabout_current_road_nodes = set()

    for node in current_road_nodes:  # loop through current road nodes
        for neighbour in G.successors(node):
            # get the neighbours of the current road nodes
            for _, edge_data in G.get_edge_data(node, neighbour).items():
                # get the edges of the current road nodes
                if edge_data.get('junction') == 'roundabout':
                    # check if any of the edges are roundabouts
                    potential_roundabout_current_road_nodes.add(node)
                    # append these edges to a list

    roundabout_nodes_dict = dict()

    # Look at the connected nodes to find the roundabout nodes
    for node in potential_roundabout_current_road_nodes:
        queue = [node] # intiate a queue
        visited = set([node])
        roundabout_nodes = [node]

        while queue:
            current_ra_node = queue.pop(0)
            for nd_ra in G.successors(current_ra_node):
                if nd_ra not in visited:
                    edge_ra_datas = G.get_edge_data(current_ra_node, nd_ra)
                    if edge_ra_datas:
                        for _, edge_ra_data in edge_ra_datas.items():
                            if edge_ra_data.get('junction') == 'roundabout':
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
    roundabout_exit_roads_dict = dict()
    for ra_key in unique_roundabouts:
        roundabout_exit_roads = dict()
        ra = unique_roundabouts[ra_key]
        for rb_nd in ra:
            for rb_nd_neighbour in G.successors(rb_nd):
                if rb_nd_neighbour not in ra:
                    rd_nb_edges = G.get_edge_data(rb_nd, rb_nd_neighbour)
                    for _, data in rd_nb_edges.items():
                        roundabout_exit_roads[rb_nd] = data.get('name')

            roundabout_exit_roads_dict[ra_key] = roundabout_exit_roads

    # Remove roundabouts that do not have any exits onto the road
    roundabout_exit_roads_dict = {
        k: v for k, v in roundabout_exit_roads_dict.items()
        if next_road_name in v.values()
    }

    # check that there is only one roundabout still left after filtering
    if len(roundabout_exit_roads_dict) > 1:
        raise ValueError("Multiple roundabouts after filtering")    

    if len(roundabout_exit_roads_dict) == 0:
        raise ValueError("No roundabouts found")

    # Get the most likely entrance node using shortest distance (this will be the path to the roundabout)
    roundabout_entrance_curr_node_nodes = {
        k: ox.shortest_path(G, current_node, k,  weight='length')
        for k, v in next(iter(roundabout_exit_roads_dict.values())).items()
        if v in current_road_name}

    roundabout_entrance_node, roundabout_entrance_path = min(
        roundabout_entrance_curr_node_nodes.items(),
        key=lambda item: len(item[1]))

    # Get the exit node from the exit number
    roundabout_nodes = list(next(iter(roundabout_exit_roads_dict.values())).keys())

    # Use deque to rotate the list so that entrance_node is first
    dq = deque(roundabout_nodes)

    while dq[0] != roundabout_entrance_node:
        dq.rotate(-1)  # Move elements left until entrance_node is at front

    roundabout_exit_node = dq[exit]

    # Get route between roundabout entrance and exit nodes
    roundabout_entrance_exit_path = ox.shortest_path(G, roundabout_entrance_node, roundabout_exit_node,  weight='length')

    # Get the final node on the road
    final_node = [nd for nd in G.successors(roundabout_exit_node) if nd not in roundabout_nodes]

    # check if there aren't multiple routes off the exit node
    if len(final_node) != 1:
        raise ValueError(f"Multiple nodes off exit node found from node: {
            roundabout_exit_node}")

    final_path = roundabout_entrance_path[:-1]
    + roundabout_entrance_exit_path + final_node

    # check if there are any nodes on the current road on roundabouts
    if not potential_roundabout_current_road_nodes:
        raise ValueError(f"Could not find any nodes connected \
            to roundabouts on the current road: {current_road_name}")

    return final_path
