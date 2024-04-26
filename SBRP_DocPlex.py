import random
import time
from datetime import datetime
from networkx import to_numpy_array
import networkx as nx
from Parsing import create_graph, get_buses, get_stops, get_schools_and_depots, read_nodes
import itertools
from docplex.mp.model import Model
import numpy as np
import json

t_coefficient = 10

def get_time():
    start_time = time.time()
    start_time_str = datetime.fromtimestamp(start_time).strftime('%Y-%m-%d %H:%M:%S')
    return start_time_str

def get_start_finish_t(schools, stops):
    finish_t = max(school[1]['latest_arrival'] for school in schools.values())  # Get the highest latest arrival time
    start_t = min(stop[2] for stop in stops.values())  # Get the lowest earliest departure time
    return start_t, finish_t

def create_psi_p(stops, time_steps, W):
    Psi_p = {}

    for index, (key, stop) in enumerate(stops.items()):
        s_p, n_p, ep, lp, i, j = stop
        arcs = []

        # Generate all possible permutations of T and W
        permutations = list(itertools.product(W, W)) 
        for perm in permutations:
            for t, t_prime in time_steps:
                w, w_prime = perm
                arcs.append((i, j, t, t_prime, w, w_prime))
        
        Psi_p[index] = arcs

    return Psi_p

