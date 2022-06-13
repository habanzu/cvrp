import networkx as nx

from model import VRP, create_constraints, output_variables, create_example_2
from pricer import VRPPricer
from parse import parse

Instance = "E/E-n23-k3"
G = parse(f"Instances/{Instance}.vrp")

model = VRP(G)

# Create pricer
pricer = VRPPricer()
pricer.init_data(G)
pricer.data['methods'] = ["ESPPRC"]
pricer.data['max_vars']= 10000
pricer.data['time_limit'] = 3600
print(f"Time limit is {pricer.data['time_limit']}")
pricer.data['farley'] = False

model.includePricer(pricer, "pricer","does pricing")

create_constraints(model,G,heuristic_stale_it=100, heuristic_max_it=2e4)

model.optimize()
model.hideOutput(quiet=False)
