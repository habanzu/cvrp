#include <vector>
#include <list>
#include <iostream>
#include <cmath>
#include <algorithm>
#include <set>
#include <bitset>

#include "labelling_lib.h"

using std::vector;
using std::list;
using std::cout;
using std::endl;

vector<double> nodes;
vector<vector<double> > edges;
vector<std::bitset<512> > neighborhoods;
unsigned num_nodes;
double capacity;
unsigned max_path_len;

struct less_than {
    bool operator()(const Label* label1, const Label* label2) const{
        return (label1->load < label2->load);
    }
};

Label::Label(unsigned v, unsigned pred, double cost, double load):v{v}, pred{pred}, cost{cost}, load{load} {
    pred_field[0] = 1;
}

Label::Label(unsigned v, unsigned pred, double cost, double load, Label* pred_ptr):v{v}, pred{pred}, cost{cost}, load{load}, pred_ptr{pred_ptr} {
    pred_field = pred_ptr->pred_field;
    pred_field[v] = 1;
}

Label::Label(unsigned v, unsigned pred, double cost, double load, Label* pred_ptr, std::bitset<512> ng_memory):v{v}, pred{pred}, cost{cost}, load{load}, pred_ptr{pred_ptr}, ng_memory{ng_memory}{
    pred_field = pred_ptr->pred_field;
    pred_field[v] = 1;
}

bool Label::dominates(const Label& x, const bool elementary, const bool ngPath){
    if((this->cost <= x.cost) && (this->load <= x.load)){
        if(!elementary && !ngPath)
            return true;
        if(x.v == 0  || this->v == 0)
            cout << "PRICER_C ERROR: Dominance check on start label." << endl;

        auto& own_comparator = ngPath ? this->ng_memory : this->pred_field;
        auto& x_comparator = ngPath ? x.ng_memory : x.pred_field;

        if((own_comparator & x_comparator) == own_comparator){
            return true;
        } else {
            return false;
        }
    }
    return false;
}

bool Label::check_whether_in_path(const unsigned node, const bool ngPath) const{
    if(node == 0)
        cout << "PRICER_C ERROR: Path check with node 0." << endl;

        std::bitset<512> mask(0);
        mask[node] = 1;

        auto& comparator = ngPath ? this->ng_memory : this->pred_field;
        if((comparator & mask) == mask){
            return true;
        } else {
            return false;
        }
}

unsigned Label::path_len(){
    unsigned path_len = 2;
    Label* current_label = this;
    while(current_label->pred > 0){
        // Path with capacity + 1 edges has visited capacity + 2 nodes, of which start and end node don't have a demand
        if(path_len > (capacity + 2)){
            cout << "PRICER_C ERROR: Path length exceeds maximum. Current value of path_len is " << path_len << endl;
            return 0;
        }
        ++path_len;
        current_label = current_label->pred_ptr;
    }
    return path_len;
}

void Label::write_path_to_output(unsigned* result){
    unsigned path_len = this->path_len();
    if(path_len > max_path_len){
        cout << "PRICER_C WARNING: Path exceeds maximum path length" << endl;
        return;
    }

    Label* current_label = this;
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

double Label::finishing_cost(double const * dual, const bool farkas){
    double finishing_cost = this->cost - dual[num_nodes-1];
    finishing_cost = farkas ? finishing_cost: finishing_cost + edges[this->v][0];
    return finishing_cost;
}

unsigned minimal_index(double const* dual, const bool farkas, const vector<Label*>& new_vars ){
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

void initGraph(unsigned num_nodes, unsigned* node_data, double* edge_data, const double capacity, const unsigned max_path_len, const unsigned ngParam){
    if(num_nodes > 512){
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
        std::bitset<512> neighborhood;
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

unsigned labelling(double const * dual, const bool farkas, const bool elementary, const unsigned long max_vars, const bool cyc2, unsigned* result, const bool abort_early, const bool ngPath){
    std::multiset<Label*, less_than> q;
    vector<list<Label>> labels;
    vector<Label*> new_vars;
    labels.resize(num_nodes);
    labels[0].push_back(Label {0,0,0,0});
    (labels[0].begin())->ng_memory = std::bitset<512>();
    q.insert(&(labels[0].back()));

    double red_cost_bound = -1e-6;
    unsigned num_paths = 0;

    while(!q.empty()){
        Label* x = *(q.begin());
        q.erase(q.begin());

        for(unsigned i=1;i<num_nodes;++i){
            if (i == x->v)
                continue;
            if(elementary && x->check_whether_in_path(i, ngPath))
                continue;
            if(ngPath && x->check_whether_in_path(i, ngPath))
                continue;
            if(cyc2 && x->pred == i)
                continue;

            double newload = x->load + nodes[i];
            if(newload > capacity)
                continue;

            bool dominated = false;
            bool first_dominated = false;
            double newcost = x->cost - dual[i-1];
            newcost = farkas ? newcost: newcost + edges[x->v][i];
            std::bitset<512> neighborhood;
            if(ngPath){
                // neighborhood = (x->v == 0) ? neighborhoods[i] : neighborhoods[i] & x->ng_memory;
                neighborhood = neighborhoods[i] & x->ng_memory;
                neighborhood[i] = 1;
            }
            Label newlabel {i, x->v, newcost, newload, x, neighborhood};

            for(auto& label: labels[i]){
                if(label.dominates(newlabel, elementary, ngPath)){
                    if(cyc2 && !first_dominated && (label.pred != newlabel.pred)){
                        first_dominated = true;
                        continue;
                    } else {
                    dominated = true;
                    break;
                    }
                }
            }
            if(!dominated){
                labels[i].push_back(newlabel);
                Label* newlabel_ref = &(labels[i].back());
                q.insert(newlabel_ref);

                for(auto it = labels[i].begin(); it != labels[i].end(); ){
                    if(newlabel_ref->dominates(*it, elementary, ngPath) && newlabel_ref != &(*it)){
                        // Remove the label from the queue
                        for(auto q_it = q.begin(); q_it != q.end();++q_it){
                            if (*q_it == &(*it)){
                                q.erase(q_it);
                                break;
                            }
                        }

                        it = labels[i].erase(it);

                    } else{
                        ++it;
                    }
                }
            }

        }

        // Check if the path to the last node has negative reduced cost
        double newcost = x->finishing_cost(dual,farkas);
        if((newcost < -1e-6) && (x->v != 0))
            ++num_paths;
        if((newcost < red_cost_bound) && (x->v != 0)){
            if(new_vars.size() == max_vars){
                new_vars[minimal_index(dual,farkas,new_vars)] = x;
                red_cost_bound = maximal_cost(dual,farkas,new_vars);
            } else {
                new_vars.push_back(x);
                if((new_vars.size() == max_vars) && abort_early){
                    // Warum löst dieser Code eine solch Katastrophale Laufzeit aus?
                    break;
                }
            }
        }
    }
    for(unsigned i=0;i<std::min(max_vars,new_vars.size());++i){
        new_vars[new_vars.size()-i-1]->write_path_to_output(result+i*max_path_len);
    }

    return num_paths;

}
