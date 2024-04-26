from Draw_Base_Graph import plot_graph
from Parsing import create_graph, get_full_graph
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import networkx as nx
import json

base_directory = "Inputs/Very Small Sample/"

def draw_solution(G, stops, arcs):

    pos = {node_data[0]: (node_data[1]['x'], node_data[1]['y']) for node_data in G.nodes(data=True)}

    for bus, routes in arcs.items():

        fig, ax = plot_graph(G, stops, label_edges=False)

        # Plot the route taken by the bus
        circle_radius = 0.35
        for i, route in enumerate(routes):
            # Extracting route information
            nx.draw_networkx_edges(G, pos, edgelist=[(route[0], route[1])], ax=ax, edge_color='red', width=2, arrows=True)
            x1, y1 = pos[route[0]]
            x2, y2 = pos[route[1]]
            symbol_position = ((x1 + x2) / 2 , (y1 + y2) / 2)
            circle = mpatches.Circle(symbol_position, radius=circle_radius, edgecolor='none', facecolor='red')
            ax.add_patch(circle)
            ax.text(symbol_position[0], symbol_position[1], str(i), fontsize=8, color='white', ha='center', va='center')

        # Save the plot as an image
        plt.savefig(base_directory + "/Solution/bus_{}.png".format(bus), dpi=300)

        # Close the plot to release memory
        plt.close()

if __name__ == "__main__":
    
    graph, stops = get_full_graph(base_directory)

    # Read the JSON file
    with open(base_directory + "/Solution/Solution.json", "r") as json_file:
        arcs = json.load(json_file)

    draw_solution(graph, stops, arcs)