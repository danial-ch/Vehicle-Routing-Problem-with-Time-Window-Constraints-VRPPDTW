from Draw_Base_Graph_VRPPDTW import plot_graph
from Parsing_VRPPDTW import get_full_graph
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import networkx as nx
import json

base_directory = "Inputs/VRPPDTW/"

if __name__ == "__main__":
    
    G, requests = get_full_graph(base_directory)

    # Read the JSON file
    with open(base_directory + "/Solution/chosen_x_ijk.json", "r") as json_file:
        chosen_x_ijk = json.load(json_file)

    for bus, arc in chosen_x_ijk.items():
        fig, ax = plt.subplots(figsize=(8, 6))
        pos = {node_data[0]: (node_data[1]['x'], node_data[1]['y']) for node_data in G.nodes(data=True)}

        # Draw nodes with different colors based on node types
        node_colors = []
        for node_data in G.nodes(data=True):
            node = node_data[0]
            if 'node_type' in node_data[1] and node_data[1]['node_type'] == 'Pickup Node':
                node_colors.append('green')
            elif 'node_type' in node_data[1] and node_data[1]['node_type'] == 'Delivery Node':
                node_colors.append('blue')
            else:
                node_colors.append('gray')  # Default color
            ax.text(pos[node][0], pos[node][1], str(node_data[1]['node_id']), fontsize=8, ha='center', va='center', color="white")
            
        nx.draw_networkx_nodes(G, pos, ax=ax, node_size=100, node_color=node_colors)

        G.remove_edges_from(list(G.edges()))

        G.add_edges_from(arc)

        nx.draw_networkx_edges(G, pos, ax=ax, edge_color='black', width=1, arrows=False)

    plt.show()