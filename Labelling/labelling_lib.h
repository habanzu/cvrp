#include<bitset>

using std::bitset;
using std::vector;

constexpr unsigned neighborhood_size = 512;

struct Label{
    unsigned v;
    unsigned pred;
    double cost;
    unsigned load;
    double farley_val;
    Label* pred_ptr;
    bitset<neighborhood_size> pred_field;
    bitset<neighborhood_size> ng_memory;
    bool dominated = false;
    Label* dominator;
    vector<Label*> dominated_nodes;

    Label();
    Label(unsigned v, unsigned pred, double cost, unsigned load);
    Label(unsigned v, unsigned pred, double cost, unsigned load, Label* pred_ptr);
    Label(unsigned v, unsigned pred, double cost, unsigned load, Label* pred_ptr, double farley_val);
    Label(unsigned v, unsigned pred, double cost, unsigned load, Label* pred_ptr, bitset<neighborhood_size>& ng_memory);
    Label(unsigned v, unsigned pred, double cost, unsigned load, Label* pred_ptr, bitset<neighborhood_size>& ng_memory, double farley_val);
    bool dominates(const Label& x, const bool elementary, const bool ngParam, const bool farley) const;
    bool check_whether_in_path(const unsigned node, const bool ngParam) const;
    unsigned path_len() const;
    void write_path_to_output(unsigned* result) const ;
    double finishing_cost(double const * dual, const bool farkas) const;
};

extern "C" {
    void initGraph(const unsigned num_nodes, const unsigned* node_data, const double* edge_data, const double capacity, const unsigned max_path_len, const unsigned* ngParams);
    unsigned labelling(const double * dual, const bool farkas, const unsigned time_limit, const bool elementary, const unsigned long max_vars, const bool cyc2, unsigned* result, bool* abort_early, const unsigned ngParam, double* farley_res);
}
