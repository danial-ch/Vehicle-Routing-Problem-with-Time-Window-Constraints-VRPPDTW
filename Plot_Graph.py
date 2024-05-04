#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Vehicle Routing Problem with time window constraints using DOcplex

This script allows the user to solve the Vehicle Routing Problem with time window constraints or
VRPPDTW using the DOcplex solver.

This is an implementation of the following paper:
Desaulniers, G., Desrosiers, J., Erdmann, A., Solomon, M.M., & Soumis, F. (2002). 
VRP with Pickup and Delivery. The Vehicle Routing Problem, 9, pp.225-242.
"""
__author__ = "Danial Chekani"
__email__ = "danialchekani@arizona.edu"
__status__ = "Dev"

import os
from pathlib import Path
import sys
from PIL import Image
import keyboard
from Parsing import get_full_graph
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import networkx as nx
import json

def get_node_label(node):
    if node[1]['name'] != None:
        return node[1]['name']
    else:
        return ""

def base_graph(G, ax, pos, label_edges = True):
    # Draw nodes with different colors based on node types
    node_colors = []
    for node_data in G.nodes(data=True):
        node = node_data[0]
        if 'node_type' in node_data[1] and node_data[1]['node_type'] == 'Pickup Node':
            node_colors.append('green')
        elif 'node_type' in node_data[1] and node_data[1]['node_type'] == 'Delivery Node':
            node_colors.append('blue')
        elif 'node_type' in node_data[1] and node_data[1]['node_type'] == 'Depot Node':
            node_colors.append('red')
        else:
            node_colors.append('gray')  # Default color
        ax.text(pos[node][0], pos[node][1], str(node_data[1]['node_id']), fontsize=8, ha='center', va='center', color="white")
        
    nx.draw_networkx_nodes(G, pos, ax=ax, node_size=100, node_color=node_colors)
    nx.draw_networkx_edges(G, pos, ax=ax, edge_color='black', width=0.5, arrows=False)

    if label_edges:
        node_labels = {node[1]['node_id']: get_node_label(node) for node in G.nodes(data=True)}
        for node, label in node_labels.items():
            node_pos = pos[node]
            x_offset = 0.5
            y_offset = -0.8
            label_pos = [node_pos[0] + x_offset, node_pos[1] + y_offset]
            plt.text(*label_pos, label, ha='center', va='center', fontsize=6, 
                    bbox=dict(boxstyle="round", facecolor='lightblue', alpha=0.3, edgecolor="none"))
        
        edge_labels = nx.get_edge_attributes(G, 'weight')
        nx.draw_networkx_edge_labels(G, pos, ax=ax, edge_labels=edge_labels, font_size=7)
    
    # Draw grid lines and grid numbers
    x_values = [pos[node][0] for node in G.nodes()]
    y_values = [pos[node][1] for node in G.nodes()]
    center_x = (min(x_values) + max(x_values)) / 2
    center_y = (min(y_values) + max(y_values)) / 2

    ax.grid(True, linestyle='-', linewidth=0.3, color='gray', zorder=0)
    # Set the x and y ticks with increments of 1
    x_ticks = range(int(min(x_values)), int(max(x_values)) + 1)
    y_ticks = range(int(min(y_values)), int(max(y_values)) + 1)
    ax.set_xticks(x_ticks)
    ax.set_yticks(y_ticks)
    ax.axhline(y=center_y,linewidth=1)
    ax.axvline(x=center_x,linewidth=1)
    
    # Create legend
    legend_handles = [mpatches.Patch(color='green', label='pickup Node'),
                      mpatches.Patch(color='blue', label='Delivery Node'),
                      mpatches.Patch(color='red', label='Depot Node'),
                      mpatches.Patch(color='gray', label='Junction Node')]
    prop = {'size': 7}  # Adjust font size as needed
    ax.legend(handles=legend_handles, prop=prop)
    
    return ax

def plot_base_graph(graph, pos):
    
    fig, ax = plt.subplots(figsize=(8, 6))
    ax = base_graph(graph, ax, pos, True)
    plt.show()

def plot_overall_solution(graph, pos, solution_dir):

    with open(solution_dir + "chosen_x_ijk.json", "r") as json_file:
        chosen_x_ijk = json.load(json_file)

    graph.remove_edges_from(list(graph.edges()))

    bus_cnt = 0
    for bus, arc in chosen_x_ijk.items():
        fig, ax = plt.subplots(figsize=(8, 6))
        fig.suptitle('Bus ' + str(bus_cnt) , fontsize=20)
        ax.clear()
        graph.add_edges_from(arc)
        ax = base_graph(graph, ax, pos, False)

        nx.draw_networkx_edges(graph, pos, ax=ax,
                               edge_color='red', width=1, arrows=True)
        graph.remove_edges_from(arc)
        bus_cnt += 1

    plt.show()

space_pressed = False

def on_key_press(event):
    global space_pressed
    if event.key == ' ':
        space_pressed = True
    elif event.key == 'q':
        sys.exit()

def plot_step_by_step(graph, pos, solution_dir, Gif=False):
    global space_pressed

    # Read the JSON file
    with open(solution_dir + "buses_paths.json", "r") as json_file:
        buses_paths = json.load(json_file)

    gif_dir = solution_dir + "Gifs/"

    if not os.path.exists(gif_dir) and Gif:
        os.makedirs(gif_dir)

    bus_cnt = 0
    for bus, movements in buses_paths.items():
        total_cost = 0
        fig, ax = plt.subplots(figsize=(8, 6))
        fig.suptitle('Bus ' + str(bus_cnt) , fontsize=20)
        fig.canvas.mpl_connect('key_press_event', on_key_press)
        ax = base_graph(graph, ax, pos, False)

        valid_movements = []
        for info in movements:
            if len(info['path']) > 1:
                valid_movements.append(info)

        for idx, info in enumerate(valid_movements):
            paths = info['path']
            ax.clear()
            ax = base_graph(graph, ax, pos, False)
            y_lim = plt.ylim()
            x_lim = plt.xlim()
            plt.ylim(y_lim[0], y_lim[1] * 1.2)

            x_center = (x_lim[0] + x_lim[1]) / 2

            if Gif:
                text = info['status']
                plt.text(x_center, y_lim[1] * 1.1, text, ha='center', va='center', 
                         fontsize=10, color='white',
                    bbox=dict(boxstyle="round", facecolor='black', edgecolor="none"))

                load_text = f"Load : {info['start_load']} -> {info['finish_load']}"
                plt.text(x_lim[0], y_lim[1] * 1.15, load_text, ha='left', 
                         va='center', fontsize=8, color='white',
                    bbox=dict(boxstyle="round", facecolor='purple', edgecolor="none"))
                
                time_text = f"Time : {info['start_time']} -> {info['finish_time']}"
                plt.text(x_lim[0], y_lim[1] * 1.05, time_text, ha='left', 
                         va='center', fontsize=8, color='white',
                         bbox=dict(boxstyle="round", facecolor='blue', edgecolor="none"))
                
                total_cost += int(info['path_cost'])
                cost_text = f"Cost : {info['path_cost']} - total Cost : {total_cost}"
                plt.text(x_lim[0], y_lim[1] * 0.95, cost_text, ha='left', 
                         va='center', fontsize=8, color='white',
                         bbox=dict(boxstyle="round", facecolor='brown', edgecolor="none"))
                    
                edges = list(zip(paths, paths[1:]))
                nx.draw_networkx_edges(graph, pos, edgelist=edges, ax=ax, edge_color='r', 
                                       width=2, arrows=True)
                
                frame_filename = gif_dir + f'Bus_{bus}_frame_{idx}.png'
                fig.savefig(frame_filename)
                
            else:
                text = info['status']
                plt.text(x_center, y_lim[1] * 1.1, text, ha='center', va='center', 
                            fontsize=10, color='white',
                    bbox=dict(boxstyle="round", facecolor='black', edgecolor="none"))

                load_text = f"Load : {info['start_load']} -> {info['finish_load']}"
                plt.text(x_lim[0], y_lim[1] * 1.15, load_text, ha='left', 
                            va='center', fontsize=8, color='white',
                    bbox=dict(boxstyle="round", facecolor='purple', edgecolor="none"))
                
                time_text = f"Time : {info['start_time']} -> {info['finish_time']}"
                plt.text(x_lim[0], y_lim[1] * 1.05, time_text, ha='left', 
                            va='center', fontsize=8, color='white',
                    bbox=dict(boxstyle="round", facecolor='blue', edgecolor="none"))
                
                total_cost += int(info['path_cost'])
                cost_text = f"Cost : {info['path_cost']} - total Cost : {total_cost}"
                plt.text(x_lim[0], y_lim[1] * 0.95, cost_text, ha='left', 
                         va='center', fontsize=8, color='white',
                         bbox=dict(boxstyle="round", facecolor='brown', edgecolor="none"))
                
                edges = list(zip(paths, paths[1:]))
                nx.draw_networkx_edges(graph, pos, edgelist=edges, ax=ax, edge_color='r', 
                                        width=2, arrows=True)

                while not space_pressed:
                    plt.pause(0.1)
                space_pressed = False

        if Gif:
            frames = [Image.open(f'{gif_dir}/{frame}') for frame in sorted(os.listdir(gif_dir)) 
                      if frame.endswith(".png")]
            gif_filename = f'{gif_dir}/bus_{bus}.gif'
            frames[0].save(gif_filename, format='GIF', append_images=frames[1:], 
                        save_all=True, duration=1000, loop=0)
            [f.unlink() for f in Path(gif_dir).glob("*") if f.name.endswith(".png")] 
        
        bus_cnt += 1
        plt.close(fig)

    if not Gif:
        plt.show()

def main():
    # Specify the folder name under the Inputs folder
    print("-------------")
    problem_dir = input("Enter folder name of the problem\n")

    base_directory = "Samples/" + problem_dir + "/"
    solution_dir = base_directory + "Solution/"

    print("Enter the operation number")
    print("1-Plot Base Graph")
    print("2-Plot Overall Solution")
    print("3-Plot Step By Step Solution")
    print("4-Create Step By Step Gif")
    operation = input()
    
    graph, requests = get_full_graph(base_directory)
    pos = {node_data[0]: (node_data[1]['x'], node_data[1]['y']) for node_data in graph.nodes(data=True)}

    if operation == "1":
        plot_base_graph(graph, pos)
    elif operation == "2":
        plot_overall_solution(graph, pos, solution_dir)
    elif operation == "3":
        plot_step_by_step(graph, pos, solution_dir, Gif=False)
    elif operation == "4":
        plot_step_by_step(graph, pos, solution_dir, Gif=True)

if __name__ == "__main__":
    main()
