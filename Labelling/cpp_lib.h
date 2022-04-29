class myProcessor {
protected:
    int size;
    double* data;

public:
    myProcessor(int size, double* data);
    int process(double *d, int size);
};

extern "C" {
    void initGraph(unsigned num_nodes, unsigned* node_data, double* edge_data);
    unsigned int myProcessorInit(int size, double* data);
    int myProcessorProcess(unsigned int id, double *d, int size);
    void labelling(double* dual, bool farkas);
} //end extern "C"
