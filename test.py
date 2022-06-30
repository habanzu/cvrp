from src.model import VRP, create_constraints, output_variables
from src.pricer import VRPPricer
from src.parse import parse
from src.output import write_solution

Instance = "X-n186-k15"
G = parse(Instance, 15,filename=f"output_uchoa/{Instance}-ng20")

model = VRP(G)

# Create pricer
pricer = VRPPricer(G)
pricer.data['methods'] = ["ng20"]
pricer.data['max_vars']= 10000
pricer.data['time_limit'] = 86400
pricer.data['farley'] = False

model.includePricer(pricer, "pricer","does pricing")
create_constraints(model,pricer,heuristic_stale_it=20, heuristic_max_it=2e4, heuristic_time=1)

model.hideOutput(quiet=True)
model.optimize()

write_solution(model, pricer)
