import networkx as nx

from model import VRP, create_constraints, output_variables, create_example_2
from pricer import VRPPricer
from parse import parse

Instance = "Uchoa/X-n106-k14"
print(f"MAIN: Instance {Instance}")
G = parse(f"Instances/{Instance}.vrp")
G.graph['min_trucks'] = 14

model = VRP(G)

# Create pricer
pricer = VRPPricer()
pricer.init_data(G)
pricer.data['methods'] = ["SPPRC"]
print(f"MAIN: methods are {pricer.data['methods']}")
pricer.data['max_vars']= 10000
pricer.data['time_limit'] = 3600
print(f"MAIN: Time limit is {pricer.data['time_limit']}")
pricer.data['farley'] = False

model.includePricer(pricer, "pricer","does pricing")

create_constraints(model,G,heuristic_stale_it=20, heuristic_max_it=2e4, heuristic_time=1e-2)

model.optimize()
model.hideOutput(quiet=False)
