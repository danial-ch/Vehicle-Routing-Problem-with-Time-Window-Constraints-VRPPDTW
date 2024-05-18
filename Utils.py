#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Utility functions for the Vehicle Routing Problem with Time Window Constraints

This script contains utility functions used in the implementation of the Vehicle Routing Problem 
with Time Window Constraints (VRPTW). These functions handle file operations, graph processing, 
and status updates necessary for solving the VRPTW.

Functions included:
- get_dirs: Prompt the user for problem directory and return directory paths.
- load_json: Load a JSON file from a specified directory.
- save_json: Save a dictionary to a JSON file in a specified directory.
- shortest_path_and_lengths_tt_and_distance: Compute shortest paths and lengths based on travel time and distance.
- get_request_id: Determine the request ID and type based on destination ID.
- get_status: Generate a status message based on request ID, type, and destination.
- get_bus_movement: Create a dictionary representing a bus movement.

Dependencies:
- json: For reading and writing JSON files.
- pathlib.Path: For directory path manipulations.
- networkx: For graph operations.
- os: For getting directories.
"""
__author__ = "Danial Chekani"
__email__ = "danialchekani@arizona.edu"
__status__ = "Dev"

import json
import os
from pathlib import Path
import networkx as nx

def get_dirs() -> tuple:
    """
    Prompt the user to input the folder name of the problem and return the base 
    directory and solution directory paths.

    Returns
    -------
    tuple
        A tuple containing the base directory and solution directory paths.
    """

    # Specify the folder name under the Inputs folder
    print("-------------")
    problem_dir = input("Enter folder name of the problem\n")

    base_directory = "Samples/" + problem_dir + "/"
    solution_dir = base_directory + "Solution/"

    if not os.path.exists(solution_dir):
        os.makedirs(solution_dir)

    return base_directory, solution_dir

def load_json(dir: str, file_name: str) -> dict:
    """
    Load a JSON file from the specified directory.

    Parameters
    ----------
    dir : str
        The directory where the JSON file is located.
    file_name : str
        The name of the JSON file to load (without the .json extension).

    Returns
    -------
    dict
        The contents of the JSON file as a dictionary.
    """
    Path(dir).mkdir(parents=True, exist_ok=True)
    with open(dir + f"{file_name}.json", "r") as json_file:
        file = json.load(json_file)

    return file

def save_json(dir: str, file_name: str, file: dict):
    """
    Save a dictionary to a JSON file in the specified directory.

    Parameters
    ----------
    dir : str
        The directory where the JSON file will be saved.
    file_name : str
        The name of the JSON file to save (without the .json extension).
    file : dict
        The dictionary to save as a JSON file.
    """
    Path(dir).mkdir(parents=True, exist_ok=True)
    with open(dir + f"{file_name}.json", "w") as json_file:
        json.dump(file, json_file, indent=4)

def shortest_path_and_lengths_tt_and_distance(graph: nx.DiGraph) -> tuple:
    """
    Calculate the shortest paths and their lengths based on travel time and distance 
    for a given graph.

    Parameters
    ----------
    graph : networkx.DiGraph
        A directed graph where edges have 'travel_time' and 'distance' attributes.

    Returns
    -------
    tuple
        A tuple containing four dictionaries:
        - shortest_paths_tt: Shortest paths by travel time.
        - t: Shortest path lengths by travel time.
        - shortest_paths_dist: Shortest paths by distance.
        - d: Shortest path lengths by distance.
    """
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

def get_request_id(destination_id: int, n: int) -> tuple:
    """
    Determine the request ID and type based on the destination ID.

    Parameters
    ----------
    destination_id : int
        The destination ID.
    n : int
        The number of requests.

    Returns
    -------
    tuple
        A tuple containing the request ID and a string indicating the type 
        ('Pickup', 'Deliver', or 'Depot').
    """
    if destination_id < n: 
        return destination_id, "Pickup"
    elif destination_id < 2 * n: 
        return destination_id - n, "Deliver"
    else: 
        return -1, "Depot"

def get_status(request_id: int, type: str, destination: int) -> str:
    """
    Generate a status message based on the request ID, type, and destination.

    Parameters
    ----------
    request_id : int
        The request ID.
    type : str
        The type of request ('Pickup' or 'Deliver').
    destination : int
        The destination node ID.

    Returns
    -------
    str
        A status message describing the current action.
    """
    status = ""
    if request_id != -1:
        if type == "Deliver": 
            status = f"Delivering Request {request_id} at Node {destination}"
        elif type == "Pickup": 
            status = f"Picking Up Request {request_id} at Node {destination}"
    else:
        status = f"Going to Destination Depot {destination}"

    return status

def get_bus_movement(origin_id: int, destination_id: int, t1: str, t2: str, 
                     l1: int, l2: int, request_id: int, path: list, 
                     path_cost: float, tt: float, dist: float, status: str) -> dict:
    """
    Create a dictionary representing a bus movement.

    Parameters
    ----------
    origin_id : int
        The origin node ID.
    destination_id : int
        The destination node ID.
    t1 : str
        The start time in HH:MM format.
    t2 : str
        The finish time in HH:MM format.
    l1 : int
        The load at the start of the journey.
    l2 : int
        The load at the end of the journey.
    request_id : int
        The request ID.
    path : list
        A list of node IDs representing the path.
    path_cost : float
        The cost of the path.
    tt : float
        The travel time in minutes.
    dist : float
        The travel distance in kilometers.
    status : str
        The status of the movement.

    Returns
    -------
    dict
        A dictionary representing the bus movement.
    """
    movement = {"origin_dest_ids": (origin_id, destination_id), 
                "start_time": t1,
                "finish_time": t2, 
                "start_load": l1,
                "finish_load": l2,
                "request_id": request_id,
                "path": path,
                "path_cost": path_cost,
                "travel_time": tt,
                "travel_distance": dist,
                "status": status}
    
    return movement