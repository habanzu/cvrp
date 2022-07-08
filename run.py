from src.model import VRP, create_constraints, output_variables
from src.pricer import VRPPricer
from src.parse import parse_graph
from src.output import write_solution
from multiprocessing import Pool
import os, itertools, re, psutil, time

def runInstance(Instance, methods, K=0,max_vars=0):
    try:
        G = parse_graph(Instance, K,filename=f"output_iterations/{Instance}")
        # G = parse_graph(Instance, K,filename=f"output/{Instance}-{method}")
    except ValueError:
        return

    model = VRP(G)

    # Create pricer
    pricer = VRPPricer(G)
    pricer.data['methods'] = methods
    if max_vars == 0:
        pricer.data['max_vars']= int(1e2)
    else:
        pricer.data['max_vars'] = max_vars
    pricer.data['time_limit'] = 86400
    pricer.data['farley'] = False
    pricer.data["ESPPRC_heur"] = True

    model.includePricer(pricer, "pricer","does pricing")
    create_constraints(model,pricer,heuristic_stale_it=20, heuristic_max_it=2e4, heuristic_time=1)

    model.hideOutput()
    model.optimize()

    write_solution(model, pricer)

uchoa_K_exceptions = {"X-n101-k25":26,"X-n148-k46":47,"X-n153-k22":23,"X-n172-k51":53,"X-n195-k51":53,"X-n233-k16":17,"X-n270-k35":36,"X-n289-k60":61,"X-n294-k50":51,"X-n313-k71":72,"X-n336-k84":86,"X-n384-k52":53,"X-n429-k61":62,"X-n469-k138":139}
pattern = r"X-n(\d+)-k(\d+)"

files = [file.rstrip(".vrp") for file in os.listdir("Instances/Uchoa") if (not file.endswith("sol"))]
# files = [file.rstrip(".vrp") for file in os.listdir("Instances/E") if (not file.endswith("sol"))]

uchoa_K = {file:int(re.search(pattern, file).group(2)) for file in files}
uchoa_K.update(uchoa_K_exceptions)

methods = ["ng20","ng8","cyc2","SPPRC"]
# methods = ["ng8"]

# test_combinations = [(file,method,uchoa_K[file]) for file, method in itertools.product(files,methods) if 100<= int(re.search(pattern, file).group(1)) < 200]
test_combinations = [(file,methods,uchoa_K[file]) for file in files if 100<= int(re.search(pattern, file).group(1)) < 200]
# Bis 510 ist alles oben im dict, wegen Speicherproblemen muss das heuntergesetzt werden.
# test_combinations = [(file,method) for file, method in itertools.product(files,methods)]


mem_threshold = 30
if __name__ == '__main__':
    with Pool(23,maxtasksperchild=1) as p:
        async_res = p.starmap_async(runInstance, test_combinations, 1)
        p.close()
        while(not async_res.ready()):
            time.sleep(10)
            print(f"Current memory: {psutil.virtual_memory().available >> 20} MB")
            if(psutil.virtual_memory().available >> 30 < mem_threshold):
                print(f"RUN: Memory less than {mem_threshold} GB, terminating processes.")
                p.terminate()
                break
        p.join()
