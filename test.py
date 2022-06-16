from src.model import VRP, create_constraints, output_variables
from src.pricer import VRPPricer
from src.parse import parse
from src.output import write_solution

Instance = "X-n120-k6"
G = parse(Instance, 6)

model = VRP(G)

# Create pricer
pricer = VRPPricer(G)
pricer.data['methods'] = ['ng8']
pricer.data['max_vars']= 1000
pricer.data['time_limit'] = 3600
pricer.data['farley'] = False

model.includePricer(pricer, "pricer","does pricing")
create_constraints(model,pricer,heuristic_stale_it=20, heuristic_max_it=2e3, heuristic_time=1e-3)

model.optimize()
model.hideOutput(quiet=False)

write_solution(model, pricer)
