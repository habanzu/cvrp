from src.model import VRP, create_constraints, output_variables
from src.pricer import VRPPricer
from src.parse import parse
from src.output import write_solution
from multiprocessing import Pool
import os, itertools

def runInstance(Instance, method, K=0):
    try:
        G = parse(Instance, K,filename=f"{Instance}-{method}")
    except ValueError:
        return

    model = VRP(G)

    # Create pricer
    pricer = VRPPricer(G)
    pricer.data['methods'] = [method]
    pricer.data['max_vars']= int(1e6)
    pricer.data['time_limit'] = int(2*86400)
    pricer.data['farley'] = False

    model.includePricer(pricer, "pricer","does pricing")
    create_constraints(model,pricer,heuristic_stale_it=20, heuristic_max_it=2e9, heuristic_time=1e-5)

    model.hideOutput()
    model.optimize()

    write_solution(model, pricer)

files = [file.rstrip(".vrp") for file in os.listdir("Instances/E") if (not file.endswith("sol"))]
methods = ["SPPRC","cyc2","ng8","ng20","ESPPRC"]
test_combinations = [(file,method,0) for file, method in itertools.product(files,methods)]

if __name__ == '__main__':
    with Pool() as p:
        p.starmap(runInstance, test_combinations)
