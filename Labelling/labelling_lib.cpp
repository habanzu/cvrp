#include <vector>
#include <list>
#include <iostream>
#include <cmath>
#include <algorithm>
#include <set>
#include <bitset>
#include <chrono>

#include "labelling_lib.h"

using std::vector;
using std::list;
using std::cout;
using std::endl;
using std::multiset;
using namespace std::chrono;

vector<double> nodes;
vector<vector<double> > edges;
vector<bitset<neighborhood_size> > neighborhoods;
unsigned num_nodes;
double capacity;
unsigned max_path_len;

struct less_than {
    bool operator()(const Label& label1, const Label& label2) const{
        return (label1.load < label2.load);
    }
};

Label::Label(unsigned v, unsigned pred, double cost, double load):v{v}, pred{pred}, cost{cost}, load{load} {
    pred_field[0] = 1;
    ng_memory = bitset<neighborhood_size>();
}

Label::Label(unsigned v, unsigned pred, double cost, double load, const Label* pred_ptr):v{v}, pred{pred}, cost{cost}, load{load}, pred_ptr{pred_ptr} {
    pred_field = pred_ptr->pred_field;
    pred_field[v] = 1;
}

Label::Label(unsigned v, unsigned pred, double cost, double load, const Label* pred_ptr, bitset<neighborhood_size> ng_memory):v{v}, pred{pred}, cost{cost}, load{load}, pred_ptr{pred_ptr}, ng_memory{ng_memory}{
    pred_field = pred_ptr->pred_field;
    pred_field[v] = 1;
}

bool Label::dominates(const Label& x, const bool elementary, const bool ngParam) const{
    if((this->cost <= x.cost) && (this->load <= x.load)){
        if(!elementary && !ngParam)
            return true;
        if(x.v == 0  || this->v == 0)
            cout << "PRICER_C ERROR: Dominance check on start label." << endl;

        auto& own_comparator = ngParam ? this->ng_memory : this->pred_field;
        auto& x_comparator = ngParam ? x.ng_memory : x.pred_field;

        if((own_comparator & x_comparator) == own_comparator){
            return true;
        } else {
            return false;
        }
    }
    return false;
}

bool Label::check_whether_in_path(const unsigned node, const bool ngParam) const{
    if(node == 0)
        cout << "PRICER_C ERROR: Path check with node 0." << endl;

    bitset<neighborhood_size> mask(0);
    mask[node] = 1;

    auto& comparator = ngParam ? this->ng_memory : this->pred_field;
    if((comparator & mask) == mask){
        return true;
    } else {
        return false;
    }
}

unsigned Label::path_len() const{
    unsigned path_len = 2;
    const Label* current_label = this;
    while(current_label->pred > 0){
        // Calculation of path len in pricer.py
        if(path_len > max_path_len || path_len > capacity + 2){
            cout << "PRICER_C ERROR: Path length exceeds maximum. Current value of path_len is " << path_len << endl;
            return 0;
        }
        ++path_len;
        current_label = current_label->pred_ptr;
    }
    return path_len;
}

void Label::write_path_to_output(unsigned* result) const{
    unsigned path_len = this->path_len();
    if(path_len > max_path_len){
        cout << "PRICER_C WARNING: Path exceeds maximum path length" << endl;
        return;
    }

    const Label* current_label = this;
    result[path_len] = 0;
    result[0] = 0;
    for(unsigned i = path_len - 1; i > 0; --i){
        result[i] = current_label->v;
        if(current_label->v == 0){
            cout << "PRICER_C WARNING: Start label in path when writing result" << endl;
            return;
        }
        current_label = current_label->pred_ptr;
    }
}

double Label::finishing_cost(double const * dual, const bool farkas) const{
    double finishing_cost = this->cost - dual[num_nodes-1];
    finishing_cost = farkas ? finishing_cost: finishing_cost + edges[this->v][0];
    return finishing_cost;
}

