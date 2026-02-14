"""Single source of truth for loading the C++ labelling library via CFFI."""

from collections.abc import Sequence
from dataclasses import dataclass
from cffi import FFI

LABELLING_CDEF = (
    "void initGraph(const unsigned num_nodes, const unsigned* node_data, "
    "const double* edge_data, const double capacity, "
    "const unsigned max_path_len, const unsigned* ngParams);"
    "unsigned labelling(const double * dual, const bool farkas, "
    "const unsigned time_limit, const bool elementary, "
    "const unsigned long max_vars, const bool cyc2, "
    "unsigned* result, unsigned* additional_information, "
    "const unsigned ngParam, double* farley_res, const bool ESPPRC_heur);"
)


def load_labelling_lib(so_path="Labelling/labelling_lib.so"):
    """Load the labelling C library via CFFI. Returns (ffi, lib)."""
    ffi = FFI()
    lib = ffi.dlopen(so_path)
    ffi.cdef(LABELLING_CDEF, override=True)
    return ffi, lib


def _init_graph(ffi, lib, num_nodes, demands, flat_edges, capacity, max_path_len, ng_params):
    """Allocate CFFI arrays and call lib.initGraph()."""
    nodes_arr = ffi.new("unsigned[]", demands)
    edges_arr = ffi.new("double[]", flat_edges)
    ng_params_arr = ffi.new("unsigned[]", ng_params)
    lib.initGraph(num_nodes, nodes_arr, edges_arr, capacity, max_path_len, ng_params_arr)


def _run_labelling(ffi, lib, dual, max_path_len, max_vars, *,
                   farkas=False, time_limit=60, elementary=False,
                   cyc2=False, ng_param=0, farley=False, heuristic_espprc=False):
    """Allocate CFFI arrays, call lib.labelling(), return (num_paths, result_arr, info_arr, farley_ptr)."""
    dual_arr = ffi.new("double[]", dual)
    result_arr = ffi.new("unsigned[]", max_vars * max_path_len)
    info_arr = ffi.new("unsigned[4]", [0, 0, 0, 0])
    farley_ptr = ffi.new("double*", 1.0 if farley else 0.0)

    num_paths = lib.labelling(
        dual_arr, farkas, time_limit, elementary, max_vars, cyc2,
        result_arr, info_arr, ng_param, farley_ptr, heuristic_espprc,
    )
    return num_paths, result_arr, info_arr, farley_ptr


@dataclass
class LabellingResult:
    num_paths: int
    paths: list[tuple[int, ...]]
    abort_early: bool
    truncated: bool
    time_measurements: tuple[float, float, float]
    farley_value: float


class LabellingLib:
    def __init__(self, so_path: str = "Labelling/labelling_lib.so"):
        self._ffi, self._lib = load_labelling_lib(so_path)
        self._num_nodes: int | None = None

    def init_graph(self, num_nodes: int, demands: Sequence[int],
                   flat_edges: Sequence[float], capacity: float,
                   max_path_len: int, ng_params: Sequence[int]) -> None:
        assert len(flat_edges) == num_nodes * num_nodes, (
            f"flat_edges length {len(flat_edges)} != num_nodes^2 {num_nodes * num_nodes}"
        )
        assert len(demands) == num_nodes, (
            f"demands length {len(demands)} != num_nodes {num_nodes}"
        )
        _init_graph(self._ffi, self._lib, num_nodes, demands,
                    flat_edges, capacity, max_path_len, ng_params)
        self._num_nodes = num_nodes

    def run_labelling(self, dual: Sequence[float], max_path_len: int,
                      max_vars: int, *, farkas: bool = False,
                      time_limit: int = 60, elementary: bool = False,
                      cyc2: bool = False, ng_param: int = 0,
                      farley: bool = False,
                      heuristic_espprc: bool = False) -> LabellingResult:
        assert self._num_nodes is not None, "init_graph() must be called before run_labelling()"
        assert len(dual) == self._num_nodes, (
            f"dual length {len(dual)} != num_nodes {self._num_nodes}"
        )
        assert max_vars > 0, f"max_vars must be positive, got {max_vars}"
        assert max_path_len > 0, f"max_path_len must be positive, got {max_path_len}"
        assert time_limit > 0, f"time_limit must be positive, got {time_limit}"
        num_paths, result_arr, info_arr, farley_ptr = _run_labelling(
            self._ffi, self._lib, dual, max_path_len, max_vars,
            farkas=farkas, time_limit=time_limit, elementary=elementary,
            cyc2=cyc2, ng_param=ng_param, farley=farley,
            heuristic_espprc=heuristic_espprc,
        )
        truncated = num_paths > max_vars
        paths = self._extract_paths(result_arr, num_paths, max_path_len, max_vars)
        return LabellingResult(
            num_paths=num_paths,
            paths=paths,
            abort_early=bool(info_arr[0]),
            truncated=truncated,
            time_measurements=tuple(info_arr[i] / 1e3 for i in range(1, 4)),
            farley_value=float(farley_ptr[0]),
        )

    @staticmethod
    def _extract_paths(result_arr, num_paths: int,
                       max_path_len: int, max_vars: int) -> list[tuple[int, ...]]:
        paths = []
        for i in range(min(num_paths, max_vars)):
            offset = i * max_path_len
            path = [0]
            for j in range(1, max_path_len):
                node = result_arr[offset + j]
                path.append(node)
                if node == 0:
                    break
            paths.append(tuple(path))
        return paths
