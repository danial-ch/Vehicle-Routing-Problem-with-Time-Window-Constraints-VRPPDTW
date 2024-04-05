from Draw_Base_Graph import plot_graph
from Parsing import create_graph
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import networkx as nx
import json

base_directory = "Inputs/Sample 1/"

def draw_solution(G, arcs):

    pos = {node_data[0]: (node_data[1]['x'], node_data[1]['y']) for node_data in G.nodes(data=True)}

    for bus, routes in arcs.items():

        fig, ax = plot_graph(G)

        # Plot the route taken by the bus
        for route in routes:
            # Extracting route information
            for i in range(len(route) - 1):
                source_node = route[i][:2]  # Start node (i, j)
                target_node = route[i + 1][:2]  # End node (i, j)
                nx.draw_networkx_edges(G, pos, edgelist=[(source_node, target_node)], ax=ax, edge_color='red', width=1)

        # Save the plot as an image
        plt.savefig(base_directory + "bus_{}.png".format(bus))

        # Close the plot to release memory
        plt.close()

if __name__ == "__main__":
    
    nodes_file = base_directory + "Nodes.txt"
    edges_file = base_directory + "Edges.txt"
    graph = create_graph(nodes_file, edges_file)

    # Read the JSON file
    with open(base_directory + "Solution.json", "r") as json_file:
        arcs = json.load(json_file)

    draw_solution(graph, arcs)