unsigned index_of_max_red_cost(double const* dual, const bool farkas, const vector<Label*>& new_vars ){
    double highest_red_cost = new_vars[0]->finishing_cost(dual,farkas);
    unsigned index = 0;
    for(unsigned i = 1; i < new_vars.size();++i){
        if(new_vars[i]->finishing_cost(dual,farkas) > highest_red_cost){
            index = i;
            highest_red_cost = new_vars[i]->finishing_cost(dual,farkas);
        }
    }
    return index;
}

double maximal_cost(double const* dual, const bool farkas, const vector<Label*>& new_vars ){
    double highest_red_cost = new_vars[0]->finishing_cost(dual,farkas);
    for(unsigned i = 1; i < new_vars.size();++i){
        if(new_vars[i]->finishing_cost(dual,farkas) > highest_red_cost){
            highest_red_cost = new_vars[i]->finishing_cost(dual,farkas);
        }
    }
    return highest_red_cost;
}

unsigned index_minimum_load_in_queue(const vector<multiset<Label, less_than>>& q){
    unsigned min_index;
    double min_load = capacity + 1;
    for(unsigned i = 0; i < num_nodes; ++i){
        if(!q[i].empty() && q[i].begin()->load < min_load){
            min_index = i;
            min_load = q[i].begin()->load;
        }
    }

    return min_index;
}

bool queue_empty(const vector<multiset<Label, less_than>>& q){
    for(unsigned i = 0; i < num_nodes; ++i){
        if(!q[i].empty())
            return false;
    }
    return true;
}

void initGraph(unsigned num_nodes, unsigned* node_data, double* edge_data, const double capacity, const unsigned max_path_len, const unsigned ngParam){
    if(num_nodes > neighborhood_size){
        cout << "PRICER_C Error: The number of nodes is to large for the Label struct. Abort." << endl;
        return;
    }
    ::num_nodes = num_nodes;
    ::capacity = capacity;
    ::max_path_len = max_path_len;
    nodes.clear();
    edges.clear();
    neighborhoods.clear();

    for(unsigned i=0;i<num_nodes;++i){
        nodes.push_back(node_data[i]);
        vector<double> v;
        for(unsigned j=0;j<num_nodes;++j){
            v.push_back(edge_data[i*num_nodes + j]);
        }
        edges.push_back(v);
    }
    neighborhoods.push_back(0);
    for(unsigned i =1; i<num_nodes;++i){
        double edge_bound = i == 1 ? edges[1][2] : edges[i][1];
        bitset<neighborhood_size> neighborhood;
        neighborhood[i] = 1;
        for(unsigned j=1; j<= ngParam; ++j){
            neighborhood[j] = 1;
            edge_bound = (edges[i][j] > edge_bound) ? edges[i][j] : edge_bound;
        }
        if(i <= ngParam && ngParam + 1 < num_nodes){
            neighborhood[ngParam + 1] = 1;
            edge_bound = (edges[i][ngParam + 1] > edge_bound) ? edges[i][ngParam + 1] : edge_bound;
        }
        unsigned start_index = i <= ngParam ? ngParam + 2 : ngParam + 1;

        for(unsigned j = start_index; j < num_nodes; ++j){
            if(j==i) continue;
            if(edges[i][j] < edge_bound){
                neighborhood[j] = 1;
                for(unsigned l = 1;l < num_nodes;++l){
                    if(l==i) continue;
                    if(edges[i][l] == edge_bound){
                        neighborhood[l] = 0;
                        break;
                    }
                }
                edge_bound = 0;
                for(unsigned l = 1; l < num_nodes;++l){
                    if (edges[i][l] > edge_bound && neighborhood[l] == 1 && i != l)
                        edge_bound = edges[i][l];
                }
            }
        }
        neighborhoods.push_back(neighborhood);

    }
    cout << "PRICER_C: Graph data successfully copied to C." << endl;
}

