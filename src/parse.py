import networkx as nx
import re

from src.output import create_file

def parse(Instance, K=0, filename= None):
    print(f"MAIN: Instance {Instance}")
    if Instance[0] == "E":
        dir = "E"
    elif Instance[0] == "X":
        dir = "Uchoa"
    else:
        raise ValueError("Instance Class is not known to the parser.")
    source = f"Instances/{dir}/{Instance}.vrp"

    with open(source,'r') as f:
        lines = f.readlines()

    for i, line in enumerate(lines):
        if line.startswith('DIMENSION'):
            n = int(line.split()[-1])
        elif line.startswith("COMMENT"):
            pattern = r".*trucks: (\d+).*"
            match = re.search(pattern, line)
            if match:
                min_trucks = int(match.group(1))
                print(f"PARSE: Minimum number of trucks is {min_trucks}")
            else:
                min_trucks = K
                print("PARSE: There is no minimum number of trucks.")
                print(f"PARSE: Using the provided K = {K}")
        elif line.startswith('CAPACITY'):
            capacity = int(line.split()[-1])
        elif line.startswith('EDGE_WEIGHT_TYPE'):
            if(line.split()[-1] != "EUC_2D"):
                raise ValueError("PARSE ERROR: Wrong edge weight type.")
        elif line.startswith("NODE_COORD_SECTION"):
            node_coord_index = i
        elif line.startswith("DEMAND_SECTION"):
            demand_index = i
        elif line.startswith("DEPOT_SECTION"):
            depot_index = i

    # According to TSP Lib, node coords can be floats
    node_coords = map(lambda x:x.split(), lines[node_coord_index+1:node_coord_index+n+1])
    node_coords = [(float(x),float(y)) for _,x,y in node_coords]

    # According to TSP Lib, demands are always integers
    demands = map(lambda x:x.split(), lines[demand_index+1:demand_index+n+1])
    demands = [int(q) for _,q in demands]
    if demands[0] != 0:
        print("ERROR: Demand of depot not zero")
    for q in demands[1:]:
        if q <= 0:
            print("ERROR: All demands should be > 0")

    if int(lines[depot_index+1]) != 1 or int(lines[depot_index+2]) != -1:
        print("ERROR: Depots cant be parsed.")

    # Hilfsfunktion zum berechner der Kosten einer Kante
    def distance(node_1,node_2):
        return int(((node_1[0]-node_2[0])**2 + (node_1[1]-node_2[1])**2)**0.5 + 0.5)

    G = nx.complete_graph(n)

    for (u, v) in G.edges():
        G.edges[u,v]['weight'] = distance(node_coords[u],node_coords[v])

    for node in G.nodes():
        G.nodes()[node]['demand'] = demands[node]
        G.nodes()[node]['coordinates'] = node_coords[node]
    G.graph['Instance'] = Instance
    G.graph['capacity'] = capacity
    G.graph['min_trucks'] = min_trucks

    if filename is None:
        create_file(Instance,G)
    else:
        create_file(filename,G)

    return G
