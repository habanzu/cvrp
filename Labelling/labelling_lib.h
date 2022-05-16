struct Label{
    unsigned v;
    unsigned pred;
    double cost;
    double load;
    Label* pred_ptr;

    bool dominates(const Label& x, const bool elementary);
    bool check_whether_in_path(const unsigned node) const;
    unsigned path_len();
    void write_path_to_output(unsigned* result);
    double finishing_cost(double const * dual, const bool farkas);
};

extern "C" {
    void initGraph(unsigned num_nodes, unsigned* node_data, double* edge_data, const double capacity, const unsigned max_path_len);
    unsigned labelling(double const * dual, const bool farkas, const bool elementary, const unsigned long max_vars, unsigned* result);
}
