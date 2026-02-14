"""Single source of truth for loading the C++ labelling library via CFFI."""

import os
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
