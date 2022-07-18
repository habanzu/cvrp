from pyscipopt import Model, Pricer, SCIP_RESULT, SCIP_STAGE
import warnings, sys, math, random, cspy, time
warnings.simplefilter(action='ignore', category=FutureWarning)
import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
import src.output

# Import the C++ library into python 
from cffi import FFI
ffi = FFI()
labelling_lib = ffi.dlopen("Labelling/labelling_lib.so")
funDefs = "void initGraph(const unsigned num_nodes, const unsigned* node_data, const double* edge_data, const double capacity, const unsigned max_path_len, const unsigned* ngParams); unsigned labelling(const double * dual, const bool farkas, const unsigned time_limit, const bool elementary, const unsigned long max_vars, const bool cyc2, unsigned* result, unsigned* additional_information, const unsigned ngParam, double* farley_res, const bool ESPPRC_heur);"
ffi.cdef(funDefs, override=True)

class VRPPricer(Pricer):
    def __init__(self,G):
        super().__init__()

        self.data = {}
        self.data["capacity"] = G.graph['capacity']
        self.data["num_vehicles"] = G.graph['min_trucks']
        self.data["abort_early"] = False

    def pricerinit(self):
        if 'methods' not in self.data:
            raise ValueError("The method(s) of the pricer need to be specified.")
        print(f"SETUP: methods are {self.data['methods']}")

        if 'time_limit' not in self.data:
            raise ValueError("The time limit of the Labelling needs to be specified.")
        print(f"SETUP: time_limit is {self.data['time_limit']}")

        if 'farley' not in self.data:
            self.data['farley'] = False
        print(f"SETUP: Farley is {self.data['farley']}")


        self.data['bounds'] = {}
        self.data['farley_bound'] = []
        for method in self.data['methods']:
            self.data['bounds'][method] = []

        self.data['cons'] = [self.model.getTransformedCons(con) for con in self.model.cons]
        self.data['vars'] = {path:self.model.getTransformedVar(var) for (path,var) in self.model.vars.items()}

        demands = list(nx.get_node_attributes(self.model.graph,"demand").values())
        if not np.all(np.array(demands[1:])):
           raise ValueError("PRICER_PY ERROR: The demands of all nodes must be > 0.")
        nodes_arr = ffi.new("unsigned[]",demands)

        minimal_demands = sum(sorted(demands[1:])[:2])

        self.data['max_path_len'] = math.ceil(2*self.data['capacity'] / minimal_demands) + 2
        print(f"PRICER_PY: The maximal path length is {self.data['max_path_len']}")

        edges = nx.adjacency_matrix(self.model.graph,dtype=np.double).toarray()
        edges = list(edges.flatten())
        edges_arr = ffi.new("double[]",edges)

        num_nodes = ffi.cast("unsigned",self.model.graph.number_of_nodes())

        capacity_ptr = ffi.cast("double",self.data['capacity'])
        ngParams = [int(method.strip("ng")) for method in self.data['methods'] if method.startswith("ng")]
        ngParams.insert(0,len(ngParams))
        ngParams_ptr = ffi.new("unsigned[]",ngParams)
        print(f"PRICER_PY: The neighborhood has been initialized to {ngParams[1:]} neighbors.")
        labelling_lib.initGraph(num_nodes,nodes_arr,edges_arr, capacity_ptr, self.data['max_path_len'], ngParams_ptr)

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

        load = sum([self.model.graph.nodes()[i]['demand'] for i in path[1:-1]])
        if load > self.data['capacity']:
            print(f"PRICER_PY ERROR: Load exceeds capacity. Load {load}")
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
        if "ESPPRC_heur" in self.data:
            heuristic_espprc = self.data['ESPPRC_heur']
        else:
            heuristic_espprc = False
        pricing_success = 0

        if heuristic_espprc and not self.data['methods'] == ['SPPRC']:
            start = time.time()
            paths, upper_bound, lower_bound, abort_early, num_paths, time_measurements  = self.labelling(dual,farkas,time_limit,max_vars, heuristic_espprc=True)
            if num_paths > 0:
                abort_early = True
                method = "ESPPRC_heur"
                for path in paths:
                    self.addVar(path,farkas)
                end = time.time()
                duration = round(end - start - time_measurements[0],1)
                items = (method, duration, *time_measurements, pricing_success, round(upper_bound,4), round(lower_bound,4), abort_early, num_paths)
                src.output.write_labelling_result(self.model.graph.graph["output_file"], items)
                return {'result':SCIP_RESULT.SUCCESS}
            else:
                print("PRICER_PY: Heuristic failed. Running exact pricing.")

        for i, method in enumerate(self.data['methods']):
            start = time.time()
            if method == 'ESPPRC':
                paths, upper_bound, lower_bound, abort_early, num_paths, time_measurements  = self.labelling(dual,farkas,time_limit,max_vars,elementary=True)
            elif method.startswith("ng"):
                ngParam = int(method.strip("ng"))
                paths, upper_bound, lower_bound, abort_early, num_paths, time_measurements  = self.labelling(dual,farkas,time_limit,max_vars,ngParam=ngParam)
            elif method == 'cyc2':
                paths, upper_bound, lower_bound, abort_early, num_paths, time_measurements  = self.labelling(dual,farkas,time_limit,max_vars,cyc2=True)
            elif method == 'SPPRC':
                paths, upper_bound, lower_bound, abort_early, num_paths, time_measurements  = self.labelling(dual,farkas,time_limit,max_vars)
            else:
                raise ValueError("Method in pricerdata methods does not exist.")
            if abort_early:
                print(f"PRICER_PY: {method} exceeded time limit. Returned {len(paths)} valid paths with negative reduced cost.")
            if not farkas:
                if abort_early:
                    if len(self.data['bounds'][method]) == 0:
                        lower_bound = 0
                    else:
                        lower_bound = self.data['bounds'][method][-1][1]
                self.data['bounds'][method].append((upper_bound,lower_bound))

            if not pricing_success and ((len(paths) > 0 or not abort_early)):
                pricing_success = 1
                for path in paths:
                    self.addVar(path,farkas)
            end = time.time()
            duration = round(end - start - time_measurements[0],1)
            items = (method, duration, *time_measurements, pricing_success, round(upper_bound,4), round(lower_bound,4), abort_early, num_paths)
            src.output.write_labelling_result(self.model.graph.graph["output_file"], items)

        if self.data['farley'] and not farkas and pricing_success:
            method = self.data['methods'][0]
            if method.startswith("ng"):
                ngParam = int(method.strip("ng"))
            else:
                ngParam = 0
            _, upper_bound, lower_bound, abort_early, _, time_measurements = self.labelling(dual,farkas,time_limit,max_vars, farley = True, ngParam=ngParam)
            if abort_early:
                print(f"PRICER_PY: Farley exceeded time limit.")
                if len(self.data['farley_bound']) == 0:
                    lower_bound = 0
                else:
                    lower_bound = self.data['farley_bound'][-1]
            self.data['farley_bound'].append(lower_bound)
            end = time.time()
            duration = round(end - start - time_measurements[0],1)
            items = ("Farley", duration, *time_measurements, abort_early, round(upper_bound,4), round(lower_bound,4), abort_early, "Not Applicable")
            src.output.write_labelling_result(self.model.graph.graph["output_file"], items)

        if not pricing_success:
            print("PRICER_PY: All methods exceeded the provided time limit without finding paths with reduced cost.")
            src.output.write_message(self.model.graph.graph["output_file"], "time_limit_exceeded, terminating\n")
            self.data["abort_early"] = True
            return {'result':SCIP_RESULT.SUCCESS}

        return {'result':SCIP_RESULT.SUCCESS}

    def labelling(self, dual,farkas, time_limit, max_vars, elementary=False, cyc2=False, ngParam=0, farley=False, heuristic_espprc=False):
        if farley and farkas:
            raise ValueError("PRICER_PY ERROR: Farley can't be called with Farkas Pricing")

        # TODO: Possible improvement: result can be reused every time
        pointer_dual = ffi.new("double[]",dual)
        result_arr = ffi.new("unsigned[]",max_vars*self.data['max_path_len'])
        additional_information_ptr = ffi.new("unsigned[4]",[0 for i in range(4)])
        if farley:
            farley_ptr = ffi.new("double*",1)
        else:
            farley_ptr = ffi.new("double*",0)

        num_paths = labelling_lib.labelling(pointer_dual, farkas, time_limit, elementary, max_vars, cyc2, result_arr, additional_information_ptr, ngParam, farley_ptr, heuristic_espprc)
        abort_early = additional_information_ptr[0]
        time_measurements = tuple(round(additional_information_ptr[i]/1e3,1) for i in range(1,4))

        upper_bound = self.model.getObjVal()
        if farley:
            return [], upper_bound, upper_bound*farley_ptr[0], abort_early, num_paths, time_measurements

        result = np.frombuffer(ffi.buffer(result_arr),dtype=np.uintc)
        if(num_paths == 0):
            if not farkas:
                return [], upper_bound, upper_bound, abort_early, num_paths, time_measurements
            else:
                return [], 0 , 0, abort_early, num_paths, time_measurements

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
                red_cost = weight - sum([dual[i-1] for i in path[:-1]])
                if red_cost < lowest_cost:
                    lowest_cost = red_cost

        if not farkas:
            lower_bound = upper_bound + self.data['num_vehicles']*lowest_cost
            return paths, upper_bound, lower_bound, abort_early, num_paths, time_measurements
        else:
            return paths, 0 , 0, abort_early, num_paths, time_measurements

    def cspy(self, dual, farkas):
        G = self.data["cspy_graph"]
        for (u,v) in G.edges():
            old_v = v
            old_u = u
            if v == "Sink":
                old_v = 0
            if u == "Source":
                old_u = 0
            if farkas:
                G[u][v]['weight'] = -dual[old_v-1]
            else:
                G[u][v]['weight'] = self.model.graph[old_u][old_v]['weight'] - dual[old_v-1]

        alg = cspy.BiDirectional(G, [G.graph['capacity'] + 2,G.number_of_nodes()], [0,0], elementary=True, direction='forward')
        alg.run()
        upper_bound = self.model.getObjVal()
        path  = tuple( 0 if node == "Source" or node == "Sink" else node for node in alg.path)
        print(f"CSPY: Found elementary path {path} with cost {alg.total_cost}")
        lower_bound = 0
        if not farkas:
            lower_bound = upper_bound + self.data['num_vehicles']*alg.total_cost
        if alg.total_cost >= -1e-6:
            return [], upper_bound, lower_bound , False
        return [path], upper_bound, lower_bound, False
