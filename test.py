from src.model import VRP, create_constraints, output_variables
from src.pricer import VRPPricer
from src.parse import parse
from src.output import write_solution

Instance = "X-n101-k25"
G = parse(Instance, 26,filename=f"output/{Instance}-debug")

model = VRP(G)

# Create pricer
pricer = VRPPricer(G)
pricer.data['methods'] = ["SPPRC"]
pricer.data['max_vars']= 10000
pricer.data['time_limit'] = 86400
pricer.data['farley'] = False

model.includePricer(pricer, "pricer","does pricing")
create_constraints(model,pricer,heuristic_stale_it=20, heuristic_max_it=2, heuristic_time=1)

model.hideOutput(quiet=True)
model.optimize()

write_solution(model, pricer)
