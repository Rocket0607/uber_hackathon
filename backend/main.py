from dwave.system import DWaveSampler, EmbeddingComposite, LeapHybridSampler
import dwave.inspector
from dimod import BinaryQuadraticModel, ExactSolver
import networkx as nx

import matplotlib.pyplot as plt

from flask import Flask, request

app = Flask(__name__)

@app.route("/home")
def main():
    def cycle_search(curr_node, curr_edge_list, visited_queue):
            # check if cycle is detected, if so add it to cycles list and delete that part of the queue
            if curr_node in visited_queue:
                cycles.append(visited_queue[visited_queue.index(curr_node):])
            
            # if the node is at a dead end, return
            if len(curr_edge_list[curr_node - 1]) == 0:
                return
            
            # run cycle search on all other nodes
            visited_queue.append(curr_node)
            while True:
                if len(curr_edge_list[curr_node-1]):
                    edge = curr_edge_list[curr_node - 1][0]
                    next_node = int(edge.split('_')[2])
                    curr_edge_list[curr_node - 1].remove(edge)
                    curr_edge_list[next_node - 1].remove("X_"+str(next_node)+"_"+str(curr_node))
                    cycle_search(next_node, curr_edge_list, visited_queue)
                else:
                    break
            return

    def remove_duplicates():
        to_remove = []
        for i in range(len(edges)):
            for j in range(len(edges[i])):
                node1 = int(edges[i][j].split('_')[1])
                node2 = int(edges[i][j].split('_')[2])
                if f"X_{node2}_{node1}" in edges[node2 - 1]:
                    if len(edges[node2 - 1]) == 1:
                        to_remove.append(f"X_{node1}_{node2}")
                    else:
                        edges[node2 - 1].remove(f"X_{node2}_{node1}")
            for j in range(len(to_remove)):
                edges[i].remove(to_remove[j])
            to_remove = []

    def add_constraints():
        # constraint 1: there will be num_nodes - 1 edges
        # generate c1 list, which includes all possible edges, each with a bias of 1
        # README: this constraint only works num_nodes is accurate. 
        #         if nodes are left out of the tree, and included in num_nodes, the constraint will enforce every node being connected
        c1 = []
        for i in range(len(edges)):
            for j in range(len(edges[i])):
                c1.append((edges[i][j], 1))
        bqm.add_linear_equality_constraint(
            c1,
            constant = -(num_nodes - 1),
            lagrange_multiplier = 5000
        )

        # constraint 2: every node should be connected to at least one edge
        for i in range(len(edges)):
            c2 = []
            for j in range(len(edges[i])):
                print("appending to c2: ", edges[i][j])
                c2.append((edges[i][j], 1))
            print("c2_"+str(i+1)+": ", c2)
            if (len(c2) != 0):
                bqm.add_linear_inequality_constraint(
                    c2,
                    lb = 1,
                    ub = 10,
                    lagrange_multiplier = 15000000,
                    label = "c2_"+str(i + 1)
                )
        
        # constraint 3: every cycle must have at least one remove edge
        for i in range(len(cycles)):
            c3 = []
            c3.append((f"X_{cycles[i][0]}_{cycles[i][-1]}", 1))
            for j in range(len(cycles[i]) - 1):
                c3.append((f"X_{cycles[i][j]}_{cycles[i][j+1]}", 1))

            print("c3:", c3)
            bqm.add_linear_equality_constraint(
                c3,
                constant = -(len(cycles[i]) - 1),
                lagrange_multiplier = 4000,
            )
        # constraint 3:
        # for i in range(len(nodes)):
        #     c3 = []
        #     for j in range(len(edges)):
        #         if (int(edges[j].split('_')[1]) == nodes[i] and depths[nodes.index(nodes[i])] > depths[nodes.index(int(edges[j].split('_')[2]))]):
        #             print("appending: ", int(edges[j].split('_')[1]), " or ", int(edges[j].split('_')[2]), " from ", edges[j].split('_'))
        #             c3.append((edges[j], 1))
        #         elif (int(edges[j].split('_')[2]) == nodes[i] and depths[nodes.index(nodes[i])] > depths[nodes.index(int(edges[j].split('_')[1]))]):
        #             print("appending: ", int(edges[j].split('_')[1]), " or ", int(edges[j].split('_')[2]), " from ", edges[j].split('_'))
        #             c3.append((edges[j], 1))
        #     print("c3_"+str(i)+": ", c3)
        #     if (len(c3) != 0):
        #         bqm.add_linear_inequality_constraint(
        #             c3,
        #             lb = 1,
        #             ub = len(c3),
        #             lagrange_multiplier = 1000,
        #             label = "c3_"+str(i + 1)
        #         )
    json = request.get_json()
    input_edges = json["edges"]
    num_nodes = json["num_nodes"]
    edges = [[] for i in range(num_nodes)]
    distances = [[] for i in range(num_nodes)]
    resistances = [[] for i in range(num_nodes)]
    for edge in input_edges:
        edge = edge.split()
        node1 = int(edge[0])
        node2 = int(edge[1])
        distance = float(edge[2])
        resistance = float(edge[3])
        if (node1 == node2):
            return("node1 and node2 cannot be the same")
            continue
        # if the first node is out of bounds, error then continue
        if (node1 > num_nodes or node1 < 1):
            return("node 1 is out of bounds")
            continue
        # if the second node isout of bounds, error then continue
        if (node2 > num_nodes or node2 < 1):
            return("node 2 is out of bounds")
            continue
        # if the edge is already in the list, error then continue
        if (f"X_{node1}_{node1}" in edges):
            return("edge already contained in list")
            continue
        # if the same edge, just from node2 to node1 is in the list, error then continue
        if (f"X_{node2}_{node1}" in edges):
            return("edge already contained in list")
            continue
        
        edges[node1-1].append(f"X_{node1}_{node2}")
        edges[node2-1].append(f"X_{node2}_{node1}")
        distances[node1-1].append(distance)
        distances[node2-1].append(distance)
        resistances[node1-1].append(resistance)
        resistances[node2-1].append(resistance)

    cycles = []
    cycle_search(1, [x[:] for x in edges], [])
    print(cycles)
    remove_duplicates()
    print(edges)

    # Initialise BQM
    bqm = BinaryQuadraticModel("BINARY")

    distance_scalar = 100
    resistance_scalar = 3

    # # objective: min(sum of the distances of the edges)
    for i in range(len(edges)):
        for j in range(len(edges[i])):
            bqm.add_variable(edges[i][j], distance_scalar * distances[i][j] + resistance_scalar * resistances[i][j])

    add_constraints()

    #sampler = EmbeddingComposite(DWaveSampler())
    #response = sampler.sample(bqm, num_reads=1000)

    sampler = ExactSolver()
    response = sampler.sample(bqm)

    # sampler = LeapHybridSampler(token="DEV-c9a363b31191890cb20b75ad57be0b71b583f88d")
    # response = sampler.sample(bqm)
    print(response.first.sample)
    print(type(response.first.sample))
    output = response.first.sample
    for key in output.keys():
        output[key] = int(output[key])
    return output