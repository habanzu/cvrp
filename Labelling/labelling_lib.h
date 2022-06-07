#include<bitset>

using std::bitset;
using std::vector;

constexpr unsigned neighborhood_size = 512;

struct Label{
    unsigned v;
    unsigned pred;
    double cost;
    double load;
    Label* pred_ptr;
    bitset<neighborhood_size> pred_field;
    bitset<neighborhood_size> ng_memory;
    bool dominated = false;
    Label* dominator;
    vector<Label*> dominated_nodes;

    Label(unsigned v, unsigned pred, double cost, double load);
    Label(unsigned v, unsigned pred, double cost, double load, Label* pred_ptr);
    Label(unsigned v, unsigned pred, double cost, double load, Label* pred_ptr, bitset<neighborhood_size> ng_memory);
    bool dominates(Label& x, const bool cyc2, const bool elementary, const bool ngParam);
    bool check_whether_in_path(const unsigned node, const bool ngParam) const;
    unsigned path_len() const;
    void write_path_to_output(unsigned* result) const ;
    double finishing_cost(double const * dual, const bool farkas) const;
};

extern "C" {
    void initGraph(unsigned num_nodes, unsigned* node_data, double* edge_data, const double capacity, const unsigned max_path_len, const unsigned ngParam);
    unsigned labelling(const double * dual, const bool farkas, const unsigned time_limit, const bool elementary, const unsigned long max_vars, const bool cyc2, unsigned* result, bool* abort_early, const bool ngParam);
}
