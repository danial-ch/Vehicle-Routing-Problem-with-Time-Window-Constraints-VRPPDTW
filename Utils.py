import json
from pathlib import Path
import networkx as nx

def get_dirs():
    # Specify the folder name under the Inputs folder
    print("-------------")
    problem_dir = input("Enter folder name of the problem\n")

    base_directory = "Samples/" + problem_dir + "/"
    solution_dir = base_directory + "Solution/"

    return base_directory, solution_dir

def load_json(dir, file_name):
    Path(dir).mkdir(parents=True, exist_ok=True)
    with open(dir + f"{file_name}.json", "r") as json_file:
        file = json.load(json_file)

    return file

def save_json(dir, file_name, file):
    Path(dir).mkdir(parents=True, exist_ok=True)
    with open(dir + f"{file_name}.json", "w") as json_file:
        json.dump(file, json_file, indent=4)

def shortest_path_and_lengths_tt_and_distance(graph):
    shortest_paths_tt = {}
    shortest_paths_dist = {}
    t = {}
    d = {}

    # Use Dijkstra to get shortest paths by travel time
    all_shortest_paths_tt = dict(nx.all_pairs_dijkstra_path(graph, weight='travel_time'))
    all_shortest_path_lengths_tt = dict(nx.all_pairs_dijkstra_path_length(graph, weight='travel_time'))

    # Use Dijkstra to get shortest paths by distance
    all_shortest_paths_dist = dict(nx.all_pairs_dijkstra_path(graph, weight='distance'))
    all_shortest_path_lengths_dist = dict(nx.all_pairs_dijkstra_path_length(graph, weight='distance'))

    # Calculate the shortest path and shortest path lengths for travel time and distance
    for source_node, paths in all_shortest_paths_tt.items():
        shortest_paths_tt[source_node] = {}
        t[source_node] = {}
        shortest_paths_dist[source_node] = {}
        d[source_node] = {}

        for target_node, path in paths.items():
            shortest_paths_tt[source_node][target_node] = path
            t[source_node][target_node] = all_shortest_path_lengths_tt[source_node][target_node]
            shortest_paths_dist[source_node][target_node] = all_shortest_paths_dist[source_node][target_node]
            d[source_node][target_node] = all_shortest_path_lengths_dist[source_node][target_node]

    return shortest_paths_tt, t, shortest_paths_dist, d

def get_status(destination_id, destination, n):

    # Assigning the status
    status = ""
    if destination_id < n:
        status = "Picking Up Request " + str(destination_id) + " at Node " + str(destination)
    elif destination_id < 2*n:
        status = "Delivering Request " + str(destination_id-n) + " at Node " + str(destination)
    elif destination_id == 2*n + 1:
        status = "Going to Destination Depot " + str(destination)

    return status

def update_movement_entry(data, origin_id, dest_id, status):
    t1 = data['start_time']
    t2 = data['finish_time']
    l1 = data['start_load']
    l2 = data['finish_load']
    path = data['path']
    path_cost = data['path_cost']
    tt = data['travel_time']
    dist = data['travel_distance']

    return get_bus_movement(origin_id, dest_id, t1, t2, l1, l2, path, path_cost, tt, dist, status)

def get_bus_movement(origin_id, destination_id, t1, t2, l1, l2, path, path_cost, tt, dist, status):

    movement = {"origin_dest_ids" : (origin_id, destination_id), 
                "start_time" : t1,
                "finish_time" : t2, 
                "start_load" : l1,
                "finish_load" : l2,
                "path" : path,
                "path_cost" : path_cost,
                "travel_time" : tt,
                "travel_distance" : dist,
                "status" : status}
    
    return movement