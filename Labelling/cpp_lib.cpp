#include <vector>
#include "cpp_lib.h"

std::vector<myProcessor> myProcessors;

myProcessor::myProcessor(int exp_in, int size_in){
    this->exp = exp_in;
    this->size = size_in;
}

int myProcessor::process(double *d, int size){
    for (int i=0; i<size; i++){
        d[i] = d[i] * d[i];
    }
    return 0;
}

unsigned int myProcessorInit(int exp_in, int size_in){
    unsigned int id;
    myProcessor tmpInst(exp_in, size_in);
    myProcessors.push_back(tmpInst);
    id = myProcessors.size() -1;
    return id;
}

int myProcessorProcess(unsigned int id, double*d, int size){
    return myProcessors[id].process(d,size);
}
