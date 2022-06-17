from src.model import VRP, create_constraints, output_variables
from src.pricer import VRPPricer
from src.parse import parse
from src.output import write_solution

Instance = "E-n33-k4"
G = parse(Instance)

model = VRP(G)

# Create pricer
pricer = VRPPricer(G)
pricer.data['methods'] = ['SPPRC']
pricer.data['max_vars']= int(1e3)
pricer.data['time_limit'] = 86400
pricer.data['farley'] = False

model.includePricer(pricer, "pricer","does pricing")
create_constraints(model,pricer,heuristic_stale_it=20, heuristic_max_it=2e6, heuristic_time=1e-5)

model.optimize()
model.hideOutput(quiet=False)

write_solution(model, pricer)
