#include <vector>
#include <queue>
#include <list>
#include <iostream>
#include <cmath>
#include <algorithm>
#include "labelling_lib.h"

using std::vector;
using std::queue;
using std::cout;
using std::endl;

vector<double> nodes;
vector<vector<double> > edges;
unsigned num_nodes;
double capacity;
unsigned max_path_len;

Label::Label(unsigned v, unsigned pred, double cost, double load):v{v}, pred{pred}, cost{cost}, load{load} {
    unsigned size = (num_nodes % 32 == 0) ? num_nodes / 32 : num_nodes / 32 + 1;
    pred_field = new unsigned[size];
}

Label::Label(unsigned v, unsigned pred, double cost, double load, Label* pred_ptr):v{v}, pred{pred}, cost{cost}, load{load}, pred_ptr{pred_ptr} {
    unsigned size = (num_nodes % 32 == 0) ? num_nodes / 32 : num_nodes / 32 + 1;
    pred_field = new unsigned[size];
}

Label::~Label(){}//delete[] pred_field;}

bool Label::dominates(const Label& x, const bool elementary){
    if((this->cost <= x.cost) && (this->load <= x.load)){
        if(!elementary)
            return true;
        if(x.v == 0  || this->v == 0)
            cout << "PRICER_C ERROR: Dominance check on start label." << endl;
        Label* own_pred = this->pred_ptr;
        while(own_pred->v > 0){
            if(!x.check_whether_in_path(own_pred->v))
                return false;
            own_pred = own_pred->pred_ptr;
        }
        return true;
    }
    return false;
}

bool Label::check_whether_in_path(const unsigned node) const{
    if(node == 0)
        cout << "PRICER_C ERROR: Path check with node 0." << endl;
    const Label* current_label = this;
    while(current_label->v > 0){
        if(current_label->v == node)
            return true;
        current_label = current_label->pred_ptr;
    }
    return false;
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

// void init_bit_field(unsigned num_nodes){
//     pred_field = new unsigned[]
// }

void initGraph(unsigned num_nodes, unsigned* node_data, double* edge_data, const double capacity, const unsigned max_path_len){
    ::num_nodes = num_nodes;
    ::capacity = capacity;
    ::max_path_len = max_path_len;
    if(!nodes.empty())
        nodes.clear();
    if(!edges.empty())
        edges.clear();


    for(unsigned i=0;i<num_nodes;i++){
        nodes.push_back(node_data[i]);
        vector<double> v;
        for(unsigned j=0;j<num_nodes;j++){
            v.push_back(edge_data[i*num_nodes + j]);
        }
        edges.push_back(v);
    }
    cout << "PRICER_C: Graph data successfully copied to C." << endl;
}

unsigned labelling(double const * dual, const bool farkas, const bool elementary, const unsigned long max_vars, unsigned* result){
    queue<Label*> q;
    vector<std::list<Label>> labels;
    vector<Label*> new_vars;
    labels.resize(num_nodes);
    labels[0].push_back(Label {0,0,0,0});
    q.push(&(labels[0].back()));

    double red_cost_bound = -1e-6;
    unsigned num_paths = 0;

    while(!q.empty()){
        Label* x = q.front();
        q.pop();

        for(unsigned i=1;i<num_nodes;++i){
            if(elementary && x->check_whether_in_path(i))
                continue;
            if(i != x->v){
                double newload = x->load + nodes[i];
                if(newload > capacity)
                    continue;
                bool dominated = false;
                double newcost = x->cost - dual[i-1];
                newcost = farkas ? newcost: newcost + edges[x->v][i];
                Label newlabel {i, x->v, newcost, newload, x};

                for(auto& label: labels[i]){
                    if(label.dominates(newlabel, elementary)){
                        dominated = true;
                        break;
                    }
                }
                if(!dominated){
                    labels[i].push_back(newlabel);
                    q.push(&(labels[i].back()));
                    // TODO: Hier könnte man prüfen, ob ein anderes Label dominiert wird und sich dieses deshalb entfernen lässt
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
            }
        }
    }

    for(unsigned i=0;i<std::min(max_vars,new_vars.size());++i){
        new_vars[new_vars.size()-i-1]->write_path_to_output(result+i*max_path_len);
    }

    return num_paths;

}
