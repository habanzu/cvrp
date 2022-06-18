import os
from datetime import datetime
import numpy as np

def write_attributes(G, pricer):
    with open(G.graph["output_file"],"a") as f:
        for k, v in G.graph.items():
            f.write(f"{k}, {v}\n")
        now = datetime.now()
        current_time = now.strftime("%H-%M-%S")
        current_date = now.strftime("%Y-%m-%d")
        f.write(f"Start date, {current_date}\n")
        f.write(f"Start time, {current_time}\n")

        for k,v in pricer.data.items():
            f.write(f"{k}, {v}\n")

def write_message(file, message):
    with open(file, "a") as f:
        f.write(message)

def write_time(model):
    file = model.graph.graph['output_file']
    message = f"scip_total_time, {model.getTotalTime()}\n"
    write_message(file, message)

def create_file(filename, G):
    file_path = f"{filename}.log"
    identifier = 1
    while os.path.exists(file_path):
        file_path = f"{filename}_{identifier}.log"
        identifier += 1
    G.graph["output_file"] = file_path
    print(f"PARSE: Writing to file {file_path}")

def write_labelling_result(file, items):
    items = (str(item) for item in items)
    with open(file,"a") as f:
        f.write(", ".join(items) + "\n")

def write_heuristic_params(file, items):
    with open(file, "a") as f:
        f.write("initial time, initial max_it, max_stale_it\n")
        f.write(", ".join(map(str,items)) + "\n")

def write_heuristic_results(file, items):
    # print("Writing heuristic results")
    items = (str(item) for item in items)
    with open(file,"a") as f:
        f.write("heuristic Number of routes, heuristic Best Solution Value, heuristic number of iterations, adjusted time, adjusted max_it\n")
        f.write(", ".join(items) + "\n")
        f.write("method, python time, total time, propagated dominance time, unpropagated dominance time, pricing_success, upper_bound, lower_bound, abort_early, num_paths, \n")

def write_solution(model, pricer):
    sol = model.getBestSol()
    sol_val = model.getObjVal()
    file = model.graph.graph['output_file']
    write_time(model)
    if pricer.data["abort_early"]:
        return

    elementary = True
    cyc2 = True
    accuracy = 1e-4

    with open(file,"a") as f:
        num_paths = sum(1 for var in pricer.data['vars'].values() if sol[var]*var.getObj() > accuracy)
        f.write("Solval, number of paths, impact cutoff\n")
        f.write(", ".join(map(str,(sol_val, num_paths, accuracy))) + "\n")
        f.write("Elementary, 2-Cycle, Path Value, Path\n")
        for path, var in pricer.data['vars'].items():
            if sol[var]*var.getObj() > accuracy:
                path_elementary = True
                path_cyc2 = True
                counts = np.unique(path[1:-1], return_counts=True)
                for i, node in enumerate(counts[0]):
                    if counts[1][i] != 1:
                        path_elementary = False
                        elementary = False
                        break
                for i, node in enumerate(path[3:-1]):
                    if(path[i+1] == node):
                        path_cyc2 = False
                        cyc2 = False
                        break
                f.write(", ".join(map(str,(path_elementary, path_cyc2, round(sol[var],4), path))) + "\n")

        f.write(f"all_elementary, {elementary}\n")
        f.write(f"all_cyc2, {cyc2}\n")
