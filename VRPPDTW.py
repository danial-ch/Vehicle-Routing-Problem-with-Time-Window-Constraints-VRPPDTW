#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Vehicle Routing Problem with time window constraints using DOcplex

This script allows the user to solve the Vehicle Routing Problem with time window constraints or
VRPPDTW using the DOcplex solver.

This is an implementation of the following paper:
Desaulniers, G., Desrosiers, J., Erdmann, A., Solomon, M.M., & Soumis, F. (2002). 
VRP with Pickup and Delivery. The Vehicle Routing Problem, 9, pp.225-242.

Contributions:
- Dr. Choobchian: Provided guidance in locating the pertinent research paper, comprehending the underlying problem, and contributing to the implementation.
- Dr. Mohammadi: Designed sample data and assisted with the implementation process.
- Dr. Shamshiripour: Contributed to the implementation and offered additional insights.

Functions included:
- get_time: Get current time
- get_path_cost: Get the cost of a single path
- get_cost_matrix: Get path costs for all paths
- optimize_model: Solve the VRPPDTW problem

Dependencies:
- docplex.mp.model: For solving the model using DoCplex.
- networkx: For graph operations.
- time: For tracking running time of the program
- datetime: For displaying time in correct format
"""
__author__ = "Danial Chekani"
__email__ = "danialchekani@arizona.edu"
__status__ = "Dev"

import time
from datetime import datetime
from typing import Dict, List, Tuple
from networkx import DiGraph
from Parsing import get_full_graph
from docplex.mp.model import Model

from Utils import get_dirs, get_request_id, get_status, save_json, shortest_path_and_lengths_tt_and_distance
from Models import Movement, Request, Trip, Vehicle

def get_time() -> str:
    """
    A simple function to get current time in readable format

    Returns
    -------
    current_time : str, YYYY:mm:dd HH:MM:SS
    """
    current_time : str
    current_time = time.time()
    current_time_str = datetime.fromtimestamp(current_time).strftime('%Y-%m-%d %H:%M:%S')
    return current_time_str

def get_path_cost(travel_time : float, distance : float , bus_type : int, 
                  capacity : int, cost_factors : list):
    """
    Calculate the total cost of a path based on travel time, distance, bus type, 
    capacity, and given cost factors.

    Parameters
    ----------
    travel_time : float
        The time it takes to travel the path in minutes.
    distance : float
        The distance of the path in kilometers.
    bus_type : int
        An identifier for the type of bus used.
    capacity : int
        The seating capacity of the bus.
    cost_factors : list
        A dynamic list containing factors used to calculate the cost.
        The number of factors depends of the implementation of the formulation.
        For example, it could include:
        - alpha (float): The cost factor per minute of travel time.
        - beta (float): The cost factor per kilometer of distance.
        - const (float): A constant cost added to the total.

    Returns
    -------
    float
        The total cost of path (i,j) taken by bus k.

    Example
    -------
    >>> get_path_cost(160, 150.0, 1, 30, [10.0, 2.0, 100.0])
    530.0
    """

    #TODO design and unpack the cost_factors according to your formulation
    alpha, beta, const = cost_factors

    return (travel_time * alpha) + (distance * beta) + const

def get_cost_matrix(vehicles : Dict[int, Vehicle], travel_time_matrix : list, 
                    distance_matrix : list, cost_factors : list):
    """
    Calculate the cost matrix for all paths and vehicles based on travel time, 
    distance, and given cost factors.

    Parameters
    ----------
    vehicles : dict
        A dictionary where the keys are vehicle IDs and the values are each 
        vehicle's information in the following format:
        (Origin_depot_ID, Destination_depot_ID, Capacity, Bus_type)
    travel_time_matrix : list
        A 2D list (matrix) where each element represents the travel time in minutes 
        between two points.
    distance_matrix : list
        A 2D list (matrix) where each element represents the distance in kilometers 
        between two points.
    cost_factors : list
        A dynamic list containing factors used to calculate the cost.
        The number of factors depends of the implementation of the formulation.
        For example, it could include:
        - alpha (float): The cost factor per minute of travel time.
        - beta (float): The cost factor per kilometer of distance.
        - const (float): A constant cost added to the total.

    Returns
    -------
    list
        A 3D list (matrix) where the element at [i][j][k] represents the cost 
        of traveling from point i to point j using vehicle k.

    Example
    -------
    >>> vehicles = {
            1: (0, 1, 30, 1),
            2: (0, 1, 40, 2)
        }
    >>> travel_time_matrix = [
            [0, 30],
            [30, 0]
        ]
    >>> distance_matrix = [
            [0, 15],
            [15, 0]
        ]
    >>> cost_factors = [10.0, 2.0, 100.0]
    >>> get_cost_matrix(vehicles, travel_time_matrix, distance_matrix, cost_factors)
    [[[0.0, 0.0], [430.0, 430.0]], [[430.0, 430.0], [0.0, 0.0]]]
    """

    cost = []
    for i in range(len(travel_time_matrix)):
        cost.append([])
        for j in range(len(travel_time_matrix[i])):
            cost[i].append([])
            for k, vehicle in vehicles.items():
                result = get_path_cost(travel_time_matrix[i][j], distance_matrix[i][j], 
                                        vehicle.bus_type, vehicle.capacity, cost_factors)
                cost[i][j].append(result)

    return cost

def optimize_model(vehicles : Dict[int, Vehicle], requests : Dict[int, Request], 
                   graph : DiGraph, cost_factors : list) \
                    -> Tuple[Dict[int, Trip], Dict[int, List], Dict[int, str], Dict[int, int]]:
    """"
    The main function to solve the Vehicle Routing Problem with Time Window Constraints

    
    Parameters
    ----------
    vehicles : dict
        A dictionary where the keys are the vehicle IDs and the values are vehicles

    requests : dict
        A dictionary where the keys are the request IDs and the values
        are requests

    graph : Networkx Digraph
        A graph storing the network's structure and travel times between nodes.

    cost_factors : list
        A dynamic list containing factors used to calculate the cost.
        The number of factors depends of the implementation of the formulation.
        For example, it could include:
        - alpha (float): The cost factor per minute of travel time.
        - beta (float): The cost factor per kilometer of distance.
        - const (float): A constant cost added to the total.

    Returns
    -------
    trips : dict
        A dictionary where the keys are vehicle IDs and the values are trips
    chosen_X : dict
        A dictionary where the keys are the vehicle IDs and the values
        are the travel arcs chosen by the vehicle.
    chosen_T : dict
        A dictionary where the keys are the vehicle IDs and the values
        are the times at which request i has been completed.
    chosen_L : dict
        A dictionary where the keys are the vehicle IDs and the values
        are the loads that have changed after serving request i.
    """

    M = 5e3  # A large positive constant for linearizing
    
    print("Started Process: " + get_time())

    K = list(vehicles.keys())
    N_values = []

    for request_id, request in requests.items():
        N_values.append(request.origin_id)
    for request_id, request in requests.items():
        N_values.append(request.destination_id)

    """
    Creating auxiliary lists P, D, N
    Since P, D, N are simply pointers to geographical nodes they 
    are created using the range function.

    Since every bus can take every possible path, k notation for P, D, N
    are omitted and each bus shares the same lists
    """
    n = len(requests)
    P = list(range(n))
    D = list(range(n,2*n))
    N = list(range(2*n))

    # Determining origin and destination index of each bus
    origin = 2*n
    destination = 2*n + 1

    s = [] # Service time of each node in N. Assumed 0 at depots
    a = [] # List of the beginning of arrival and departure windows.
    b = [] # List of the end of arrival and departure windows.
    l = [] # List of the loads at each node in N.

    for i in range(n):
        l.append(requests[i].num_of_people)
        a.append(requests[i].earliest_departure_minutes)
        b.append(requests[i].latest_departure_minutes)
        s.append(requests[i].departure_service_time)

    for i in range(n):
        l.append(-requests[i].num_of_people) # load of a bus changes by -d_i when delivering request i
        a.append(requests[i].earliest_arrival_minutes)
        b.append(requests[i].latest_arrival_minutes)
        s.append(requests[i].arrival_service_time)

    # Including values for depots
    a.extend([0,24*60])
    b.extend([0,24*60])
    s.extend([0,0])
    l.extend([0,0])

    V = {}
    V_val = {}
    A = {}

    # Creating dict of possible arcs for each bus
    for k in K:
        arcs = []
        V_val[k] = N_values + [vehicles[k].origin_id, vehicles[k].destination_id]
        V[k] = [i for i in range(len(V_val[k]))]
        for i in V[k]:
            for j in V[k]:
                if i != j:
                    arcs.append((i,j))
        A[k] = arcs

    model = Model("VRPPDTW")

    # Decision variable X stores all the possible arcs for each bus
    X = {}
    cnt = 0
    for k, arcs in A.items():
        for arc in arcs:
            i, j = arc
            X[arc, k] = model.binary_var(name=f'X_{i}_{j}_{k}_{cnt}')
            cnt += 1

    # Decision variable T for storing time to serve request i by bus k
    T = {}
    cnt = 0
    for k in K:
        for i in range(len(V[k])):
            T[i, k] = model.continuous_var(name=f't_ik_{i}_{k}_{cnt}')
            cnt += 1

    # Decision variable L for storing load change after serving request i by bus k
    L = {}
    cnt = 0
    for k in K:
        for i in range(len(V[k])):
            L[i, k] = model.continuous_var(name=f'lk_{i}_{k}_{cnt}')
            cnt += 1

    print("Created variables: " + get_time())

    # Using Dijekstra to get the shortest paths based on travel time and distance
    # It is assumed that travel_time is the same for all buses and only
    # Depends on i and j
    shortest_paths_tt, t, _, d = shortest_path_and_lengths_tt_and_distance(graph)

    cost = get_cost_matrix(vehicles, t, d, cost_factors)
    
    print("Calculated Costs: " + get_time())

    # Define the objective function
    objective = model.sum(cost[V_val[k][i]][V_val[k][j]][k] * X[(i,j), k] 
                          for (i,j) in A[k] for k in K)

    model.minimize(objective)

    # Constraint 9.2
    for i in P:
        model.add_constraint(model.sum(X[(i,j), k]
                                       for j in N + [destination] if i != j
                                       for k in K) == 1,
                                       ctname=f'const_9_2_{i}')

    # Constraint 9.3
    for k in K:
        for i in P:
            model.add_constraint(model.sum(X[(i, j), k] for j in N if j != i) -
                                model.sum(X[(j, n+i), k] for j in N if j != n+i) == 0,
                                ctname=f'const_9_3_{k}_{i}')

    # Constraint 9.4
    for k in K:
        model.add_constraint(model.sum(X[(origin,j), k]
                                    for j in P + [destination]) == 1,
                                    ctname=f'const_9_4_{k}')

    # Constraint 9.5
    for k in K:
        for j in N:
            model.add_constraint(sum(X[(i, j), k] for i in N + [origin] if i != j)
                                  - sum(X[(j, i), k] for i in N + [destination] if i != j) 
                                  == 0, ctname=f"const_9_5_{k}_{j}")

    # Constraint 9.6
    for k in K:
        model.add_constraint(model.sum(X[(i,destination), k]
                                       for i in D + [origin]) == 1,
                                       ctname=f'const_9_6_{k}')

    # Constraint 9.7
    # Linearized to make it convex
    # T_ik + s_i + t_i,n+i,k - T_jk <= (1 - X_ijk) * M
    for k in K:
        for (i, j) in A[k]:
            model.add_constraint(
                T[i, k] + s[i] + t[V_val[k][i]][V_val[k][j]] - T[j, k] 
                <= (1 - X[(i, j), k]) * M,
                ctname=f'const_9_7a_{k}_{i}_{j}'
            )

    # Constraint 9.8
    for k in K:
        for i in V[k]:
            model.add_constraint(T[i, k] >= a[i], ctname=f'const_9_8_lower_{k}_{i}')
            model.add_constraint(T[i, k] <= b[i], ctname=f'const_9_8_upper_{k}_{i}')

    # Constraint 9.9
    for k in K:
        for i in P:
            model.add_constraint(T[i, k] + t[V_val[k][i]][V_val[k][n+i]] <= 
                                 T[n+i, k], ctname=f'const_9_9_{k}_{i}')

    # Constraint 9.10
    # Linearized to make it convex
    # x_ijk = 0 + alpha
    # L_ik + l_i + l_jk <= M * beta
    # L_ik + l_i + l_jk >= -M * beta
    # alpha + beta <= 1
    for k in K:
        for (i, j) in A[k]:
            alpha = model.binary_var(name=f'alpha_{k}_{i}_{j}')
            beta = model.binary_var(name=f'beta_{k}_{i}_{j}')
            model.add_constraint(
                X[(i,j), k] == 0 + alpha,
                ctname=f'const_9_10a_{k}_{i}_{j}'
            )
            model.add_constraint(
                L[i, k] + l[j] - L[j, k] <= M * beta,
                ctname=f'const_9_10b_{k}_{i}_{j}'
            )
            model.add_constraint(
                L[i, k] + l[j] - L[j, k] >= (-M) * beta,
                ctname=f'const_9_10c_{k}_{i}_{j}'
            )
            model.add_constraint(
                alpha + beta <= 1,
                ctname=f'const_9_10d_{k}_{i}_{j}'
            )

    # Constraint 9.11
    for k in K:
        for i in P:
            model.add_constraint(L[i, k] >= l[i], ctname=f'const_9_11_lower_{k}_{i}')
            model.add_constraint(L[i, k] <= vehicles[k].capacity, ctname=f'const_9_11_upper_{k}_{i}')

    # Constraint 9.12
    for k in K:
        for z in D:
            i = z - n
            model.add_constraint(L[z, k] >= 0, ctname=f'const_9_12_lower_{k}_{i}')
            model.add_constraint(L[z, k] <= vehicles[k].capacity - l[i], 
                                 ctname=f'const_9_12_upper_{k}_{i}')

    # Constraint 9.13
    for k in K:
        model.add_constraint(L[origin, k] == 0, ctname=f'const_9_13_{k}')

    # Constraint 9.14
    for k in K:
        for (i,j) in A[k]:
            model.add_constraint(X[(i,j), k] >= 0, ctname=f'const_9_14_{k}_{i}_{j}')

    print("Model Sovle Start: " + get_time())

    # Solving the model
    solution = model.solve()

    print("Model Sovle Finish: " + get_time())

    # Creating output dicts
    chosen_X = {k: [] for k in K}
    chosen_T = {k: [] for k in K}
    chosen_L = {k: [] for k in K}

    trips = {k: Trip() for k in K}

    if solution:
        for k in K:
            for (i, j) in A[k]:
                # Choosing arcs that are 1
                var_value = solution.get_value(X[(i,j), k])
                if var_value > 0.9:

                    # Converting time to HH:MM
                    start_time_string = "{}:{}".format(*divmod(round(solution.get_value(T[i, k])), 60))
                    finish_time_string = "{}:{}".format(*divmod(round(solution.get_value(T[j, k])), 60))

                    request_id, destination_type = get_request_id(V[k][j], n)

                    status = get_status(request_id, destination_type, V_val[k][j])

                    # Calculating total cost, travel_time, and distance for each bus
                    path_cost = cost[V_val[k][i]][V_val[k][j]][k]
                    trips[k].total_cost += path_cost
                    path_tt = t[V_val[k][i]][V_val[k][j]]
                    trips[k].total_travel_time += path_tt
                    path_dist = d[V_val[k][i]][V_val[k][j]]
                    trips[k].total_distance += path_dist
                    
                    movement = Movement(V[k][i], V[k][j], start_time_string,
                                        finish_time_string, round(solution.get_value(L[i, k])),
                                        round(solution.get_value(L[j, k])),
                                        request_id,
                                        shortest_paths_tt[V_val[k][i]][V_val[k][j]],
                                        path_cost,
                                        path_tt,
                                        path_dist,
                                        status)
                    
                    trips[k].movements[V[k][i]] = movement
                    
                    # Storing chosen arcs from X
                    chosen_X[k].append((V_val[k][i], V_val[k][j]))

            # Storing T values in HH:MM
            for i in range(len(V[k])):
                time_string = "{}:{}".format(*divmod(round(solution.get_value(T[i, k])), 60))
                chosen_T[k].append(time_string)

            # Storing L values
            for i in range(len(V[k])):
                chosen_L[k].append(round(solution.get_value(L[i, k])))

            # Sorting arcs based on values of (i,j)
            trips[k].sort_movements(n)

        print("Objective value:", model.objective_value)

    else:
        print("The model could not be solved.")

    return trips, chosen_X, chosen_T, chosen_L

def main():

    # Getting graph structure, requests and vehicles based on user input data
    base_directory, solution_dir = get_dirs()
    graph, requests, vehicles = get_full_graph(base_directory)

    trips, chosen_x_ijk, chosen_t_ik, chosen_l_ik = \
    optimize_model(vehicles, requests, graph, [0.6, 0.5, 5])
    
    # If model is solved, the results are stored in json files
    if not (len(trips) == 0):
        save_json(solution_dir, "trips", trips)
        save_json(solution_dir, "chosen_x_ijk", chosen_x_ijk)
        save_json(solution_dir, "chosen_t_ik", chosen_t_ik)
        save_json(solution_dir, "chosen_l_ik", chosen_l_ik)

if __name__ == "__main__":
    main()

