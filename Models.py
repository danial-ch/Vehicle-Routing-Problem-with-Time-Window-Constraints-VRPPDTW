#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Models required for the Vehicle Routing Problem with Time Window Constraints

This script contains models for modeling and structuring the data, including Node, Edge, Vehicle,
Request, Movement and Trip classes.
"""

__author__ = "Danial Chekani"
__email__ = "danialchekani@arizona.edu"
__status__ = "Dev"

class Node():
    """
    A class used to represent a node in the network

    Attributes
    ----------
    node_id : int
        The unique identifier for the node.
    x : float
        The x-coordinate of the node.
    y : float
        The y-coordinate of the node.
    node_type : str
        The type of the node (e.g., 'junction_node', 'depot_node').
    name : str, optional
        The name of the node.
    """

    def __init__(self, node_id : int, x : float, y : float, 
                 node_type : str, name : str = None) -> None:
        self.node_id = node_id
        self.x = x
        self.y = y
        self.node_type = node_type
        self.name = name

class Edge():
    """
    A class used to represent an edge in the network

    Attributes
    ----------
    edge_id : int
        The unique identifier for the edge.
    origin_id : int
        The ID of the origin node.
    destination_id : int
        The ID of the destination node.
    travel_time : float
        The travel time along the edge in minutes.
    distance : float
        The distance of the edge in miles.
    """

    def __init__(self, edge_id : int, origin_id : int, destination_id : int,
                 travel_time : float, distance : float) -> None:
        self.edge_id = edge_id
        self.origin_id = origin_id
        self.destination_id = destination_id
        self.travel_time = travel_time
        self.distance = distance

class Vehicle():
    """
    A class used to represent a vehicle

    Attributes
    ----------
    vehicle_id : int
        The unique identifier for the vehicle.
    origin_id : int
        The ID of the origin node.
    destination_id : int
        The ID of the destination node.
    capacity : int
        The capacity of the vehicle.
    bus_type : int
        The type of the vehicle.
    """

    def __init__(self, vehicle_id : int, origin_id : int, 
                 destination_id : int, capacity : int, bus_type = int) -> None:
        self.vehicle_id = vehicle_id
        self.origin_id = origin_id
        self.destination_id = destination_id
        self.capacity = capacity
        self.bus_type = bus_type

class Request():
    """
    A class used to represent a request

    Attributes
    ----------
    request_id : int
        The unique identifier for the request.
    origin_id : int
        The ID of the origin node.
    destination_id : int
        The ID of the destination node.
    num_of_people : int
        The number of people in the request.
    earliest_departure_minutes : float
        The earliest departure time in minutes from the start of the day.
    latest_departure_minutes : float
        The latest departure time in minutes from the start of the day.
    departure_service_time : float
        The service time at departure in minutes.
    earliest_arrival_minutes : float
        The earliest arrival time in minutes from the start of the day.
    latest_arrival_minutes : float
        The latest arrival time in minutes from the start of the day.
    arrival_service_time : float
        The service time at arrival in minutes.
    """

    def __init__(self, request_id : int, origin_id : int, destination_id : int, 
                 num_of_people : int, earliest_departure_minutes : float,
                 latest_departure_minutes : float, departure_service_time : float,
                 earliest_arrival_minutes : float, latest_arrival_minutes : float, 
                 arrival_service_time : float) -> None:
        self.request_id = request_id
        self.origin_id = origin_id
        self.destination_id = destination_id
        self.num_of_people = num_of_people
        self.earliest_departure_minutes = earliest_departure_minutes
        self.latest_departure_minutes = latest_departure_minutes
        self.departure_service_time = departure_service_time
        self.earliest_arrival_minutes = earliest_arrival_minutes
        self.latest_arrival_minutes = latest_arrival_minutes
        self.arrival_service_time = arrival_service_time

class Movement():
    """
    A class used to represent a link in the vehicles trip

    Attributes
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
    """

    def __init__(self, origin_id: int, destination_id: int, t1: str, t2: str, 
                     l1: int, l2: int, request_id: int, path: list, 
                     path_cost: float, tt: float, dist: float, status: str) -> None:
        self.origin_id = origin_id
        self.destination_id = destination_id
        self.t1 = t1
        self.t2 = t2
        self.l1 = l1
        self.l2 = l2
        self.request_id = request_id
        self.path = path
        self.path_cost = path_cost
        self.travel_time = tt
        self.distance = dist
        self.status = status

class Trip():
    """
    A class used to describe the full trip vehicles takes

    Attributes
    ----------
    movements : dict
        Dictionary of movements unordered. Each key points to the origin of movement
    movements_sorted : list
        List of movements sorted
    total_cost : float
        total cost of the trip
    total_distance : float
        total distance of the trip
    total_travel_time : float
        total travel time of the trip

    Methods
    -------
    sort_movements(n)
        sorts the movements into movements_sorted and deletes movements dict
    """

    def __init__(self) -> None:
        self.movements = {}
        self.movements_sorted = []
        self.total_cost = 0
        self.total_distance = 0
        self.total_travel_time = 0

    def sort_movements(self, n) -> None:
        # connect edges together to sort the trip
        next_i = 2*n
        while len(self.movements) > 0:
            item = self.movements.pop(next_i)
            next_i = item.destination_id
            self.movements_sorted.append(item)

        del self.__dict__["movements"]