import ollama

from routing import (
    get_continuing_road_path,
    get_roundabout_path,
    get_turn_path,
)

INITIAL_PROMPT = """
You are a navigation decision assistant.

You are given:
- The **current road name** (e.g., "High Street"),
- The **next road name** (e.g., "Station Road"),
- The **current node**, which represents the current geographic position in the road graph (this is a node ID from a road network graph),
- A **natural language instruction** (e.g., "At roundabout take the second exit", "Continue straight", "Turn right at the junction").
- These instructions are written for human drivers, so may be extra information
    to aid them is not required by our tools, such as nearby landmarks and junction number. 
    You will need to filter these.

Your task is to:
1. Choose the correct function to call from the available tools:
   - `get_turn_path` for left or right turns at standard junctions, end of roads, at traffic lights or at mini-roundabouts. Remember, these instructions are written
        for drivers, so may include extra information such as landmarks. They will often contain the turn number, i.e., third left, 
        which tells the user which left turn to take relative to their current location. We don't need this information for the 
        functions, we only need the turn direction, the current road name and next road name.
   - `get_roundabout_path` for instructions involving roundabouts (e.g., "Roundabout 3rd exit", "RB left 2nd exit"). 
        Roundabout instructions will explicitly mention roundabout. Roundabout may be abbreviated (e.g., RB, R/bout). Instructions involving 
        mini-roundabouts should not use the `get_roundabout_path` function. Use `get_turn_path` instead. Roundabout instructions will refer 
        to the roundabout **exit** number (e.g. "third exit", "5th exit").
   - `get_continuing_road_path` when the road simply changes name but no actual turn occurs (e.g., "Continue onto Station Road").

2. Extract all required arguments from the instruction and road names:
    - Always include G as the first argument in every function call without explanation. 
    G is predefined. Never reason about G or check whether it is available—just pass G as the argument to G as is.
   - If the instruction mentions a turn, extract the direction ("left", "right", "straight").
   - If the instruction involves a roundabout, extract the exit number as an integer (e.g., "Take the 2nd exit" → 2).
   - Instructions may contain abbreviarations, for example "TL" or "T/L" means traffic lights, "EOR" means "end of road" and
    RB means roundabout. There may be other abbreviations not mentioned in this prompt.

3. Call exactly **one** of the tools with appropriate arguments.
   - Use the `current_node` as the starting point in all function calls.
   - If none of the tools are suitable, reply with a message explaining why and that the instruction requires human attention.

Be precise and cautious. Only call a function if you're confident it matches the instruction.
If the instruction is ambiguous, unsupported, or incomplete, do **not** guess — respond clearly that it can't be handled automatically.
"""


def run_llm(input: dict, prompt: str, tools: list, model_name: str = "qwen3:8b"):
    """_summary_

    Args:
        input (dict): _description_
        prompt (str): _description_
        model_name (_type_, optional): _description_. Defaults to "qwen3:8b".
    """

    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": 'Explain why you chose the tool, or chose no tool. Do not think'},
        {
            "role": "user",
            "content": (
                f"You are at node {input['current_node']} on {input['current_road']}.\n"
                f"The next road is {input['next_road']}.\n"
                f"The instruction is: '{input['instruction']}'."
            ),
        },
        
        #{"role": "system", "content": 'Do not think!'},
        
    ]

    try:
        response = ollama.chat(
            model=model_name,
            messages=messages,
            tools=tools,
            #think = False# This is where you pass the tool definitions
        )
        return response
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


if __name__ == "__main__":
    print("Hello")

    # G_tolworth = ox.graph_from_point((51.3829463, -0.2933327), dist=5000, network_type='drive')
    # print(get_nodes_on_road(G_tolworth, 'Ewell Road'))

    node1_2_input = {
        "current_node": "23780711",
        "current_road": "Douglas Road",
        "next_road": "Ewell Road",
        "instruction": "Take the second left",
    }

    llm_response = run_llm(
        input=node1_2_input,
        prompt=INITIAL_PROMPT,
        tools=[get_continuing_road_path, get_turn_path, get_roundabout_path],
    )

    print(llm_response)
