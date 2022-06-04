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
        if 'methods' not in self.data:
            raise ValueError("The method(s) of the pricer need to be specified.")
        self.data['bounds'] = {}
        for method in self.data['methods']:
            self.data['bounds'][method] = []

        self.data['cons'] = [self.model.getTransformedCons(con) for con in self.model.cons]
        self.data['vars'] = {path:self.model.getTransformedVar(var) for (path,var) in self.model.vars.items()}

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
        ngParam = 8
        print(f"PY PRICING: The neighborhood has been fixed to {ngParam} neighbors.")
        labelling_lib.initGraph(num_nodes,nodes_arr,edges_arr, capacity_ptr, self.data['max_path_len'], ngParam)

    def init_data(self, G):
        self.data = {}
        self.data["capacity"] = G.graph['capacity']
        self.data["num_vehicles"] = int(G.graph['min_trucks'])

    def pricerfarkas(self):
        dual = [self.model.getDualfarkasLinear(con) for con in self.data['cons']]
#         print(f"PRICER_PY: Farkas Values are {dual}")
        return self.SPPRC_chooser(dual, farkas=True)

    def pricerredcost(self):
        dual = [self.model.getDualsolLinear(con) for con in self.data['cons']]
#         print(f"PRICER_PY: Dual variables are {dual}")
        return self.SPPRC_chooser(dual, farkas=False)

    def addVar(self, path, farkas):
        if path in self.data['vars'].keys():
            cost = self.model.getVarRedcost(self.data['vars'][path])
            if farkas:
                print(f"PY Farkaspricing: Path already exists. | {path}")
            else:
                print(f"PY Pricing: Path already exists. Reduced Cost {cost:.2f} | {path}")
            raise NotImplementedError("Path already exists. This is probably due to a missing branching rule.")

        weight = nx.path_weight(self.model.graph,path,"weight")

        var = self.model.addVar(vtype="C",obj=weight,pricedVar=True)

        counts = np.unique(path[1:-1], return_counts=True)
        for i, node in enumerate(counts[0]):
            self.model.addConsCoeff(self.data['cons'][node-1], var ,counts[1][i])

        self.model.addConsCoeff(self.data['cons'][-1], var, 1)
        self.data['vars'][tuple(path)] = var
        return var

    def SPPRC_chooser(self, dual, farkas):
        max_vars = self.data['max_vars']
        abort_early = self.data['abort_early']

        for i, method in enumerate(self.data['methods']):
            if method == 'elementary':
                paths, upper_bound, lower_bound = self.labelling(dual,farkas,True,max_vars,False,abort_early,False)
            elif method == 'ng8':
                paths, upper_bound, lower_bound = self.labelling(dual,farkas,False,max_vars,False,abort_early,True,8)
            elif method == 'ng20':
                raise NotImplementedError("At the moment the ng Parameter is fixed to 8.")
                paths, upper_bound, lower_bound = self.labelling(dual,farkas,False,max_vars,False,abort_early,True,20)
            elif method == 'cyc2':
                paths, upper_bound, lower_bound = self.labelling(dual,farkas,False,max_vars,True,abort_early,False)
            elif method == 'SPPRC':
                paths, upper_bound, lower_bound = self.labelling(dual,farkas,False,max_vars,False,abort_early,False)
            else:
                raise ValueError("Method in pricerdata methods does not exist.")
            if not farkas:
                self.data['bounds'][method].append((upper_bound,lower_bound))
            if i == 0:
                lowerbound = lower_bound
                for path in paths:
                    self.addVar(path,farkas)


        if not farkas:
            return {'result':SCIP_RESULT.SUCCESS,'lowerbound':lowerbound}
        else:
            return {'result':SCIP_RESULT.SUCCESS}

    def labelling(self, dual,farkas, elementary, max_vars, cyc2, abort_early, ngParam, ngPath=0):

        # TODO: Possible improvement: result can be reused every time
        pointer_dual = ffi.cast("double*", np.array(dual,dtype=np.double).ctypes.data)

        result = np.zeros(max_vars*self.data['max_path_len'] ,dtype=np.uintc)
        result_arr = ffi.cast("unsigned*",result.ctypes.data)

        num_paths = labelling_lib.labelling(pointer_dual, farkas, elementary, max_vars, cyc2, result_arr, abort_early, ngParam)
        # print(f"PY PRICING: Found {num_paths} paths with reduced cost")

        upper_bound = self.model.getObjVal()
        if(num_paths == 0):
            # print("PY PRICING: There are no paths with negative reduced costs")
            if not farkas:
                return [], upper_bound, upper_bound
            else:
                return [], 0 , 0

        lowest_cost = 0
        paths = []
        for i in range(min(num_paths,max_vars)):
            single_result = result[i*self.data['max_path_len']:(i+1)*self.data['max_path_len']]
            result_indices = np.insert(np.nonzero(single_result),0,0)
            result_indices = np.append(result_indices,0)
            path = tuple(single_result[result_indices])
            paths.append(path)
            weight = nx.path_weight(self.model.graph,path,"weight")

            if not farkas:
                red_cost = weight - sum([dual[i-1] for i in path[1:-1]]) - dual[-1]
                if red_cost < lowest_cost:
                    lowest_cost = red_cost

        if not farkas:
            lower_bound = upper_bound + self.data['num_vehicles']*lowest_cost
            return paths, upper_bound, lower_bound
        else:
            return paths, 0 , 0
