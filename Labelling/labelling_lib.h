struct Label{
    unsigned v;
    unsigned pred;
    double cost;
    double load;
    Label* pred_ptr;

    bool dominates(const Label& x, const bool elementary);
    bool check_whether_in_path(const unsigned node) const;
    unsigned path_len();
};

extern "C" {
    void initGraph(unsigned num_nodes, unsigned* node_data, double* edge_data, const double capacity);
    unsigned labelling(double const * dual, const bool farkas, const bool elementary, const int max_vars, unsigned* result);
}
