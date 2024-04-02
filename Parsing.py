import networkx as nx

def read_nodes(filename):
    nodes = []
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
            elif node_type == 2:
                attributes['node_type'] = 'Depot Node'
            node = {'node_id': node_id, 'x': x, 'y': y, 'name': name, **attributes}
            nodes.append(node)
    return nodes

def read_edges(filename):
    edges = []
    with open(filename, 'r') as file:
        for line in file:
            line = line.strip()
            if line.startswith('#') or not line.strip():
                continue  # Ignore comment lines and empty lines
            data = line.split('|')
            edge_id, source, target, weight = data
            edges.append((int(source), int(target), float(weight)))
    return edges

def create_graph(nodes_file, edges_file):
    G = nx.Graph()
    
    nodes = read_nodes(nodes_file)
    edges = read_edges(edges_file)
    
    for node_data in nodes:
        node_id = node_data['node_id']
        G.add_node(node_id, **node_data)
    
    for edge in edges:
        source, target, weight = edge
        G.add_edge(source, target, weight=weight)
    
    return G