unsigned labelling(const double * dual, const bool farkas, const unsigned time_limit, const bool elementary, const unsigned long max_vars, const bool cyc2, unsigned* result, bool* abort_early, const bool ngParam){
    auto t0 = high_resolution_clock::now();

    vector<multiset<Label, less_than>> q;
    // TODO: Wieso wirft vector<vector< const Label>> einen Fehler?
    vector<list<Label> > propagated;
    vector<Label*> new_vars;
    propagated.resize(num_nodes);
    q.resize(num_nodes);
    q[0].insert(Label {0,0,0,0});

    double red_cost_bound = -1e-6;
    unsigned num_paths = 0;

    while(!queue_empty(q)){
        unsigned queue_index = index_minimum_load_in_queue(q);
        auto it_q = q[queue_index].begin();
        propagated[it_q->v].push_back(*it_q);
        // TODO: Ist das die korrekte Syntax für eine REferenz?
        Label& x = propagated[it_q->v].back();
        q[queue_index].erase(it_q);

        for(unsigned i=1;i<num_nodes;++i){
            if (i == x.v)
                continue;
            if((elementary || ngParam) && x.check_whether_in_path(i, ngParam))
                continue;
            if(cyc2 && x.pred == i)
                continue;

            // Create new label
            const double newload = x.load + nodes[i];
            if(newload > capacity)
                continue;
            bool dominated = false;
            bool first_dominated = false;
            const double newcost = farkas ? x.cost - dual[i-1]: x.cost - dual[i-1] + edges[x.v][i];
            bitset<neighborhood_size> neighborhood;
            if(ngParam){
                neighborhood = neighborhoods[i] & x.ng_memory;
                neighborhood[i] = 1;
            }
            Label newlabel {i, x.v, newcost, newload, &x, neighborhood};

            for(const Label& label: propagated[i]){
                // TODO: Rewrite dominates()
                if(label.dominates(newlabel, elementary, ngParam)){
                    if(cyc2 && !first_dominated && (label.pred != newlabel.pred)){
                        // TODO: Geht hier alles gut mit dem neuen propagated labels Teil?
                        first_dominated = true;
                    } else {
                    dominated = true;
                    break;
                    }
                }
            }
            if(!dominated){

                for(auto it = q[i].begin(); it != q[i].end(); ){
                    // TODO: Ich sollte getrennte queues für jeden Knoten haben.
                    if(it->load <= newlabel.load && it->dominates(newlabel, elementary, ngParam)){
                        if(cyc2 && !first_dominated && (it->pred != newlabel.pred)){
                            // TODO: Geht hier alles gut mit dem neuen propagated labels Teil?
                            // TODO: Nein. Wenn das neues Label eines in der queue dominiert wird nicht auf zweifache Dominanz geschaut. Dass muss gefixt werden.
                            first_dominated = true;
                        } else {
                        dominated = true;
                        break;
                        }
                    }
                    // TODO: Hier müsste nicht jedes Mal auf die load überprüft werden. DAs könnte optimiert werden.
                    if(it->load >= newlabel.load && newlabel.dominates(*it, elementary, ngParam)){
                        it = q[i].erase(it);
                        continue;
                    }
                    ++it;
                }
            }
            if(!dominated){
                q[i].insert(newlabel);
            }

        }

        auto t1 = high_resolution_clock::now();
        auto duration = duration_cast<seconds>(t1-t0).count();
        if(duration > time_limit){
            *abort_early = true;
            break;
        }

        // Check if the path to the last node has negative reduced cost
        double newcost = x.finishing_cost(dual,farkas);
        if((newcost < -1e-6) && (x.v != 0))
            ++num_paths;
        if((newcost < red_cost_bound) && (x.v != 0)){
            if(new_vars.size() == max_vars){
                new_vars[index_of_max_red_cost(dual,farkas,new_vars)] = &x;
                red_cost_bound = maximal_cost(dual,farkas,new_vars);
            } else {
                new_vars.push_back(&x);
            }
        }
    }
    for(unsigned i=0;i<new_vars.size();++i){
        new_vars[i]->write_path_to_output(result+i*max_path_len);
    }
    return num_paths;

}
