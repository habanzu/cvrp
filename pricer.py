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

funDefs = "void initGraph(unsigned num_nodes, unsigned* node_data, double* edge_data, const double capacity, const unsigned max_path_len, const unsigned ngParam); unsigned labelling(double const * dual, const bool farkas, const unsigned time_limit, const bool elementary, const unsigned long max_vars, const bool cyc2, unsigned* result, bool* abort_early, const bool ngPath);"
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
        self.data["num_vehicles"] = G.graph['min_trucks']

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
        time_limit = self.data['time_limit']
        pricing_success = 0

        for i, method in enumerate(self.data['methods']):
            if method == 'elementary':
                paths, upper_bound, lower_bound, abort_early = self.labelling(dual,farkas,time_limit, True,max_vars,False,False)
            elif method == 'ng8':
                paths, upper_bound, lower_bound, abort_early  = self.labelling(dual,farkas, time_limit, False,max_vars,False,True,8)
            elif method == 'ng20':
                raise NotImplementedError("At the moment the ng Parameter is fixed to 8.")
                paths, upper_bound, lower_bound, abort_early  = self.labelling(dual,farkas, time_limit, False,max_vars,False,True,20)
            elif method == 'cyc2':
                paths, upper_bound, lower_bound, abort_early  = self.labelling(dual,farkas, time_limit, False,max_vars,True,False)
            elif method == 'SPPRC':
                paths, upper_bound, lower_bound, abort_early  = self.labelling(dual,farkas,time_limit, False,max_vars,False,False)
            else:
                raise ValueError("Method in pricerdata methods does not exist.")
            if not farkas:
                if abort_early:
                    if len(self.data['bounds'][method]) == 0:
                        lower_bound = 0
                    else:
                        lower_bound = self.data['bounds'][method][-1][1]
                self.data['bounds'][method].append((upper_bound,lower_bound))
            if not pricing_success and (len(paths) > 0 or not abort_early):
                pricing_success = 1
                for path in paths:
                    self.addVar(path,farkas)
        if not pricing_success:
            print("PRICER_PY: All methods exceeded the provided time limit without finding paths with reduced cost.")
            return {'result':SCIP_RESULT.DIDNOTRUN}

        return {'result':SCIP_RESULT.SUCCESS}
        # return {'result':SCIP_RESULT.SUCCESS}'lowerbound':lowerbound}

    def labelling(self, dual,farkas, time_limit, elementary, max_vars, cyc2, ngParam, ngPath=0):

        # TODO: Possible improvement: result can be reused every time
        pointer_dual = ffi.cast("double*", np.array(dual,dtype=np.double).ctypes.data)

        TODO: Wieder effizienter machen. Hab ich probiert um Fehler in der n256 Instanz zu finden.
        result_arr = ffi.new("unsigned[]",max_vars*self.data['max_path_len'])
        result = np.zeros(max_vars*self.data['max_path_len'] ,dtype=np.uintc)
        # result_arr = ffi.cast("unsigned*",result.ctypes.data)

        abort_early_ptr = ffi.new("bool*",False)

        num_paths = labelling_lib.labelling(pointer_dual, farkas, time_limit, elementary, max_vars, cyc2, result_arr, abort_early_ptr, ngParam)
        # print(f"PY PRICING: Found {num_paths} paths with reduced cost")
        abort_early = abort_early_ptr[0]

        for i in range(max_vars*self.data['max_path_len']):
            result[i] = result_arr[i]

        upper_bound = self.model.getObjVal()
        if(num_paths == 0):
            if not farkas:
                return [], upper_bound, upper_bound, abort_early
            else:
                return [], 0 , 0, abort_early

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
            return paths, upper_bound, lower_bound, abort_early
        else:
            return paths, 0 , 0, abort_early
