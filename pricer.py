from pyscipopt import Model, Pricer, SCIP_RESULT, SCIP_STAGE
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
import sys, math, random

from cffi import FFI
ffi = FFI()
labelling_lib = ffi.dlopen("Labelling/labelling_lib.so")

funDefs = "void initGraph(unsigned num_nodes, unsigned* node_data, double* edge_data, const double capacity, const unsigned max_path_len, const unsigned ngParam); unsigned labelling(double const * dual, const bool farkas, const bool elementary, const unsigned long max_vars, const bool cyc2, unsigned* result, const bool abort_early, const bool ngPath);"
ffi.cdef(funDefs, override=True)

class VRPPricer(Pricer):
    def pricerinit(self):
        self.data['cons'] = [self.model.getTransformedCons(con) for con in self.model.cons]
        self.data['vars'] = {path:self.model.getTransformedVar(var) for (path,var) in self.model.vars.items()}
        if 'ngParam' not in self.data:
            self.data['ngParam'] = 1

        demands = list(nx.get_node_attributes(self.model.graph,"demand").values())
        if not np.all(np.array(demands[1:])):
           print("PRICER_PY: The demands of all nodes must be > 0.")
        nodes_arr = ffi.cast("unsigned*", np.array(demands).astype(np.uintc).ctypes.data)

        minimal_demands = sum(sorted(demands[1:])[:2])

        self.data['max_path_len'] = math.ceil(2*self.data['capacity'] / minimal_demands) + 2
        print(f"PRICER_PY: The maximal path length is {self.data['max_path_len']}")

        edges = nx.adjacency_matrix(self.model.graph,dtype=np.double).toarray()
        edges_arr = ffi.cast("double*", edges.ctypes.data)

        num_nodes = ffi.cast("unsigned",self.model.graph.number_of_nodes())

        capacity_ptr = ffi.cast("double",self.data['capacity'])
        labelling_lib.initGraph(num_nodes,nodes_arr,edges_arr, capacity_ptr, self.data['max_path_len'], self.data['ngParam'])

    def init_data(self, G):
        self.data = {}
        self.data["capacity"] = G.graph['capacity']
        self.data["num_vehicles"] = int(G.graph['min_trucks'])
        self.data['bounds'] = []

    def pricerfarkas(self):
        dual = [self.model.getDualfarkasLinear(con) for con in self.data['cons']]
#         print(f"PRICER_PY: Farkas Values are {dual}")
        return self.labelling(dual, farkas=True)

    def pricerredcost(self):
        dual = [self.model.getDualsolLinear(con) for con in self.data['cons']]
#         print(f"PRICER_PY: Dual variables are {dual}")
        return self.labelling(dual)

    def labelling(self, dual,farkas=False, elementary=False, max_vars=10000, cyc2=False, abort_early=False, ngParam = 1, ngPath = False):
        if 'elementary' in self.data:
            elementary = self.data['elementary']
        if 'max_vars' in self.data:
            max_vars = self.data['max_vars']
        if 'cyc2' in self.data:
            cyc2 = self.data['cyc2']
        if 'abort_early' in self.data:
            abort_early = self.data['abort_early']
        if 'ngPath' in self.data:
            ngPath = self.data['ngPath']

        # TODO: Possible improvement: result can be reused every time
        pointer_dual = ffi.cast("double*", np.array(dual,dtype=np.double).ctypes.data)

        result = np.zeros(max_vars*self.data['max_path_len'] ,dtype=np.uintc)
        result_arr = ffi.cast("unsigned*",result.ctypes.data)

        num_paths = labelling_lib.labelling(pointer_dual, farkas, elementary, max_vars, cyc2, result_arr, abort_early, ngPath)
        print(f"PY PRICING: Found {num_paths} paths with reduced cost")

        if(num_paths == 0):
            print("PY PRICING: There are no paths with negative reduced costs")
            return {'result':SCIP_RESULT.SUCCESS}

        lowest_cost = 0
        for i in range(min(num_paths,max_vars)):
            single_result = result[i*self.data['max_path_len']:(i+1)*self.data['max_path_len']]
            result_indices = np.insert(np.nonzero(single_result),0,0)
            result_indices = np.append(result_indices,0)
            path = tuple(single_result[result_indices])

            if path in self.data['vars'].keys():
                cost = self.model.getVarRedcost(self.data['vars'][path])
                if farkas:
                    print(f"PY Farkaspricing: Path already exists. | {path}")
                else:
                    print(f"PY Pricing: Path already exists. Reduced Cost {cost:.2f} | {path}")
                return {'result':SCIP_RESULT.SUCCESS}

            weight = nx.path_weight(self.model.graph,path,"weight")

            var = self.model.addVar(vtype="C",obj=weight,pricedVar=True)
            if not farkas:
                red_cost = weight - sum([dual[i-1] for i in path[1:-1]]) - dual[-1]
                if red_cost < lowest_cost:
                    lowest_cost = red_cost

            counts = np.unique(path[1:-1], return_counts=True)
            for i, node in enumerate(counts[0]):
                self.model.addConsCoeff(self.data['cons'][node-1], var ,counts[1][i])

            self.model.addConsCoeff(self.data['cons'][-1], var, 1)
            self.data['vars'][tuple(path)] = var

        if not farkas:
            upper_bound = self.model.getObjVal()
            lower_bound = upper_bound + self.data['num_vehicles']*lowest_cost
            self.data['bounds'].append((upper_bound,lower_bound))
            return {'result':SCIP_RESULT.SUCCESS,'lowerbound':lower_bound}
        return {'result':SCIP_RESULT.SUCCESS}
