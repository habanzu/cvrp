from src.model import VRP, create_constraints, output_variables
from src.pricer import VRPPricer
from src.parse import parse

Instance = "X-n172-k51"
G = parse(Instance, 53)

model = VRP(G)

# Create pricer
pricer = VRPPricer(G)
pricer.data['methods'] = ["ESPPRC","ng8","cyc2","SPPRC"]
pricer.data['max_vars']= 1
pricer.data['time_limit'] = 10
pricer.data['farley'] = False

model.includePricer(pricer, "pricer","does pricing")
create_constraints(model,pricer,heuristic_stale_it=20, heuristic_max_it=2e5, heuristic_time=1e-5)

model.optimize()
model.hideOutput(quiet=False)
