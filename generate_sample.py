import json
import random
from pathlib import Path 

def load_config(config_path):
    with open(config_path) as f:
        return json.load(f)


def generate_sample(config, i):
    #Name
    sample = {}
    sample["scenario"] = f"scenario_{i}"

    #Closed Roads
    road_groups = config["closed_roads"]

    normalized_groups = []
    for group in road_groups:
        if isinstance(group, list):
            normalized_groups.append(group)
        else:
            normalized_groups.append([group])

    max_roads = config["sampling"]["max_closed_roads"]

    if len(normalized_groups) == 0:
        num_groups = 0
    else:
        max_possible = min(max_roads, len(normalized_groups))
        num_groups = random.randint(1, max_possible)

    if num_groups == 0:
        sample["closed_roads"] = []
    else:
        selected_groups = random.sample(normalized_groups, num_groups)

        closed_edges = []
        for group in selected_groups:
            closed_edges.extend(group)

        sample["closed_roads"] = closed_edges

    #traffic multiplier
    traffic = config.get("traffic_multiplier", 1.0)

    if isinstance(traffic, list):
        traffic = random.choice(traffic)

    if not isinstance(traffic, (int, float)) or traffic <= 0:
        print("Warning: invalid traffic_multiplier → using 1.0")
        traffic = 1.0

    sample["traffic_multiplier"] = traffic

    # simulation time 
    sim_time = config["simulation_time"]

    if isinstance(sim_time, list):
        sim_time = random.choice(sim_time)

    if not isinstance(sim_time, int) or sim_time <= 0:
        raise ValueError("simulation_time must be a positive integer")

    sample["simulation_time"] = sim_time

    #routing
    routing_config = config.get("routing_algorithm", "fastest")

    if not isinstance(routing_config, list):
        routing_config = [routing_config]
 
    allowed = ["fastest", "shortest"]

    valid = [r for r in routing_config if r in allowed]

    if not valid:
        print("Warning: invalid routing → using fastest")
        sample["routing_algorithm"] = "fastest"
    else:
        sample["routing_algorithm"] = random.choice(valid)

    return sample


