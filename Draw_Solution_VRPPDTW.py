from Draw_Base_Graph_VRPPDTW import plot_graph
from Parsing_VRPPDTW import get_full_graph
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import networkx as nx
import json

base_directory = "Inputs/VRPPDTW/"

if __name__ == "__main__":
    
    graph, requests = get_full_graph(base_directory)

    pos = {node_data[0]: (node_data[1]['x'], node_data[1]['y']) for node_data in graph.nodes(data=True)}

    # Read the JSON file
    with open(base_directory + "/Solution/buses_paths.json", "r") as json_file:
        buses_paths = json.load(json_file)

    for bus, movements in buses_paths.items():
        fig, ax = plt.subplots(figsize=(8, 6))
        for idx, info in enumerate(movements):
            paths = info['path']
            ax.clear()

            # Draw nodes with different colors based on node types
            node_colors = []
            for node_data in graph.nodes(data=True):
                node = node_data[0]
                if 'node_type' in node_data[1] and node_data[1]['node_type'] == 'Pickup Node':
                    node_colors.append('green')
                elif 'node_type' in node_data[1] and node_data[1]['node_type'] == 'Delivery Node':
                    node_colors.append('blue')
                else:
                    node_colors.append('gray')  # Default color
                ax.text(pos[node][0], pos[node][1], str(node_data[1]['node_id']), fontsize=8, ha='center', va='center', color="white")
                
            nx.draw_networkx_nodes(graph, pos, ax=ax, node_size=100, node_color=node_colors)

            nx.draw_networkx_edges(graph, pos, ax=ax, edge_color='black', width=1, arrows=False)

            # Draw grid lines and grid numbers
            ax.grid(True, linestyle='-', linewidth=0.5, color='gray', zorder=0)
            ax.set_xticks(range(-10, 11))
            ax.set_yticks(range(-10, 11))
            ax.axhline(0, color='black', linewidth=1.5)
            ax.axvline(0, color='black', linewidth=1.5)
            
            # Create legend
            legend_handles = [mpatches.Patch(color='green', label='pickup Node'),
                            mpatches.Patch(color='blue', label='Delivery Node'),
                            mpatches.Patch(color='red', label='Depot Node'),
                            mpatches.Patch(color='gray', label='Junction Node')]
            ax.legend(handles=legend_handles)

            if idx == 0:
                plt.pause(2)

            if idx == len(movements) - 1:
                edges = []
                for segment in movements:
                    path = segment['path']
                    if len(path) > 2:
                        for i in range(len(path) - 1):
                            edges.append((path[i],path[i+1]))
                    elif len(path) == 2:
                        edges.append(tuple(path))
                nx.draw_networkx_edges(graph, pos, edgelist=edges, ax=ax, edge_color='r', width=2, arrows=False)
            else:
                edges = list(zip(paths, paths[1:]))
                nx.draw_networkx_edges(graph, pos, edgelist=edges, ax=ax, edge_color='r', width=2, arrows=True)
            plt.pause(1)
    
    plt.show()

