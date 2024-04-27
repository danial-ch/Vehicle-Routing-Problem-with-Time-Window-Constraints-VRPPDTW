import random
import time
from datetime import datetime
from networkx import to_numpy_array
import networkx as nx
from Parsing_VRPPDTW import create_graph, get_vehicles, get_requests
import itertools
from docplex.mp.model import Model
import numpy as np
import json

def get_time():
    start_time = time.time()
    start_time_str = datetime.fromtimestamp(start_time).strftime('%Y-%m-%d %H:%M:%S')
    return start_time_str

def optimize_model(vehicles, requests, graph):

    print("Started Process: " + get_time())

    K = list(vehicles.keys())
    N_values = []

    for request_id, request in requests.items():
        N_values.append(request[0])
    for request_id, request in requests.items():
        N_values.append(request[1])

    n = len(requests)
    P = list(range(n))
    D = list(range(n,2*n))
    N = list(range(2*n))

    origin = 2*n
    destination = 2*n + 1

    s = []
    a = []
    b = []
    l = []

    for i in range(n):
        l.append(requests[i][2])
        a.append(requests[i][3])
        b.append(requests[i][4])
        s.append(requests[i][5])

    for i in range(n):
        l.append(-requests[i][2])
        a.append(requests[i][6])
        b.append(requests[i][7])
        s.append(requests[i][8])

    s.extend([0,0])
    a.extend([0,24*60])
    b.extend([0,24*60])
    l.extend([0,0])

    V = {}
    V_val = {}
    A = {}

    for k in K:
        arcs = []
        V_val[k] = N_values + [vehicles[k][0], vehicles[k][1]]
        V[k] = [i for i in range(len(V_val[k]))]
        for i in V[k]:
            for j in V[k]:
                if i != j:
                    arcs.append((i,j))
        A[k] = arcs

    print("Created V and A: " + get_time())

    all_shortest_paths = dict(nx.all_pairs_dijkstra_path(graph, weight='weight'))
    all_shortest_path_lengths = dict(nx.all_pairs_dijkstra_path_length(graph, weight='weight'))

    shortest_paths_dict = {}
    cost = {}

    for source_node, paths in all_shortest_paths.items():
        shortest_paths_dict[source_node] = {}
        cost[source_node] = {}
        for target_node, path in paths.items():
            shortest_paths_dict[source_node][target_node] = path
            cost[source_node][target_node] = all_shortest_path_lengths[source_node][target_node]

    print("Calculated Costs: " + get_time())

    # model = Model("VRPPDTW", solver='cplex_local')
    model = Model("VRPPDTW")

    X = {}
    cnt = 0
    for k, arcs in A.items():
        for arc in arcs:
            i, j = arc
            X[arc, k] = model.binary_var(name=f'X_{i}_{j}_{k}_{cnt}')
            cnt += 1

    T = {}
    cnt = 0
    for k in K:
        for i in range(len(V[k])):
            T[i, k] = model.continuous_var(name=f't_ik_{i}_{k}_{cnt}')
            cnt += 1

    L = {}
    cnt = 0
    for k in K:
        for i in range(len(V[k])):
            L[i, k] = model.continuous_var(name=f'lk_{i}_{k}_{cnt}')
            cnt += 1

    # Define the objective function
    objective = model.sum(cost[V_val[k][i]][V_val[k][j]] * X[(i,j), k] 
                          for (i,j) in A[k] for k in K)

    # Set the objective function as minimization
    model.minimize(objective)

    print("Defined Model: " + get_time())

    for i in P:
        model.add_constraint(model.sum(X[(i,j), k]
                                    #    for j in N.union(vehicles[k][2])
                                    #    for j in N + [vehicles[k][2]]
                                       for j in N + [destination]
                                       if i != j
                                       for k in K) == 1,
                                       ctname=f'const_9_2_{i}')
        
    for k in K:
        for i in P:
            model.add_constraint(model.sum(X[(i, j), k] for j in N if j != i) -
                                model.sum(X[(j, n+i), k] for j in N if j != n+i) == 0,
                                ctname=f'const_9_3_{k}_{i}')
        
    # for k in K:
    #     sum_term1 = 0
    #     sum_term2 = 0
    #     # for i in P:
    #     for i in range(n):
    #         # for j in N:
    #         for j in range(2*n):
    #             # if i!=j:
    #                 sum_term1 += X[(i,j), k]
    #                 sum_term2 += X[(j,n+i), k]
    #         model.add_constraint(sum_term1 - sum_term2 == 0, 
    #                             ctname=f'const_9_3_{k}_{i}')

    # model.add_constraint(X[(2,4), 0] == 1, ctname='asdasd')
    # model.add_constraint(X[(5,1), 0] == 1, ctname='asdasd')

    # for k in K:
    #     # Flow from depot to customers
    #     model.add_constraint(
    #         model.sum(X[(2*n, j), k] for j in range(n)) == 1,
    #         ctname=f'flow_from_depot_{k}'
    #     )

    #     # Flow to depot from customers
    #     model.add_constraint(
    #         model.sum(X[(i, 2*n+1), k] for i in range(n)) == 1,
    #         ctname=f'flow_to_depot_{k}'
    #     )

    #     # Flow conservation
    #     for j in range(n):
    #         model.add_constraint(
    #             model.sum(X[(i, j), k] for i in range(2*n+2) if i != j) ==
    #             model.sum(X[(j, i), k] for i in range(2*n+2) if i != j),
    #             ctname=f"flow_conservation_{k}_{j}"
    #         )

    for k in K:
        model.add_constraint(model.sum(
                                    # X[(vehicles[k][1],j), k]
                                    X[(origin,j), k]
                                    #    for j in P.union(vehicles[k][2])) == 1,
                                    #    for j in P + [vehicles[k][2]]) == 1,
                                    for j in P + [destination]) == 1,
                                    ctname=f'const_9_4_{k}')
        
    for k in K:
        for j in N:
            model.add_constraint(sum(X[(i, j), k] for i in 
                                     N + [origin] if i != j)
                                  - sum(X[(j, i), k] for i in 
                                        N + [destination] if i != j) 
                                  == 0, ctname=f"const_9_5_{k}_{j}")
        
    for k in K:
        model.add_constraint(model.sum(
                                    # X[(i,vehicles[k][2]), k]
                                    X[(i,destination), k]
                                    #    for i in D.union(vehicles[k][1])) == 1,
                                    #    for i in D + [vehicles[k][1]]) == 1,
                                       for i in D + [origin]) == 1,
                                       ctname=f'const_9_6_{k}')
        
    # for k in K:
    #     for (i,j) in A[k]:
    #         model.add_constraint(X[(i,j), k] * (T[i, k] + s[i] + 
    #                                                 cost[V_val[k][i]][V_val[k][j]] - T[j, k]) 
    #                              <= 0, ctname=f'const_9_7_{k}_{i}_{j}')

    for k in K:
        for (i, j) in A[k]:
            M2 = 1e6
            model.add_constraint(
                T[i, k] + s[i] + cost[V_val[k][i]][V_val[k][j]] - T[j, k] <= (1 - X[(i, j), k]) * M2,
                ctname=f'const_9_7a_{k}_{i}_{j}'
            )

    for k in K:
        for i in V[k]:
            model.add_constraint(T[i, k] >= a[i], ctname=f'const_9_8_lower_{k}_{i}')
            model.add_constraint(T[i, k] <= b[i], ctname=f'const_9_8_upper_{k}_{i}')

    for k in K:
        for i in P:
            model.add_constraint(T[i, k] + cost[V_val[k][i]][V_val[k][n+i]] <= 
                                 T[n+i, k], ctname=f'const_9_9_{k}_{i}')
            
    # for k in K:
    #     for (i,j) in A[k]:
    #         model.add_constraint(X[(i,j), k] * (L[i, k] + l[j] - L[j, k]) == 0, ctname=f'const_9_10_{k}_{i}_{j}')
            
    for k in K:
        for (i, j) in A[k]:
            alpha1 = model.binary_var(name=f'alpha1_{k}_{i}_{j}')
            alpha2 = model.binary_var(name=f'alpha2_{k}_{i}_{j}')
            M = 1e6  # A large positive constant
            model.add_constraint(
                X[(i,j), k] <= M * alpha1,
                ctname=f'const_9_10a_{k}_{i}_{j}'
            )
            model.add_constraint(
                L[i, k] + l[j] - L[j, k] <= M * alpha2 ,
                ctname=f'const_9_10b_{k}_{i}_{j}'
            )
            model.add_constraint(
                alpha1 + alpha2 <= 1,
                ctname=f'const_9_10c_{k}_{i}_{j}'
            )
            # model.add_constraint(
            #     L[i, k] + l[j] - L[j, k] >= 0,
            #     ctname=f'const_9_10d_{k}_{i}_{j}'
            # )

    for k in K:
        for i in P:
            model.add_constraint(L[i, k] >= l[i], ctname=f'const_9_11_lower_{k}_{i}')
            model.add_constraint(L[i, k] <= vehicles[k][2], ctname=f'const_9_11_upper_{k}_{i}')

    for k in K:
        for z in D:
            i = z - n
            model.add_constraint(L[z, k] >= 0, ctname=f'const_9_12_lower_{k}_{i}')
            model.add_constraint(L[z, k] <= vehicles[k][2] - l[i], ctname=f'const_9_12_upper_{k}_{i}')

    for k in K:
        model.add_constraint(L[origin, k] == 0, ctname=f'const_9_13_{k}')

        ##
        model.add_constraint(L[destination, k] == 0, ctname=f'const_9_15_{k}')

    for k in K:
        for (i,j) in A[k]:
            model.add_constraint(X[(i,j), k] >= 0, ctname=f'const_9_14_{k}_{i}_{j}')

    print("Model Sovle Start: " + get_time())

    solution = model.solve()

    print("Model Sovle Finish: " + get_time())

    chosen_xijk = {k: [] for k in K}
    chosen_X = {k: [] for k in K}
    chosen_T = {k: [] for k in K}
    chosen_L = {k: [] for k in K}

    buses_paths = {k: {} for k in K}
    buses_paths_sorted = {k: [] for k in K}

    if solution:
        for k in K:
            for (i, j) in A[k]:
                var_value = solution.get_value(X[(i,j), k])
                if var_value > 0.9:
                    start_time_string = "{}:{}".format(*divmod(round(solution.get_value(T[i, k])), 60))
                    finish_time_string = "{}:{}".format(*divmod(round(solution.get_value(T[j, k])), 60))

                    if V[k][j] < n:
                        status = "Picking Up Request " + str(j) + " at Node " + str(V_val[k][j])
                    elif V[k][j] < 2*n:
                        status = "Delivering Request " + str(j-n) + " at Node " + str(V_val[k][j])
                    elif V[k][j] == 2*n + 1:
                        status = "Going to Destination Depot " + str(V_val[k][j])
                    
                    buses_paths[k][V[k][i]] = {"origin_dest_ids" : (V[k][i], V[k][j]), "start_time" : start_time_string,
                                         "finish_time" : finish_time_string, 
                                         "start_load" : solution.get_value(L[i, k]),
                                         "finish_load" : solution.get_value(L[j, k]),
                                         "path" : shortest_paths_dict[V_val[k][i]][V_val[k][j]],
                                         "status" : status}
                    chosen_xijk[k].append((V[k][i], V[k][j]))
                    chosen_X[k].append((V_val[k][i], V_val[k][j]))

            for i in range(len(V[k])):
                time_string = "{}:{}".format(*divmod(round(solution.get_value(T[i, k])), 60))
                chosen_T[k].append(time_string)

            for i in range(len(V[k])):
                chosen_L[k].append(round(solution.get_value(L[i, k])))

            next_i = 2*n
            while len(buses_paths[k]) > 0:
                item = buses_paths[k].pop(next_i)
                next_i = item["origin_dest_ids"][1]
                buses_paths_sorted[k].append(item)

        print("Objective value:", model.objective_value)

    else:
        print("The model could not be solved.")

    return buses_paths_sorted, chosen_X, chosen_T, chosen_L

def main():

    base_directory = "Inputs/VRPPDTW/"
    vehicles = get_vehicles(base_directory + "Vehicles.txt")
    requests = get_requests(base_directory + "Requests.txt")
    graph = create_graph(base_directory + "Nodes.txt",base_directory + "Edges.txt", requests)

    buses_paths, chosen_X, chosen_T, chosen_L = optimize_model(vehicles, requests, graph)

    with open(base_directory + "/Solution/buses_paths.json", "w") as json_file:
        json.dump(buses_paths, json_file, indent=4)

    with open(base_directory + "/Solution/chosen_x_ijk.json", "w") as json_file:
        json.dump(chosen_X, json_file, indent=4)

    with open(base_directory + "/Solution/chosen_t_ik.json", "w") as json_file:
        json.dump(chosen_T, json_file, indent=4)

    with open(base_directory + "/Solution/chosen_l_ik.json", "w") as json_file:
        json.dump(chosen_L, json_file, indent=4)

if __name__ == "__main__":
    main()

