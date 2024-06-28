#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Parsing utilities for the Vehicle Routing Problem with Time Window Constraints

This script contains functions for parsing input data and creating the necessary 
graph structures for solving the Vehicle Routing Problem with Time Window Constraints (VRPTW). 
It includes functions for reading and processing node, edge, request, and vehicle data from CSV files.

Functions included:
- get_full_graph: Read input data and construct the full graph.
- convert_to_minutes: Convert a time string in HH:MM format to total minutes.
- read_nodes: Read node data from a CSV file and classify nodes based on requests and vehicles.
- read_edges: Read edge data from a CSV file.
- create_graph: Create a directed graph using nodes and edges data.
- get_requests: Read and parse request data from a CSV file.
- get_vehicles: Read and parse vehicle data from a CSV file.

Dependencies:
- csv: For reading CSV files.
- networkx: For graph operations.
"""

__author__ = "Danial Chekani"
__email__ = "danialchekani@arizona.edu"
__status__ = "Dev"

import csv
from typing import Dict, Tuple
import networkx as nx

from Models import Edge, Node, Request, Vehicle

def get_full_graph(base_directory: str) -> Tuple[nx.DiGraph, Dict[int, Request], Dict[int, Vehicle]]:
    """
    Read input data including vehicles, requests, nodes, and edges, and construct the full graph.

    Parameters
    ----------
    base_directory : str
        The base directory containing the CSV files for nodes, edges, requests, and vehicles.

    Returns
    -------
    tuple
        A tuple containing the graph, requests dictionary, and vehicles dictionary.
    """
    nodes_file = base_directory + "Nodes.csv"
    edges_file = base_directory + "Edges.csv"
    requests = get_requests(base_directory + "Requests.csv")
    vehicles = get_vehicles(base_directory + "Vehicles.csv")
    graph = create_graph(nodes_file, edges_file, requests, vehicles)

    return graph, requests, vehicles

def convert_to_minutes(time_str: str) -> int:
    """
    Convert a time string in HH:MM format to total minutes.

    Parameters
    ----------
    time_str : str
        The time string in HH:MM format or just hours.

    Returns
    -------
    int
        The total time in minutes.
    """
    parts = time_str.split(':')
    
    if len(parts) == 2:
        hours = int(parts[0])
        minutes = int(parts[1])
    else:
        hours = int(time_str)
        minutes = 0
    
    total_minutes = hours * 60 + minutes
    return total_minutes

def read_nodes(nodes_file: str, requests: Dict[int, Request], 
               vehicles: Dict[int, Vehicle]) -> Dict[int, Node]:
    """
    Read node data from a CSV file and classify nodes based on requests and vehicles.
    Each line has a format of (Node_ID, X, Y, Name : Optional)

    Parameters
    ----------
    nodes_file : str
        The file path to the nodes CSV file.
    requests : dict
        A dictionary of requests where keys are request IDs.
    vehicles : dict
        A dictionary of vehicles where keys are vehicle IDs.

    Returns
    -------
    dict
        A dictionary where keys are node IDs and values are node attributes.
    """
    nodes = {}
    with open(nodes_file, 'r') as file:
        reader = csv.reader(file)
        next(reader, None)
        for line in reader:
            node_name = line[3] if len(line) > 3 else None
            node = Node(int(line[0]), float(line[1]), float(line[2]), 'Junction Node' ,node_name)
            nodes[node.node_id] = node

    for _, request in requests.items():
        nodes[request.origin_id].node_type = 'Pickup Node'
        nodes[request.destination_id].node_type = 'Delivery Node'

    for _, vehicle in vehicles.items():
        nodes[vehicle.origin_id].node_type = 'Depot Node'
        nodes[vehicle.destination_id].node_type = 'Depot Node'

    return nodes

def read_edges(filename: str) -> Dict[int, Edge]:
    """
    Read edge data from a CSV file.
    Each line has a format of (Edge_ID, Origin, Destination, Travel_Time, Distance)

    Parameters
    ----------
    filename : str
        The file path to the edges CSV file.

    Returns
    -------
    dict
        A dictionary where keys are edge IDs and values are edge attributes.
    """
    edges = {}
    with open(filename, 'r') as file:
        reader = csv.reader(file)
        next(reader, None)
        for line in reader:
            edge = Edge(line[0], int(line[1]), int(line[2]), float(line[3]), float(line[4]))
            edges[edge.edge_id] = edge
            
    return edges

def create_graph(nodes_file: str, edges_file: str, requests: Dict[int, Request], 
                 vehicles: Dict[int, Vehicle]) -> nx.DiGraph:
    """
    Create a directed graph using nodes and edges data.

    Parameters
    ----------
    nodes_file : str
        The file path to the nodes CSV file.
    edges_file : str
        The file path to the edges CSV file.
    requests : dict
        A dictionary of requests where keys are request IDs.
    vehicles : dict
        A dictionary of vehicles where keys are vehicle IDs.

    Returns
    -------
    nx.DiGraph
        A directed graph with nodes and edges added.
    """
    G = nx.DiGraph()
    
    nodes = read_nodes(nodes_file, requests, vehicles)
    edges = read_edges(edges_file)
    
    for index, (_, node) in enumerate(nodes.items(), start=0):
        G.add_node(index, **node.__dict__)

    # Add edges in both directions
    for index, (key, edge) in enumerate(edges.items(), start=0):
        G.add_edge(edge.origin_id, edge.destination_id, travel_time=edge.travel_time, 
                   distance=edge.distance, id=edge.edge_id)
        G.add_edge(edge.destination_id, edge.origin_id, travel_time=edge.travel_time, 
                   distance=edge.distance, id=edge.edge_id)
    
    return G

def get_requests(filename: str) -> Dict[int, Request]:
    """
    Read and parse request data from a CSV file.
    Each line has a format of (Request_ID, Origin_ID, Destination_ID, Number_of_people, 
        Earliest_departure_origin, Latest_departure_origin, service_time_origin,
        Earliest_departure_destination, Latest_departure_destination, service_time_destination)

    Parameters
    ----------
    filename : str
        The file path to the requests CSV file.

    Returns
    -------
    dict
        A dictionary where keys are request IDs and values are tuples containing request details.
    """
    requests = {}
    with open(filename, 'r') as file:
        reader = csv.reader(file)
        next(reader, None)
        for line in reader:
            request = Request(int(line[0]), int(line[1]), int(line[2]), int(line[3]),
                              convert_to_minutes(line[4]), convert_to_minutes(line[5]),
                              convert_to_minutes(line[6]), convert_to_minutes(line[7]),
                              convert_to_minutes(line[8]), convert_to_minutes(line[9]))
            requests[request.request_id] = request

    return requests

def get_vehicles(filename: str) -> Dict[int, Vehicle]:
    """
    Read and parse vehicle data from a CSV file.
    Each line has a format of (Vehicle_ID, Origin_depot, Destination_depot, Capacity, Bus_type)

    Parameters
    ----------
    filename : str
        The file path to the vehicles CSV file.

    Returns
    -------
    dict
        A dictionary where keys are vehicle IDs and values are tuples containing vehicle details.
    """
    vehicles = {}
    with open(filename, 'r') as file:
        reader = csv.reader(file)
        next(reader, None)
        for line in reader:
            vehicle = Vehicle(int(line[0]), int(line[1]), int(line[2]),
                              int(line[3]), int(line[4]))
            vehicles[vehicle.vehicle_id] = vehicle

    return vehicles