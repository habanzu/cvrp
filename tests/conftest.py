import os
import sys
import math
import pytest
import networkx as nx
import numpy as np

# Ensure repo root is on sys.path so `src` is importable
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

from src.parse import parse_graph
from src.model import VRP, create_constraints
from src.pricer import VRPPricer
from src.output import write_solution
from src.labelling import LabellingLib


def solve_instance(name, k, methods, max_vars, time_limit):
    """Parse *name*, build the model, solve, and return (model, pricer).

    Parameters
    ----------
    name : str          Instance name, e.g. "E-n22-k4".
    k : int             Override for min_trucks (0 to use instance comment).
    methods : list[str] Pricing methods, e.g. ["ng8"].
    max_vars : int      Maximum variables per pricing round.
    time_limit : int    C labelling time-limit in seconds.
    """
    G = parse_graph(name, K=k, filename=f"output/test-{name}")
    model = VRP(G)

    pricer = VRPPricer(G)
    pricer.data["methods"] = methods
    pricer.data["max_vars"] = max_vars
    pricer.data["time_limit"] = time_limit
    pricer.data["farley"] = False

    model.includePricer(pricer, "pricer", "does pricing")
    create_constraints(model, pricer, heuristic_stale_it=20, heuristic_max_it=2, heuristic_time=1)

    model.hideOutput(quiet=True)
    model.optimize()

    return model, pricer


# ---------------------------------------------------------------------------
# Fixtures: parsed graphs (cheap — just parsing, no solving)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def graph_e_n22_k4():
    return parse_graph("E-n22-k4", K=0, filename="output/test-E-n22-k4-fixture")


@pytest.fixture(scope="session")
def graph_e_n23_k3():
    return parse_graph("E-n23-k3", K=0, filename="output/test-E-n23-k3-fixture")


@pytest.fixture(scope="session")
def graph_e_n30_k3():
    return parse_graph("E-n30-k3", K=0, filename="output/test-E-n30-k3-fixture")


# ---------------------------------------------------------------------------
# Fixtures: solved instances (expensive — cached per session)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def solved_e_n22_k4_ng8():
    return solve_instance("E-n22-k4", k=0, methods=["ng8"], max_vars=100, time_limit=300)


@pytest.fixture(scope="session")
def solved_e_n22_k4_spprc():
    return solve_instance("E-n22-k4", k=0, methods=["SPPRC"], max_vars=100, time_limit=300)


@pytest.fixture(scope="session")
def solved_e_n23_k3_ng8():
    return solve_instance("E-n23-k3", k=0, methods=["ng8"], max_vars=100, time_limit=300)


@pytest.fixture(scope="session")
def solved_e_n30_k3_ng8():
    return solve_instance("E-n30-k3", k=0, methods=["ng8"], max_vars=100, time_limit=300)


# ---------------------------------------------------------------------------
# CFFI helpers
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def labelling_lib():
    """Return a LabellingLib instance."""
    return LabellingLib()


@pytest.fixture(scope="session")
def init_e_n22_k4_graph(labelling_lib, graph_e_n22_k4):
    """Call initGraph for E-n22-k4, return (lib, G, max_path_len)."""
    G = graph_e_n22_k4

    demands = list(nx.get_node_attributes(G, "demand").values())
    flat_edges = nx.adjacency_matrix(G, dtype=np.double).toarray().flatten().tolist()
    num_nodes = G.number_of_nodes()
    capacity = float(G.graph["capacity"])

    minimal_demands = sum(sorted(demands[1:])[:2])
    max_path_len = math.ceil(2 * capacity / minimal_demands) + 2

    labelling_lib.init_graph(num_nodes, demands, flat_edges, capacity, max_path_len, [1, 8])

    return labelling_lib, G, max_path_len
