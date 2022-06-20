from src.model import VRP, create_constraints, output_variables
from src.pricer import VRPPricer
from src.parse import parse
from src.output import write_solution
from multiprocessing import Pool
import os, itertools, re

def runInstance(Instance, method, K=0,max_vars=0):
    try:
        G = parse(Instance, K,filename=f"output_uchoa/{Instance}-{method}")
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
    pricer.data['time_limit'] = 86400
    pricer.data['farley'] = False

    model.includePricer(pricer, "pricer","does pricing")
    create_constraints(model,pricer,heuristic_stale_it=20, heuristic_max_it=2e9, heuristic_time=1e-5)

    model.hideOutput()
    model.optimize()

    write_solution(model, pricer)

uchoa_K = {"X-n101-k25":26,"X-n148-k46":47,"X-n153-k22":23,"X-n172-k51":53,"X-n195-k51":53,"X-n233-k16":17,"X-n270-k35":36,"X-n289-k60":61,"X-n294-k50":51,"X-n313-k71":72,"X-n336-k84":86,"X-n384-k52":53,"X-n429-k61":62,"X-n469-k138":139}
pattern = r"X-n(\d+)-k(\d+)"

files = [file.rstrip(".vrp") for file in os.listdir("Instances/Uchoa") if (not file.endswith("sol"))]

methods = ["SPPRC","cyc2","ng8","ng20"]
test_combinations = [(file,method,uchoa_K.setdefault(file,0)) for file, method in itertools.product(files,methods) if int(re.search(pattern, file).group(1)) < 510]
print(test_combinations)

if __name__ == '__main__':
    with Pool(24) as p:
        p.starmap(runInstance, test_combinations)
