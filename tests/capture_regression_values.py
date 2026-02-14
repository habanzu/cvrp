"""
Capture regression test values and save as JSON.

Run from repo root:
    python tests/capture_regression_values.py

Writes tests/regression_values.json, which test_cffi.py and test_solver.py load.
"""

import json
import math
import os
import sys

sys.path.insert(0, ".")
from src.labelling import LabellingLib
from tests.conftest import solve_instance

lib = LabellingLib()

# Synthetic graph: 6 nodes (depot=0, customers=1..5)

NUM_NODES = 6
DEMANDS = [0, 1, 2, 1, 2, 1]
CAPACITY = 4.0

EDGES = [
    [0, 10, 15, 20, 25, 30],
    [10, 0, 12, 8, 22, 18],
    [15, 12, 0, 10, 14, 20],
    [20, 8, 10, 0, 16, 25],
    [25, 22, 14, 16, 0, 10],
    [30, 18, 20, 25, 10, 0],
]

FLAT_EDGES = [float(EDGES[i][j]) for i in range(NUM_NODES) for j in range(NUM_NODES)]
MAX_PATH_LEN = math.ceil(2 * CAPACITY / min(DEMANDS[1:])) + 2
DUALS = [25.0, 25.0, 25.0, 25.0, 25.0, 0.0]
MAX_VARS = 20


def init_graph():
    lib.init_graph(NUM_NODES, DEMANDS, FLAT_EDGES, CAPACITY, MAX_PATH_LEN, [0])


def do_labelling(elementary=False):
    result = lib.run_labelling(DUALS, MAX_PATH_LEN, MAX_VARS, elementary=elementary)
    return result.num_paths, result.paths


def reduced_cost(path):
    edge_cost = sum(EDGES[path[k]][path[k + 1]] for k in range(len(path) - 1))
    dual_sum = sum(DUALS[node - 1] for node in path[1:-1])
    return edge_cost - dual_sum - DUALS[-1]


def compute_load(path):
    return sum(DEMANDS[node] for node in path[1:-1])


def capture_mode(elementary):
    init_graph()
    num_paths, paths = do_labelling(elementary=elementary)

    # Structural invariants — fail loudly if broken
    assert all(p[0] == 0 and p[-1] == 0 for p in paths), "Not all paths start/end at depot"
    assert all(compute_load(p) <= CAPACITY for p in paths), "Load exceeds capacity"
    assert all(reduced_cost(p) < -1e-6 for p in paths), "Non-negative reduced cost found"
    assert num_paths < MAX_VARS, f"num_paths ({num_paths}) >= MAX_VARS, may be truncated"
    if elementary:
        for p in paths:
            customers = p[1:-1]
            assert len(customers) == len(set(customers)), f"Duplicate in elementary path {p}"

    sorted_rcs = sorted(reduced_cost(p) for p in paths)
    return {
        "num_paths": num_paths,
        "best_reduced_cost": min(sorted_rcs),
        "sorted_reduced_costs": sorted_rcs,
    }


SOLVER_INSTANCES = [
    {"name": "E-n22-k4", "k": 0, "methods": ["ng8"], "max_vars": 100, "time_limit": 300},
    {"name": "E-n22-k4", "k": 0, "methods": ["SPPRC"], "max_vars": 100, "time_limit": 300},
    {"name": "E-n23-k3", "k": 0, "methods": ["ng8"], "max_vars": 100, "time_limit": 300},
    {"name": "E-n30-k3", "k": 0, "methods": ["ng8"], "max_vars": 100, "time_limit": 300},
]


def capture_solver():
    results = {}
    for inst in SOLVER_INSTANCES:
        key = f"{inst['name']}_{inst['methods'][0]}"
        model, _ = solve_instance(**inst)
        results[key] = {"obj_val": model.getObjVal()}
    return results


if __name__ == "__main__":
    result = {
        "graph": {
            "num_nodes": NUM_NODES,
            "demands": DEMANDS,
            "capacity": CAPACITY,
            "edges": EDGES,
            "duals": DUALS,
        },
        "spprc": capture_mode(elementary=False),
        "elementary": capture_mode(elementary=True),
        "solver": capture_solver(),
    }

    out_path = os.path.join(os.path.dirname(__file__), "regression_values.json")
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)
        f.write("\n")
