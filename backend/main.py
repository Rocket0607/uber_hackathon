# DWave imports which we use to perform the quantum annealing
from dwave.system import DWaveSampler, EmbeddingComposite, LeapHybridSampler
from dimod import BinaryQuadraticModel, ExactSolver

# Flask import so that the API is accessible
from flask import Flask, request

# Creating the Flask app object
app = Flask(__name__)

# Creating the /route path (if the a request is made to the /route path, main() will run)
@app.route("/route")
def main():

    # Defining functions for use later in main() function

    # Cycle search is used when defining constraints. It traverses the graph that represents the map of the city and finds enough cycles (or loops)
    # for the program to use later on
    def cycle_search(curr_node, curr_edge_list, visited_queue):
            # check if cycle is detected, if so add it to cycles list and delete that part of the queue
            if curr_node in visited_queue:
                cycles.append(visited_queue[visited_queue.index(curr_node):])
            
            # if the node is at a dead end, return
            if len(curr_edge_list[curr_node - 1]) == 0:
                return
            
            # run cycle search on all other nodes
            visited_queue.append(curr_node)

            # recurse through other nodes, modifying the lists as necessary
            while True:
                if len(curr_edge_list[curr_node-1]):
                    edge = curr_edge_list[curr_node - 1][0]
                    next_node = int(edge.split('_')[2])
                    curr_edge_list[curr_node - 1].remove(edge)
                    curr_edge_list[next_node - 1].remove("X_"+str(next_node)+"_"+str(curr_node))
                    cycle_search(next_node, curr_edge_list, visited_queue)
                else:
                    # end this function if it is currently at a dead end (this will cause the function to continue running on the previous node)
                    break
            return

    # A function to remove duplicate values from the edges list. The duplicate values are necessary for detecting cycles and other functions, but are not
    # needed for the final result
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

    # A function that adds constraings to the quantum algorithm (commonly called Quadratic Unconstrained Binary Object or QUBO).
    # The constraints work by enforcing a certain number of items within a list. e.x. for the first example, we simply create a list with all the edges
    # and tell the quantum annealer how many of the edges in that list should be equal to 1 (or selected for the final path)
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

    # Getting request data using Flask (these are the inputs)
    json = request.get_json()
    public_transportation = json["public_transportation"]
    input_edges = json["edges"]
    num_nodes = json["num_nodes"]
    # Setting up lists that will be populated as we parse the inputs
    edges = [[] for i in range(num_nodes)]
    distances = [[] for i in range(num_nodes)]
    # go through each edge string in the input. Inputs are strucutred like this:
    # node1 node2 distance
    # So we can split the string to seperate the nodes and the distances between them, giving us information on the edge.
    # The nodes will primarily represent intersections and large points of interest and the edges are the roads/paths between them.
    for edge in input_edges:
        # splitting the input string using a python string method
        edge = edge.split()
        node1 = int(edge[0])
        node2 = int(edge[1])
        distance = float(edge[2])
        transport_mode = float(edge[3])
        # error checks making sure the input data is valid
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
        
        # appending the input data to the apprioate list
        # the lists are structured as a 2d array, where each edge is put into the sub-list with the index of its starting node. 
        # (edge 1 to 2 would be put in the first sub-array, or array with index 0)
        # this is to make running other functions (specifically search functions more efficient later on)
        edges[node1-1].append(f"X_{node1}_{node2}")
        edges[node2-1].append(f"X_{node2}_{node1}")
        distances[node1-1].append(distance)
        distances[node2-1].append(distance)

    # running the cycle search algorithm
    cycles = []
    cycle_search(1, [x[:] for x in edges], [])
    # removing the duplicates in the lists
    remove_duplicates()

    # Initialise BQM (Binary Quadratic Model) which we will use to sample (run) the quantum annealer on our data.
    bqm = BinaryQuadraticModel("BINARY")

    # definding scalars for how the different properties of roads will factor into the program. 
    # The higher the scalar -> the more important the property -> the more it affects the final result
    distance_scalar = 5
    resistance_scalar = 1000

    # defining the objective function, which tells the quantum annealer what variables to minimise. 
    # This is done by summing up all the proprties into one final weight, which is then minimised by the annealer
    # objective: min(sum of the distances of the edges)
    for i in range(len(edges)):
        for j in range(len(edges[i])):

            # TODO: add weight for how many other uber drivers are on that path
            # TODO: add negative weight for demand on that path
            bqm.add_variable(edges[i][j], distance_scalar * distances[i][j])

    add_constraints()

    # Sample using DWave QPU
    #sampler = EmbeddingComposite(DWaveSampler())
    #response = sampler.sample(bqm, num_reads=1000)

    # Sample using your local machine (simulates quantum processes)
    sampler = ExactSolver()
    response = sampler.sample(bqm)

    # Sample using hybrid sampler, generally the most efficient approach when working with large datasets
    # sampler = LeapHybridSampler(token="DEV-c9a363b31191890cb20b75ad57be0b71b583f88d")
    # response = sampler.sample(bqm)

    # converting the values in the output dictionary to python integers since the default type of the values (int8) is not JSON serialisable.
    output = response.first.sample
    for key in output.keys():
        output[key] = int(output[key])
    
    # Return the output, serving the data to whatever made the request.
    return output