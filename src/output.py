import os
from datetime import datetime

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

def create_file(filename, G):
    if not os.path.exists("output"):
        os.makedirs("output")
    file_path = f"output/{filename}.log"
    identifier = 1
    while os.path.exists(file_path):
        file_path = f"output/{filename}_{identifier}.log"
        identifier += 1
    G.graph["output_file"] = file_path

def write_labelling_result(file, items):
    items = (str(item) for item in items)
    with open(file,"a") as f:
        f.write(", ".join(items) + "\n")

def write_heuristic_results(file, items):
    print("Writing heuristic results")
    items = (str(item) for item in items)
    with open(file,"a") as f:
        f.write("Number of routes, Best Solution Value, number of iterations, time, max_it, max_stale_it\n")
        f.write(", ".join(items) + "\n")
        f.write("method, duration, pricing_success, upper_bound, lower_bound, abort_early, num_paths\n")
