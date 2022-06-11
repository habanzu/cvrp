from pyscipopt import Model, Pricer, SCIP_RESULT, SCIP_STAGE
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
import hygese as hgs
import sys, math, random

class VRP(Model):
    def __init__(self,graph):
        super().__init__()

        self.original_graph = graph
        self.graph = graph.copy()
        self.vars = {}
        self.cons = []

def create_constraints(model, G, heuristic_time=0):
    # Create a valid set of variables and the constraints to it
    for i in range(1,G.number_of_nodes()):
        #TODO: I should check, whether these paths are indeed feasible.
        path = (0,i,0)
        cost = nx.path_weight(G,path,"weight")
        var = model.addVar(vtype="C",obj=cost)
        model.vars[path] = var
        cons = model.addCons(var == 1, name=f"node_{i}",modifiable=True)
        model.cons.append(cons)

    # Add the convexity constraint, which limits the number of available vehicles
    convexity_constraint = model.addCons(sum(model.vars.values()) <= G.graph['min_trucks'], modifiable=True)
    model.cons.append(convexity_constraint)

    if heuristic_time != 0:
        paths = heuristic(model,heuristic_time)
        for path in paths:
            weight = nx.path_weight(G,path,"weight")
            var = model.addVar(vtype="C",obj=weight)
            counts = np.unique(path[1:-1], return_counts=True)
            for i, node in enumerate(counts[0]):
                model.addConsCoeff(model.cons[node-1], var ,counts[1][i])

            model.addConsCoeff(model.cons[-1], var, 1)

def output_variables(model, pricer):
    sol = model.getBestSol()
    # Flushing should probably prevent the console output from SCIP mix up with the following print
    sys.stdout.flush()

    elementary = True
    comp_value = 1e-6
    print("The solution contains the following paths: ")
    print(f"Only paths with associated value larger than {comp_value} are analysed.")
    for path, var in pricer.data['vars'].items():
        if sol[var] > 1e-6:
            counts = np.unique(path[1:-1], return_counts=True)
            for i, node in enumerate(counts[0]):
                if counts[1][i] != 1:
                    print("The following path is non elementary")
                    elementary = False
                    break
            print(f"{sol[var]} * {var}: {path}")

    if elementary:
        print("Solution contains only elementary paths.")
    else:
        print("Solution contains non elementary paths.")

def heuristic(model, time):
    ap = hgs.AlgorithmParameters(timeLimit=time)  # seconds
    hgs_solver = hgs.Solver(parameters=ap, verbose=False)
    data = dict()
    G = model.graph
    n = G.number_of_nodes()
    x_coords = [G.nodes[i]['coordinates'][0] for i in range(n)]
    y_coords = [G.nodes[i]['coordinates'][1] for i in range(n)]

    data['x_coordinates'] = x_coords
    data['y_coordinates'] = y_coords
    data['service_times'] = np.zeros(n)
    data['demands'] = [G.nodes[i]['demand'] for i in range(n)]
    data['vehicle_capacity'] = G.graph['capacity']
    data['num_vehicles'] = int(G.graph['min_trucks'])
    data['depot'] = 0

    result = hgs_solver.solve_cvrp(data)
    print(f"HYGESE: Found Solution with value {result.cost}")
    paths = []
    for res in result.routes:
        res.insert(0,0)
        res.append(0)
        path = tuple(res)
        paths.append(tuple(res))
    return paths

def create_example_1():
    G = nx.complete_graph(50)
    for (u, v) in G.edges():
        G.edges[u,v]['weight'] = random.randint(1,10)

    for node in G.nodes():
        G.nodes()[node]['demand'] = random.randint(1,10)

    G.graph['capacity'] = 20
    G.graph['min_trucks'] = 5
    return G

def create_example_2():
    G = nx.complete_graph(4)
    for (u, v) in G.edges():
        G.edges[u,v]['weight'] = 1
    G.edges[1,2]['weight'] = 1

    for node in G.nodes():
        G.nodes()[node]['demand'] = 2

    G.graph['capacity'] = 4
    G.graph['min_trucks'] = 2
    return G
