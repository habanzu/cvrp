import networkx as nx

from model import VRP, create_constraints, output_variables, create_example_2
from pricer import VRPPricer
from parse import parse
from output import create_file

Instance = "E/E-n23-k3"
output_name = Instance.split("/")[-1]
print(f"MAIN: Instance {Instance}")
G = parse(f"Instances/{Instance}.vrp")
G.graph['min_trucks'] = 14
G.graph["Instance"] = Instance

model = VRP(G)

# Create pricer
pricer = VRPPricer()
pricer.init_data(G)
pricer.data['methods'] = ["ESPPRC","ng8","cyc2","SPPRC"]
print(f"MAIN: methods are {pricer.data['methods']}")
pricer.data['max_vars']= 1
pricer.data['time_limit'] = 10
print(f"MAIN: Time limit is {pricer.data['time_limit']}")
pricer.data['farley'] = True

create_file(output_name,G, pricer)

model.includePricer(pricer, "pricer","does pricing")
create_constraints(model,G,heuristic_stale_it=20, heuristic_max_it=2e1, heuristic_time=1e-2)

model.optimize()
model.hideOutput(quiet=False)
