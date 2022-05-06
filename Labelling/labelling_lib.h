struct Label{
    unsigned v;
    unsigned pred;
    double cost;
    double load;
    Label* pred_ptr;

    bool dominates(const Label& x);
};

extern "C" {
    void initGraph(unsigned num_nodes, unsigned* node_data, double* edge_data, const double capacity);
    void labelling(double const * dual,const bool farkas, unsigned* result);
}
