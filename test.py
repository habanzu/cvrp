from src.model import VRP, create_constraints, output_variables
from src.pricer import VRPPricer
from src.parse import parse

Instance = "X-n502-k39"
G = parse(Instance, 39)

model = VRP(G)

# Create pricer
pricer = VRPPricer(G)
pricer.data['methods'] = ["ESPPRC"]
pricer.data['max_vars']= 1000
pricer.data['time_limit'] = 86400
pricer.data['farley'] = False

model.includePricer(pricer, "pricer","does pricing")
create_constraints(model,pricer,heuristic_stale_it=20, heuristic_max_it=2e6, heuristic_time=1e-3)

model.optimize()
model.hideOutput(quiet=False)
