#include <vector>
#include <iostream>
#include "cpp_lib.h"

using std::vector;

vector<myProcessor> myProcessors;
vector<int> nodes;
vector<vector<double> > edges;
unsigned num_nodes;

myProcessor::myProcessor(int size, double* data){
    this->size = size;
    this->data = data;
}

int myProcessor::process(double *d, int size){
    for (int i=0; i<size; i++){
        d[i] = d[i] * d[i];
    }
    return 0;
}

unsigned int myProcessorInit(int size, double* data){
    unsigned int id;
    myProcessor tmpInst(size, data);
    myProcessors.push_back(tmpInst);
    id = myProcessors.size() -1;
    return id;
}

int myProcessorProcess(unsigned int id, double*d, int size){
    return myProcessors[id].process(d,size);
}

void initGraph(unsigned num_nodes, unsigned* node_data, double* edge_data){
    ::num_nodes = num_nodes;
    for(unsigned i=0;i<num_nodes;i++){
        nodes.push_back(node_data[i]);
        vector<double> v;
        for(unsigned j=0;j<num_nodes;j++){
            v.push_back(edge_data[i*num_nodes + j]);
        }
        edges.push_back(v);
    }
    // Wo gehen prints hin mit cffi?
    std::cout << "Graph data successfully copied to C." << std::endl;
}

void labelling(double* dual, bool farkas){
    for(unsigned i = 0; i<num_nodes;++i){
        dual[i] = 17.0;
    }
}
