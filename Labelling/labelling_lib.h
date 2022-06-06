#include<bitset>

constexpr unsigned neighborhood_size = 512;

struct Label{
    unsigned v;
    unsigned pred;
    double cost;
    double load;
    Label* pred_ptr;
    std::bitset<neighborhood_size> pred_field;
    std::bitset<neighborhood_size> ng_memory;

    Label(unsigned v, unsigned pred, double cost, double load);
    Label(unsigned v, unsigned pred, double cost, double load, Label* pred_ptr);
    Label(unsigned v, unsigned pred, double cost, double load, Label* pred_ptr, std::bitset<neighborhood_size> ng_memory);
    bool dominates(const Label& x, const bool elementary, const bool ngParam);
    bool check_whether_in_path(const unsigned node, const bool ngParam) const;
    unsigned path_len();
    void write_path_to_output(unsigned* result);
    double finishing_cost(double const * dual, const bool farkas);
};

unsigned index_of_max_red_cost(double const* dual, const bool farkas, const std::vector<Label*>& new_vars);

extern "C" {
    void initGraph(unsigned num_nodes, unsigned* node_data, double* edge_data, const double capacity, const unsigned max_path_len, const unsigned ngParam);
    unsigned labelling(double const * dual, const bool farkas, const unsigned time_limit, const bool elementary, const unsigned long max_vars, const bool cyc2, unsigned* result, bool* abort_early, const bool ngParam);
}
