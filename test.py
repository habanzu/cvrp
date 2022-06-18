from src.model import VRP, create_constraints, output_variables
from src.pricer import VRPPricer
from src.parse import parse
from src.output import write_solution

Instance = "E-n23-k3"
G = parse(Instance)

model = VRP(G)

# Create pricer
pricer = VRPPricer(G)
pricer.data['methods'] = ["ng20"]
pricer.data['max_vars']= int(1e6)
pricer.data['time_limit'] = 10
pricer.data['farley'] = False

model.includePricer(pricer, "pricer","does pricing")
create_constraints(model,pricer,heuristic_stale_it=20, heuristic_max_it=2e6, heuristic_time=1e-5)

model.hideOutput(quiet=True)
model.optimize()

write_solution(model, pricer)
