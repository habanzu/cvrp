import networkx as nx

from model import VRP, create_constraints, output_variables, create_example_2
from pricer import VRPPricer
from parse import parse


G = parse("Instances/E/E-n23-k3.vrp")

model = VRP(G)

# Create pricer
pricer = VRPPricer()
pricer.init_data(G)
pricer.data['methods'] = ["SPPRC"]
pricer.data['max_vars']= 10000
pricer.data['time_limit'] = 60
pricer.data['farley'] = False

model.includePricer(pricer, "pricer","does pricing")

create_constraints(model,G,heuristic_time=0)

model.optimize()
model.hideOutput(quiet=False)