def optimize_model(buses, stops, schools, depots, graph, t_start, t_finish, capacity):

    print("Started Process: " + get_time())

    V = list(buses.keys())
    P = list(stops.keys())
    S = [school_data[1]['node_id'] for school_data in schools.values()]
    N = list(graph.nodes)
    T = list(range(t_start, t_finish + t_coefficient, t_coefficient))

    # time_steps = [(t1, t2) for i, t1 in enumerate(T) for t2 in T[i+1:]]
    time_steps = [(t1, t2) for i, t1 in enumerate(T) for t2 in T if t1 != t2]

    W = []
    Av = []

    n_schools = len(S)

    #!!!!! if all the people in the stop can't fit, it ignores it

    for state in itertools.product(P, repeat=n_schools):
        if sum(state) <= capacity:
            W.append(state)

    w0 = (0,) * n_schools

    Psi_p = create_psi_p(stops, time_steps, W)

    for t, t_prime in time_steps:
        for w in W:
            for w_prime in W:
                for i,j in graph.edges():
                    Av.append((i,j,t,t_prime,w,w_prime))

    # Get cost matrix
    cost = to_numpy_array(graph)

    print("Created Variables: " + get_time())

    # Create a model
    model = Model("MSBRP")

    x = model.binary_var_matrix(V, Av, name='x')

    # Define the objective function
    objective = model.sum(cost[i][j] * x[v, (i,j,t,t_prime,w,w_prime)] 
                          for v in V for (i,j,t,t_prime,w,w_prime) in Av)

    # Set the objective function as minimization
    model.minimize(objective)

    print("Defined Model: " + get_time())

    # Define the flow balance constraint
    for v in V:
        model.add_constraint(model.sum(x[v, (i,j,t,t_prime,w,w_prime)] 
                                       for (i,j,t,t_prime,w,w_prime) in Av 
                                       if i == buses[v][0] and t == buses[v][2] and w == w0) == 1, 
                                       ctname='flow_balance_origin_{0}'.format(v))

    print("Flow Balance Origin Constraint: " + get_time())

    # Define the flow balance constraints at bus's destination vertex using add_constraint method
    for v in V:
        model.add_constraint(model.sum(x[v, (i,j,t,t_prime,w,w_prime)] 
                                       for (i,j,t,t_prime,w,w_prime) in Av 
                                       if j == buses[v][1] and t_prime == buses[v][3] and w in W) == 1,
                                       ctname='flow_balance_destination_{0}'.format(v))

    print("Flow Balance Destination Constraint: " + get_time())

    adjacency_list = {}
    # Iterate over each node in the graph
    for node in graph.nodes():
        # Get the list of adjacent nodes for the current node
        neighbors = list(nx.neighbors(graph, node))
        adjacency_list[node] = neighbors

    print("Adjucency List: " + get_time())

    # Define the flow balance constraints at bus's intermediate vertex using add_constraint method
    # for v in V:
    #     sum_term1 = 0
    #     sum_term2 = 0
    #     for i in N:
    #         for t in T:
    #             for w in W:
    #                 if (i not in {buses[v][0], buses[v][1]}) and (t not in {buses[v][2], buses[v][3]}) and (w != w0):
    #                     for j in adjacency_list[i]:
    #                         if j != i:
    #                             for t_zeg in T:
    #                                 if t_zeg != t:
    #                                     for w_zeg in W:
    #                                         if w_zeg != w:
    #                                             sum_term1 += x[v, (i,j,t,t_zeg,w,w_zeg)]

    #                     for j_prime in adjacency_list[i]:
    #                         if j_prime != i:
    #                             for t_prime in T:
    #                                 if t_prime != t:
    #                                     for w_prime in W:
    #                                         if w_prime != w:
    #                                             sum_term2 += x[v, (j_prime,i,t_prime,t,w_prime,w)]
                                        
    #     model.add_constraint(sum_term1 - sum_term2 == 0, 
    #                         ctname='flow_balance_intermediate_{0}'.format(v))

    # for v in V:
    #     sum_term1 = 0
    #     sum_term2 = 0
    #     for i in N:
    #         for t in T:
    #             for w in W:
    #                 if (i,t,w) != (buses[v][0], buses[v][2], w0) and (i,t,w) != (buses[v][1], buses[v][3], w0):
    #                     for j in adjacency_list[i]:
    #                         if j != i:
    #                             for t_zeg in T:
    #                                 if t_zeg != t:
    #                                     for w_zeg in W:
    #                                         if w_zeg != w:
    #                                             sum_term1 += x[v, (i,j,t,t_zeg,w,w_zeg)]

    #                     for j_prime in adjacency_list[i]:
    #                         if j_prime != i:
    #                             for t_prime in T:
    #                                 if t_prime != t:
    #                                     for w_prime in W:
    #                                         if w_prime != w:
    #                                             sum_term2 += x[v, (j_prime,i,t_prime,t,w_prime,w)]
                                        
    #     model.add_constraint(sum_term1 - sum_term2 == 0, 
    #                         ctname='flow_balance_intermediate_{0}'.format(v))
    
    for v in V:
        sum_term1 = 0
        sum_term2 = 0
        for (i,j,t,t_prime,w,w_prime) in Av:
            for j_prime in adjacency_list[i]:
                if j_prime != j:
                    for t_zeg in T:
                        if t_zeg != t:
                            for w_zeg in W:
                                # if w_zeg != w:
                                    if ((i,t,w) != (buses[v][0], buses[v][2], w0)) and ((i,t,w) != (buses[v][1], buses[v][3], w0)):
                                        sum_term1 += x[v, (i,j,t,t_zeg,w,w_zeg)]
                                        sum_term2 += x[v, (j_prime,i,t_prime,t,w_prime,w)]
        model.add_constraint(sum_term1 - sum_term2 == 0, 
                            ctname='flow_balance_intermediate_{0}'.format(v))
    
    # for v in V:
    #     model.add_constraint(
    #         model.sum(x[v, (i,j,t,t_zeg,w,w_zeg)] - x[v, (j_prime,i,t_prime,t,w_prime,w)]
    #             for (i,j,t,t_prime,w,w_prime) in Av 
    #             for j_prime in adjacency_list[i] if j_prime != i
    #             for t_zeg in T if t_zeg != t
    #             for w_zeg in W if w_zeg != w
    #             if (i not in {buses[v][0], buses[v][1]}) and (t not in {buses[v][2], buses[v][3]})
    #             and (w != w0)
    #             ) == 0,
    #                 ctname='flow_balance_intermediate_{0}'.format(v))

    # for v in V:
    #     model.add_constraint(
    #         model.sum(x[v, (i,j,t,t_zeg,w,w_zeg)] - x[v, (j_prime,i,t_prime,t,w_prime,w)]
    #             for (i,j,t,t_prime,w,w_prime) in Av 
    #             for j_prime in adjacency_list[i] if j_prime != i
    #             for t_zeg in T if t_zeg != t
    #             for w_zeg in W if w_zeg != w
    #             if ((i,t,w) != (buses[v][0], buses[v][2], w0)) and ((i,t,w) != (buses[v][1], buses[v][3], w0))
    #             ) == 0,
    #                 ctname='flow_balance_intermediate_{0}'.format(v))

    print("Flow Balance Intermediate Constraint: " + get_time())

    # Define the student loading request constraint
    for p in P:
        model.add_constraint(model.sum(
            x[v, (i,j,t,t_prime,w,w_prime)] * (sum(w_prime) - sum(w)) 
            for v in V for (i,j,t,t_prime,w,w_prime) in Psi_p[p]) == stops[p][1],
            ctname='student_loading_request_{0}'.format(p)
        )

    print("Model Sovle Start: " + get_time())

    solution = model.solve()

    print("Model Sovle Finish: " + get_time())

    chosen_arcs = {v: [] for v in V}

    if solution:
        # Retrieve and store the values of the decision variables that are 1
        for v in V:
            for (i, j, t, t_prime, w, w_prime) in Av:
                var_value = solution.get_value(x[v, (i, j, t, t_prime, w, w_prime)])
                if var_value == 1:
                    chosen_arcs[v].append((i, j, t, t_prime, w, w_prime))

        print("Objective value:", model.objective_value)

    else:
        print("The model could not be solved.")

    return chosen_arcs

def main():

    capacity = 6

    base_directory = "Inputs/Very Small Sample/"
    buses = get_buses(base_directory + "Buses.txt")
    stops = get_stops(base_directory + "People.txt")
    schools, depots = get_schools_and_depots(read_nodes(base_directory + "Nodes.txt"))
    graph = create_graph(base_directory + "Nodes.txt",base_directory + "Edges.txt")
    start_t, finish_t = get_start_finish_t(schools, stops)

    chosen_arcs = optimize_model(buses, stops, schools, depots, graph, start_t, finish_t, capacity)

    with open(base_directory + "/Solution/Solution.json", "w") as json_file:
        json.dump(chosen_arcs, json_file, indent=4)

if __name__ == "__main__":
    main()

