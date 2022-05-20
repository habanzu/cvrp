struct Label{
    unsigned v;
    unsigned pred;
    double cost;
    double load;
    Label* pred_ptr;
    unsigned long pred_field[2] = {0};

    Label(unsigned v, unsigned pred, double cost, double load);
    Label(unsigned v, unsigned pred, double cost, double load, Label* pred_ptr);
    ~Label();
    bool dominates(const Label& x, const bool elementary);
    bool check_whether_in_path(const unsigned node) const;
    unsigned path_len();
    void write_path_to_output(unsigned* result);
    double finishing_cost(double const * dual, const bool farkas);
};

unsigned minimal_index(double const* dual, const bool farkas, const std::vector<Label*>& new_vars);

extern "C" {
    void initGraph(unsigned num_nodes, unsigned* node_data, double* edge_data, const double capacity, const unsigned max_path_len);
    unsigned labelling(double const * dual, const bool farkas, const bool elementary, const unsigned long max_vars, const bool cyc2, unsigned* result);
}
