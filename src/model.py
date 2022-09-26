from pyscipopt import Model, Pricer, SCIP_RESULT, SCIP_STAGE
import warnings, sys, math, random, time
warnings.simplefilter(action='ignore', category=FutureWarning)
import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
import hygese as hgs

from src.output import write_heuristic_results, write_attributes, write_heuristic_params

class VRP(Model):
    def __init__(self,graph):
        super().__init__()

        self.graph = graph
        self.vars = {}
        self.cons = []

def create_constraints(model, pricer, heuristic_time=0.001, heuristic_stale_it=2, heuristic_max_it=1e4):
    G = model.graph
    write_attributes(model.graph,pricer)
    # Create a valid set of variables and the constraints to it
    for i in range(1,G.number_of_nodes()):
        path = (0,i,0)
        cost = nx.path_weight(G,path,"weight")
        var = model.addVar(vtype="C",obj=cost)
        model.vars[path] = var
        cons = model.addCons(var == 1, name=f"node_{i}",modifiable=True)
        model.cons.append(cons)

    # Add the convexity constraint, which limits the number of available vehicles
    convexity_constraint = model.addCons(sum(model.vars.values()) <= G.graph['min_trucks'], modifiable=True)
    model.cons.append(convexity_constraint)

    # Add the paths returned by the heuristic of Vidal (section A.2)
    if heuristic_time > 0 and heuristic_max_it > 0:
        paths = heuristic(model,heuristic_time, heuristic_max_it, heuristic_stale_it, pricer.data['time_limit'])
        for path in paths:
            load = sum([G.nodes()[i]['demand'] for i in path[1:-1]])
            if load > G.graph['capacity']:
                raise ValueError(f"PRICER_PY ERROR: Load exceeds capacity. Load {load}")

            weight = nx.path_weight(G,path,"weight")
            var = model.addVar(vtype="C",obj=weight)
            counts = np.unique(path[1:-1], return_counts=True)
            for i, node in enumerate(counts[0]):
                model.addConsCoeff(model.cons[node-1], var ,counts[1][i])

            model.addConsCoeff(model.cons[-1], var, 1)
            model.vars[path] = var

def output_variables(model, pricer):
    """Print the values of the variables to the screen."""
    sol = model.getBestSol()
    # Flushing should probably prevent the console output from SCIP mix up with the following print
    sys.stdout.flush()

    elementary = True
    comp_value = 1e-6
    print("The solution contains the following paths: ")
    print(f"Only paths with associated value larger than {comp_value} are analysed.")
    for path, var in pricer.data['vars'].items():
        if sol[var] > comp_value:
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

def heuristic(model, heuristic_time, max_it, max_stale_it, time_limit):
    """Run the heuristic by Vidal to create valid initial solutions (section A.4)"""
    heuristic_start_time = time.time()
    data = dict()
    G = model.graph
    n = G.number_of_nodes()
    x_coords = [G.nodes[i]['coordinates'][0] for i in range(n)]
    y_coords = [G.nodes[i]['coordinates'][1] for i in range(n)]

    write_heuristic_params(G.graph['output_file'],(heuristic_time, max_it, max_stale_it))

    data['x_coordinates'] = x_coords
    data['y_coordinates'] = y_coords
    data['service_times'] = np.zeros(n)
    data['demands'] = [G.nodes[i]['demand'] for i in range(n)]
    data['vehicle_capacity'] = G.graph['capacity']
    data['num_vehicles'] = int(G.graph['min_trucks'])
    data['depot'] = 0

    paths, stale_it, i, best_cost, start = [], 0, 0, 0, time.time()

    # Repeatedly run the heuristic. The number of calls is adaptevily set and can also be changed by parameters.
    while(stale_it < max_stale_it) and i < max_it:
        found_new = False
        if i == 0:
            ap = hgs.AlgorithmParameters(timeLimit= model.graph.number_of_nodes()/10, seed=i)  # seconds
        else:
            ap = hgs.AlgorithmParameters(timeLimit= heuristic_time, seed=i)
        hgs_solver = hgs.Solver(parameters=ap, verbose=False)

        alg_start_time = time.time()
        result = hgs_solver.solve_cvrp(data)
        if (time.time() - alg_start_time) > 9*heuristic_time and i > 0:
            print(f"HYGESE: Took {round(time.time() - alg_start_time, 6)}s to solve the heuristic")
            print(f"HYGESE: Increasing heuristic time limit")
            heuristic_time *=10
            max_it /=10

        if(result.cost == 0):
            heuristic_time *=10
            max_it /=10
            print(f"HYGESE: Did not find valid solution at iteration {i}")
            continue

        if best_cost == 0 or result.cost < best_cost:
            best_cost = result.cost
        for res in result.routes:
            res.insert(0,0)
            res.append(0)
            path = tuple(res)
            if path not in paths:
                found_new = True
                paths.append(tuple(res))
        if found_new:
            stale_it = 0
        else:
            stale_it = stale_it + 1
        i = i + 1
        if time.time()- start > time_limit:
            print(f"HYGESE: Reached time limit")
            break
    print(f"HYGESE: Found {len(paths)} initial routes in {i} rounds. Best sol val is {best_cost}")
    heuristic_time_measured = round(time.time() - heuristic_start_time, 1)
    items = (len(paths), best_cost, i, heuristic_time, max_it, heuristic_time_measured)
    write_heuristic_results(model.graph.graph["output_file"], items)
    return paths

def create_example_1():
    G = nx.complete_graph(10)
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
    G.nodes()[2]['demand'] = 1

    G.graph['capacity'] = 4
    G.graph['min_trucks'] = 2
    return G
