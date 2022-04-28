class myProcessor {
protected:
    int exp;
    int size;

public:
    myProcessor(int exp_in, int size_in);
    int process(double *d, int size);
};

extern "C" {
    unsigned int myProcessorInit(int exp_in, int size_in);
    int myProcessorProcess(unsigned int id, double *d, int size);
} //end extern "C"
