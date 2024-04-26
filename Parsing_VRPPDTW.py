import networkx as nx

def get_full_graph(base_directory):
    nodes_file = base_directory + "Nodes.txt"
    edges_file = base_directory + "Edges.txt"
    requests = get_requests(base_directory + "Requests.txt")
    graph = create_graph(nodes_file, edges_file, requests)

    return graph, requests

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

def read_nodes(nodes_file, requests):
    nodes = {}
    with open(nodes_file, 'r') as file:
        for line in file:
            line = line.strip()
            if line.startswith('#') or not line.strip():
                continue  # Ignore comment lines and empty lines
            data = line.split('|')
            node_id = int(data[0])
            x = float(data[1])
            y = float(data[2])
            name = data[3] if len(data) > 3 else None
            node = {'node_id': node_id, 'x': x, 'y': y, 'name': name, 'node_type' : 'Junction Node'}
            nodes[node_id] = node

    for request_id, request in requests.items():
        origin, destination, count, _, _, _, _, _, _ = request
        nodes[origin]['node_type'] = 'Pickup Node'
        nodes[destination]['node_type'] = 'Delivery Node'
        
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

def create_graph(nodes_file, edges_file, requests):
    G = nx.DiGraph()
    
    nodes = read_nodes(nodes_file, requests)
    edges = read_edges(edges_file)
    
    for index, (key, value) in enumerate(nodes.items(), start=0):
        G.add_node(index, **value)

    for index, (key, edge) in enumerate(edges.items(), start=0):
        G.add_edge(edge['origin'], edge['destination'], 
                   weight=edge['travel_time'], id=edge['edge_id'])
        G.add_edge(edge['destination'], edge['origin'], 
                   weight=edge['travel_time'], id=edge['edge_id'])
    
    return G

def get_requests(filename):
    requests = {}
    with open(filename, 'r') as file:
        for line in file:
            line = line.strip()
            if line.startswith('#') or not line.strip():
                continue  # Ignore comment lines and empty lines
            data = line.split('|')
            request_id = int(data[0])
            origin = int(data[1])
            destination = int(data[2])
            count = int(data[3])
            earliest_departure_o = convert_to_minutes(data[4])
            latest_departure_o = convert_to_minutes(data[5])
            service_time_o = convert_to_minutes(data[6])
            earliest_departure_d = convert_to_minutes(data[7])
            latest_departure_d = convert_to_minutes(data[8])
            service_time_d = convert_to_minutes(data[9])
            requests[request_id] = (origin, destination, count, earliest_departure_o, 
                                    latest_departure_o, service_time_o, earliest_departure_d,
                                    latest_departure_d, service_time_d)
    return requests

def get_vehicles(filename):
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
            capacity = int(data[3])
            buses[bus_id] = (origin_id, destination_id, capacity)
    return buses