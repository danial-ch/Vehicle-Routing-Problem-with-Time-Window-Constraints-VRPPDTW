from Parsing import create_graph, get_buses, get_stops, get_schools_and_depots, read_nodes
import itertools
from docplex.mp.model import Model
import numpy as np
import json

def get_start_finish_t(schools, stops):
    """
    Get the start and finish times based on the latest arrival time
    from schools and earliest departure time from stops.
    """
    finish_t = max(school[1]['latest_arrival'] for school in schools.values())  # Get the highest latest arrival time
    start_t = min(stop[2] for stop in stops.values())  # Get the lowest earliest departure time
    return start_t, finish_t

def create_cost_matrix(graph):
    num_nodes = len(graph.nodes)
    cost_matrix = np.zeros((num_nodes, num_nodes))

    for u, v, data in graph.edges(data=True):
        cost_matrix[u][v] = data.get('weight', 1)
        cost_matrix[v][u] = data.get('weight', 1)

    return cost_matrix

def create_itw_cost(graph, N, T, W):

    cost_matrix = create_cost_matrix(graph)

    itw_cost = {}
    for i in N:
        for j in N:
            for t in T:
                for t_prime in T:
                    for w in W:
                        for w_prime in W:
                            itw_cost[(i, j, t, t_prime, w, w_prime)] = cost_matrix[i][j]

    return itw_cost

def create_psi_p(stops, T, W):
    Psi_p = {}

    for stop in stops.values():
        s_p, n_p, ep, lp, i, j = stop
        arcs = []
        
        # Generate all possible permutations of T and W
        permutations = list(itertools.product(T, T, W, W)) 
        for perm in permutations:
            t, t_prime, w, w_prime = perm
            arcs.append((i, j, t, t_prime, w, w_prime))
        
        Psi_p[stop] = arcs

    return Psi_p

def optimize_model(buses, stops, schools, depots, graph, t_start, t_finish, capacity):

    V = list(buses.keys())
    P = list(stops.keys())
    S = [school_data[1]['node_id'] for school_data in schools.values()]
    N = list(graph.nodes)
    T = list(range(t_start, t_finish))

    W = []
    n_schools = len(S)

    #!!!!! if all the people in the stop can't fit, it ignores it

    for state in itertools.product(P, repeat=n_schools):
        if sum(state) <= capacity:
            W.append(state)

    w0 = [0] * n_schools

    Psi_p = create_psi_p(stops, T, W)

    # Generate Av efficiently using itertools.product
    Av = list(itertools.product(
        itertools.permutations(N, 2),
        itertools.permutations(T, 2),
        itertools.permutations(W, 2)
    ))

    # Flatten the list of tuples
    Av = [tuple(itertools.chain.from_iterable(item)) for item in Av]

    cost = create_itw_cost(graph, N, T, W)

    # Create a model
    model = Model("MSBRP")

    x = model.binary_var_matrix(V, Av, name='x')

    # Define the objective function
    objective = model.sum(cost[i,j,t,t_prime,w,w_prime] * x[v, (i,j,t,t_prime,w,w_prime)] 
                          for v in V for (i,j,t,t_prime,w,w_prime) in Av)

    # Set the objective function as minimization
    model.minimize(objective)

    # Define the flow balance constraint
    for v in V:
        model.add_constraint(model.sum(x[v, (i,j,t,t_prime,w,w_prime)] 
                                       for (i,j,t,t_prime,w,w_prime) in Av 
                                       if i == buses[v][0] and t == buses[v][2] and w == w0) == 1, 
                                       ctname='flow_balance_{0}'.format(v))

    # Define the flow balance constraints at bus's destination vertex using add_constraint method
    for v in V:
        model.add_constraint(model.sum(x[v, (i,j,t,t_prime,w,w_prime)] 
                                       for (i,j,t,t_prime,w,w_prime) in Av 
                                       if j == buses[v][1] and t_prime == buses[v][3] and w in W) == 1,
                                       ctname='flow_balance_destination_{0}'.format(v))

    #????
    # Define the flow balance constraints at bus's intermediate vertex using add_constraint method
    for v in V:
        model.add_constraint(
            model.sum(x[v, (i,j,t,t_prime,w,w_prime)]
                      for (i,j,t,t_prime,w,w_prime) in Av 
                      if i != buses[v][0] and j != buses[v][1] and t != buses[v][2] 
                      and t_prime != buses[v][3] and w != w0)
            - model.sum(x[v, (i,j,t,t_prime,w,w_prime)] 
                        for (i,j,t,t_prime,w,w_prime) in Av
                        if i != buses[v][0] and j != buses[v][1] and t != buses[v][2] 
                        and t_prime != buses[v][3] and w != w0) == 0,
                    ctname='flow_balance_intermediate_{0}_{1}_{2}_{3}_{4}_{5}'.format(v, i, t, w, j, t_prime))

    # Define the student loading request constraint
    for p in P:
        model.add_constraint(model.sum(
            x[v, (i,j,t,t_prime,w,w_prime)] * (w_prime - w) 
            for v in V for (i,j,t,t_prime,w,w_prime) in Psi_p[p]) == stops[p][1],
            ctname='student_loading_request_{0}'.format(p)
        )

    # Solve the model
    solution = model.solve()

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

    base_directory = "Inputs/Small Sample/"
    buses = get_buses(base_directory + "Buses.txt")
    stops = get_stops(base_directory + "People.txt")
    schools, depots = get_schools_and_depots(read_nodes(base_directory + "Nodes.txt"))
    graph = create_graph(base_directory + "Nodes.txt",base_directory + "Edges.txt")
    start_t, finish_t = get_start_finish_t(schools, stops)

    chosen_arcs = optimize_model(buses, stops, schools, depots, graph, start_t, finish_t, capacity)

    with open(base_directory + "Solution.json", "w") as json_file:
        json.dump(chosen_arcs, json_file, indent=4)

if __name__ == "__main__":
    main()

