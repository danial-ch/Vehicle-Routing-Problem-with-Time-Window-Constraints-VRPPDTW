#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Vehicle Routing Problem with time window constraints using DOcplex

This script allows the user to solve the Vehicle Routing Problem with time window constraints or
VRPPDTW using the DOcplex solver.

This is an implementation of the following paper:
Desaulniers, G., Desrosiers, J., Erdmann, A., Solomon, M.M., & Soumis, F. (2002). 
VRP with Pickup and Delivery. The Vehicle Routing Problem, 9, pp.225-242.
"""
__author__ = "Danial Chekani"
__email__ = "danialchekani@arizona.edu"
__status__ = "Dev"

import copy
import time
from datetime import datetime
import networkx as nx
from networkx import DiGraph
from Parsing import get_full_graph
from docplex.mp.model import Model
import json

from Utils import get_bus_movement, get_dirs, get_status, save_json, shortest_path_and_lengths_tt_and_distance

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

def get_path_cost(travel_time, distance, cost_factors):

    #TODO design and unpack the cost_factors based on own formulas
    alpha, beta, const = cost_factors

    return (travel_time * alpha) + (distance * beta) + const

def get_cost_matrix(travel_time_matrix, distance_matrix, cost_factors):

    cost = []
    for i in range(len(travel_time_matrix)):
        cost.append([])
        for j in range(len(travel_time_matrix[i])):
            result = get_path_cost(travel_time_matrix[i][j], distance_matrix[i][j], cost_factors)
            cost[i].append(result)

    return cost

def optimize_model(vehicles : dict, requests : dict, graph : DiGraph, cost_factors : list) -> dict:
    """"
    The main function to solve the Vehicle Routing Problem with Time Window Constraints

    
    Parameters
    ----------
    vehicles : dict
        A dictionary where the keys are the vehicle IDs and the values 
        are each vehicle's information in the following format:
        (Origin_depot_ID, Destination_depot,ID, Capacity)

    requests : dict
        A dictionary where the keys are the request IDs and the values
        are each request's information in the following format:
        (Request_origin, Request_destination, Num_people_at_request, Earliest_departure_minutes,
        Latest_departure_minutes, Departure_service_time, Earliest_arrival_minutes,
        Latest_arrival_minutes, Arrival_service_time)

    graph : Networkx Digraph
        A graph storing the network's structure and travel times between nodes.

    Returns
    -------
    buses_paths_sorted : dict
        A dictionary where the keys are bus IDs and the values
        are a list of travels the bus has made in order of travel.
        Each travel is a dictionary in the following format:
        {'origin_dest_ids' : tuple, (i,j), 'start_time' : str, HH:MM, 'finish_time' : str, HH:MM,
         'start_load' : int, 'finish_load' : int, 'path' : list[int], 'status' : str}
    chosen_X : dict
        A dictionary where the keys are the bus IDs and the values
        are the travel arcs chosen by the bus.
    chosen_T : dict
        A dictionary where the keys are the bus IDs and the values
        are the times at which request i has been completed.
    chosen_L : dict
        A dictionary where the keys are the bus IDs and the values
        are the loads that have changed after serving request i.
    """

    M = 5e3  # A large positive constant for linearizing
    
    print("Started Process: " + get_time())

    K = list(vehicles.keys())
    N_values = []

    for request_id, request in requests.items():
        N_values.append(request[0])
    for request_id, request in requests.items():
        N_values.append(request[1])

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
        l.append(requests[i][2])
        a.append(requests[i][3])
        b.append(requests[i][4])
        s.append(requests[i][5])

    for i in range(n):
        l.append(-requests[i][2]) # load of a bus changes by -d_i when delivering request i
        a.append(requests[i][6])
        b.append(requests[i][7])
        s.append(requests[i][8])

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
        V_val[k] = N_values + [vehicles[k][0], vehicles[k][1]]
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

    shortest_paths_tt, t, shortest_paths_dist, d = shortest_path_and_lengths_tt_and_distance(graph)

    cost = get_cost_matrix(t, d, cost_factors)
    
    print("Calculated Costs: " + get_time())

    # Define the objective function
    objective = model.sum(cost[V_val[k][i]][V_val[k][j]] * X[(i,j), k] 
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
            model.add_constraint(L[i, k] <= vehicles[k][2], ctname=f'const_9_11_upper_{k}_{i}')

    # Constraint 9.12
    for k in K:
        for z in D:
            i = z - n
            model.add_constraint(L[z, k] >= 0, ctname=f'const_9_12_lower_{k}_{i}')
            model.add_constraint(L[z, k] <= vehicles[k][2] - l[i], ctname=f'const_9_12_upper_{k}_{i}')

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

    buses_paths = {k: {} for k in K}
    buses_paths_sorted = {k: [] for k in K}

    if solution:
        for k in K:

            total_bus_cost = 0
            total_bus_travel_time = 0
            total_bus_dist = 0
        
            for (i, j) in A[k]:
                # Choosing arcs that are 1
                var_value = solution.get_value(X[(i,j), k])
                if var_value > 0.9:

                    # Converting time to HH:MM
                    start_time_string = "{}:{}".format(*divmod(round(solution.get_value(T[i, k])), 60))
                    finish_time_string = "{}:{}".format(*divmod(round(solution.get_value(T[j, k])), 60))

                    status = get_status(V[k][j], V_val[k][j], n)

                    path_cost = cost[V_val[k][i]][V_val[k][j]]
                    total_bus_cost += path_cost
                    bus_tt = t[V_val[k][i]][V_val[k][j]]
                    total_bus_travel_time += bus_tt
                    bus_dist = d[V_val[k][i]][V_val[k][j]]
                    total_bus_dist += bus_dist
                    
                    # Creating the buses_path dict
                    movement = get_bus_movement(V[k][i], V[k][j], start_time_string,
                                                finish_time_string, round(solution.get_value(L[i, k])),
                                                round(solution.get_value(L[j, k])),
                                                shortest_paths_tt[V_val[k][i]][V_val[k][j]],
                                                path_cost,
                                                bus_tt,
                                                bus_dist,
                                                status)
                    buses_paths[k][V[k][i]] = movement
                    
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
            next_i = 2*n
            while len(buses_paths[k]) > 0:
                item = buses_paths[k].pop(next_i)
                next_i = item["origin_dest_ids"][1]
                buses_paths_sorted[k].append(item)

            buses_paths_sorted[k][1]["Total_Cost"] = total_bus_cost
            buses_paths_sorted[k][1]["Total_Travel_time"] = total_bus_travel_time
            buses_paths_sorted[k][1]["Total_Distance"] = total_bus_dist

        print("Objective value:", model.objective_value)

    else:
        print("The model could not be solved.")

    return buses_paths_sorted, chosen_X, chosen_T, chosen_L

def main():

    base_directory, solution_dir = get_dirs()
    graph, requests, vehicles = get_full_graph(base_directory)

    buses_paths, chosen_x_ijk, chosen_t_ik, chosen_l_ik = \
    optimize_model(vehicles, requests, graph, [0.6, 0.5, 5])
    
    # If model is solved, the results are stored in json files
    if not (len(buses_paths) == 0 or len(buses_paths[0]) == 0):
        save_json(solution_dir, "buses_paths", buses_paths)
        save_json(solution_dir, "chosen_x_ijk", chosen_x_ijk)
        save_json(solution_dir, "chosen_t_ik", chosen_t_ik)
        save_json(solution_dir, "chosen_l_ik", chosen_l_ik)

if __name__ == "__main__":
    main()

