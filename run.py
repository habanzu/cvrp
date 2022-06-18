from src.model import VRP, create_constraints, output_variables
from src.pricer import VRPPricer
from src.parse import parse
from src.output import write_solution
from multiprocessing import Pool
import os, itertools

def runInstance(Instance, method, K=0,max_vars=0):
    try:
        G = parse(Instance, K,filename=f"test_added_vars/{Instance}-{method}-v_{max_vars}")
    except ValueError:
        return

    model = VRP(G)

    # Create pricer
    pricer = VRPPricer(G)
    pricer.data['methods'] = [method]
    if max_vars == 0:
        pricer.data['max_vars']= int(1e6)
    else:
        pricer.data['max_vars'] = max_vars
    pricer.data['time_limit'] = 1#7200#86400
    pricer.data['farley'] = False

    model.includePricer(pricer, "pricer","does pricing")
    create_constraints(model,pricer,heuristic_stale_it=20, heuristic_max_it=2e8, heuristic_time=1e-5)

    model.hideOutput()
    model.optimize()

    write_solution(model, pricer)

files = [file.rstrip(".vrp") for file in os.listdir("Instances/E") if (not file.endswith("sol"))]
methods = ["ng20","ESPPRC"]
max_vars = [int(10**i) for i in range(7)]
test_combinations = [(file,method,0,max_var) for file, method, max_var in itertools.product(files,methods,max_vars)]

if __name__ == '__main__':
    with Pool() as p:
        p.starmap(runInstance, test_combinations)
