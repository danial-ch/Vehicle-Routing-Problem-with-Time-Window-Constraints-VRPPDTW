from Parsing_VRPPDTW import get_full_graph
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Circle
import networkx as nx

base_directory = "Inputs/VRPPDTW/"

def plot_graph(G, label_edges = True):
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
    
    # Draw edges with different colors based on edge attributes
    edge_colors = [attr.get('color', 'black') for u, v, attr in G.edges(data=True)]
    nx.draw_networkx_edges(G, pos, ax=ax, edge_color=edge_colors, width=1, arrows=False)

    # Draw edge labels with weights
    if label_edges:
        edge_labels = nx.get_edge_attributes(G, 'weight')
        nx.draw_networkx_edge_labels(G, pos, ax=ax, edge_labels=edge_labels)
    
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
    
    return fig, ax

if __name__ == "__main__":

    graph, requests = get_full_graph(base_directory)
    
    plot_graph(graph)
    plt.show()