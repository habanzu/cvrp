from src.model import VRP, create_constraints, output_variables
from src.pricer import VRPPricer
from src.parse import parse_graph
from src.output import write_solution
from multiprocessing import Pool
import os, itertools, re, psutil, time

# This memory threshold aborts the process, if less memory than this threshold is available
mem_threshold = 2
num_threads = 4

# If using this script, set the parameters in the following funciton carefully.
# See CVRP.ipynb for an explanation of these parameters.
# Be aware that any error messages of the threads will not be displayed, so make sure that test.py runs before running this file
# Also, the command line output will be a mix of all threads at once.
# To gain an idea of how this code works, use CVRPY.ipynb or at least test.py
def runInstance(Instance, method, K=0,max_vars=0):

    # try:
    G = parse_graph(Instance, K,filename=f"output/{Instance}-{method}")
    # except ValueError:
        # return
    print("Called run instance")
    model = VRP(G)

    # Create pricer
    pricer = VRPPricer(G)
    pricer.data['methods'] = [method]
    if max_vars == 0:
        pricer.data['max_vars']= int(1e2)
    else:
        pricer.data['max_vars'] = max_vars
    pricer.data['time_limit'] = 86400
    pricer.data['farley'] = False
    pricer.data["ESPPRC_heur"] = True

    model.includePricer(pricer, "pricer","does pricing")
    create_constraints(model,pricer,heuristic_stale_it=20, heuristic_max_it=2, heuristic_time=1)

    model.hideOutput()
    model.optimize()
    write_solution(model, pricer)

# This dict contains exemption for K of the convexity constraints.
# Usually the k in the instance name can be used.
# If not, it is noted in this dict.
# This exception dict is only complete for instances of up to 512 customers.

uchoa_K_exceptions = {"X-n101-k25":26,"X-n148-k46":47,"X-n153-k22":23,"X-n172-k51":53,"X-n195-k51":53,"X-n233-k16":17,"X-n270-k35":36,"X-n289-k60":61,"X-n294-k50":51,"X-n313-k71":72,"X-n336-k84":86,"X-n384-k52":53,"X-n429-k61":62,"X-n469-k138":139}
pattern = r"X-n(\d+)-k(\d+)"

files = [file.rstrip(".vrp") for file in os.listdir("Instances/Uchoa") if (not file.endswith("sol"))]
# files = [file.rstrip(".vrp") for file in os.listdir("Instances/E") if (not file.endswith("sol"))]

uchoa_K = {file:int(re.search(pattern, file).group(2)) for file in files}
uchoa_K.update(uchoa_K_exceptions)

methods = ["ng20","ng8","cyc2","SPPRC"]

test_combinations = [(file,method,uchoa_K[file]) for file, method in itertools.product(files,methods) if 100<= int(re.search(pattern, file).group(1)) < 120]
# test_combinations = [(file,methods,uchoa_K[file]) for file in files if 100<= int(re.search(pattern, file).group(1)) < 200]
# test_combinations = [(file,method) for file, method in itertools.product(files,methods)]

if __name__ == '__main__':
    with Pool(num_threads,maxtasksperchild=1) as p:
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
