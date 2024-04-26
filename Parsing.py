import networkx as nx

def get_full_graph(base_directory):
    nodes_file = base_directory + "Nodes.txt"
    edges_file = base_directory + "Edges.txt"
    graph = create_graph(nodes_file, edges_file)
    stops = get_stops(base_directory + "People.txt")

    return graph, stops

def convert_to_minutes(time_str):
    # Split the string into hours and minutes
    parts = time_str.split(':')
    
    # Convert hours to minutes
    if len(parts) == 2:
        hours = int(parts[0])
        minutes = int(parts[1])
    else:
        hours = int(time_str)
        minutes = 0
    
    # Convert to total minutes
    total_minutes = hours * 60 + minutes
    return total_minutes

def read_nodes(filename):
    nodes = {}
    with open(filename, 'r') as file:
        for line in file:
            line = line.strip()
            if line.startswith('#') or not line.strip():
                continue  # Ignore comment lines and empty lines
            data = line.split('|')
            node_id = int(data[0])
            x = float(data[1])
            y = float(data[2])
            node_type = int(data[3])
            name = data[4] if len(data) > 4 else None
            attributes = {}
            if node_type == 0:
                attributes['node_type'] = 'Junction Node'
            elif node_type == 1:
                attributes['node_type'] = 'School Node'
                attributes['earliest_arrival'] = convert_to_minutes(data[5])
                attributes['latest_arrival'] = convert_to_minutes(data[6])
            elif node_type == 2:
                attributes['node_type'] = 'Depot Node'
            node = {'node_id': node_id, 'x': x, 'y': y, 'name': name, **attributes}
            nodes[node_id] = node
    return nodes

def read_edges(filename):
    edges = {}
    with open(filename, 'r') as file:
        for line in file:
            line = line.strip()
            if line.startswith('#') or not line.strip():
                continue  # Ignore comment lines and empty lines
            data = line.split('|')
            edge_id, source, target, weight = data
            edges[edge_id] = {'edge_id': edge_id, 'origin': int(source), 
                              'destination': int(target), 'travel_time': float(weight)}
    return edges

def create_graph(nodes_file, edges_file):
    G = nx.DiGraph()
    
    nodes = read_nodes(nodes_file)
    edges = read_edges(edges_file)
    
    for index, (key, value) in enumerate(nodes.items(), start=0):
        G.add_node(index, **value)

    for index, (key, edge) in enumerate(edges.items(), start=0):
        G.add_edge(edge['origin'], edge['destination'], 
                   weight=edge['travel_time'], id=edge['edge_id'])
        G.add_edge(edge['destination'], edge['origin'], 
                   weight=edge['travel_time'], id=edge['edge_id'])
    
    return G

def get_schools_and_depots(nodes):
    schools = {}
    depots = {}
    for (key, node) in enumerate(nodes.items(), start=0):
        if node[1]['node_type'] == 'School Node':
            schools[node[1]['node_id']] = node
        elif node[1]['node_type'] == 'Depot Node':
            depots[node[1]['node_id']] = node
    return schools, depots

def get_stops(filename):
    stops = {}
    with open(filename, 'r') as file:
        for line in file:
            line = line.strip()
            if line.startswith('#') or not line.strip():
                continue  # Ignore comment lines and empty lines
            data = line.split('|')
            person_id = int(data[0])
            edge_i = int(data[1])
            edge_j = int(data[2])
            destination = int(data[3])
            earliest_departure = convert_to_minutes(data[4])
            latest_departure = convert_to_minutes(data[5])
            stop_key = (destination, earliest_departure, latest_departure, edge_i, edge_j)
            if stop_key in stops:
                stops[stop_key] += 1
            else:
                stops[stop_key] = 1
    stops_list = [(stop[0], n_p, stop[1], stop[2], stop[3], stop[4]) for stop, n_p in stops.items()]

    stops_dict = {index: stop for index, stop in enumerate(stops_list)}

    return stops_dict

def get_buses(filename):
    buses = {}
    with open(filename, 'r') as file:
        for line in file:
            line = line.strip()
            if line.startswith('#') or not line.strip():
                continue  # Ignore comment lines and empty lines
            data = line.split('|')
            bus_id = int(data[0])
            origin_id = int(data[1])
            destination_id = int(data[2])
            earliest_time = convert_to_minutes(data[3])
            latest_time = convert_to_minutes(data[4])
            buses[bus_id] = (origin_id, destination_id, earliest_time, latest_time)
    return buses