import json
import os
import pytest

EPS = 1e-6

_REGRESSION_FILE = os.path.join(os.path.dirname(__file__), "regression_values.json")
with open(_REGRESSION_FILE) as _f:
    REGRESSION = json.load(_f)
SOLVER = REGRESSION["solver"]


class TestInstanceCorrectness:

    def test_e_n22_k4_ng8(self, solved_e_n22_k4_ng8):
        model, pricer = solved_e_n22_k4_ng8
        assert model.getObjVal() == pytest.approx(SOLVER["E-n22-k4_ng8"]["obj_val"], abs=EPS)

    def test_e_n22_k4_spprc(self, solved_e_n22_k4_spprc):
        model, pricer = solved_e_n22_k4_spprc
        assert model.getObjVal() == pytest.approx(SOLVER["E-n22-k4_SPPRC"]["obj_val"], abs=EPS)

    def test_e_n23_k3_ng8(self, solved_e_n23_k3_ng8):
        model, pricer = solved_e_n23_k3_ng8
        assert model.getObjVal() == pytest.approx(SOLVER["E-n23-k3_ng8"]["obj_val"], abs=EPS)

    def test_e_n30_k3_ng8(self, solved_e_n30_k3_ng8):
        model, pricer = solved_e_n30_k3_ng8
        assert model.getObjVal() == pytest.approx(SOLVER["E-n30-k3_ng8"]["obj_val"], abs=EPS)


class TestSolverProperties:

    def _get_active_paths(self, model, pricer):
        """Return list of paths with nonzero solution value."""
        sol = model.getBestSol()
        paths = []
        for path, var in pricer.data["vars"].items():
            if sol[var] > EPS:
                paths.append(path)
        return paths

    def test_routes_cover_all_nodes(self, solved_e_n22_k4_ng8):
        model, pricer = solved_e_n22_k4_ng8
        G = model.graph
        paths = self._get_active_paths(model, pricer)

        covered = set()
        for path in paths:
            covered.update(path[1:-1])

        customer_nodes = set(range(1, G.number_of_nodes()))
        assert customer_nodes <= covered, (
            f"Missing nodes: {customer_nodes - covered}"
        )

    def test_solution_is_feasible(self, solved_e_n22_k4_ng8):
        model, pricer = solved_e_n22_k4_ng8
        G = model.graph
        capacity = G.graph["capacity"]
        paths = self._get_active_paths(model, pricer)

        for path in paths:
            load = sum(G.nodes[i]["demand"] for i in path[1:-1])
            assert load <= capacity, (
                f"Path {path} has load {load} > capacity {capacity}"
            )

    def test_paths_start_and_end_at_depot(self, solved_e_n22_k4_ng8):
        model, pricer = solved_e_n22_k4_ng8
        paths = self._get_active_paths(model, pricer)

        for path in paths:
            assert path[0] == 0, f"Path {path} does not start at depot"
            assert path[-1] == 0, f"Path {path} does not end at depot"
