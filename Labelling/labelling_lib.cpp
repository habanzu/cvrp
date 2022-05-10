#include <vector>
#include <queue>
#include <list>
#include <iostream>
#include <cmath>
#include "labelling_lib.h"

using std::vector;
using std::queue;
using std::cout;
using std::endl;

vector<double> nodes;
vector<vector<double> > edges;
unsigned num_nodes;
double capacity;

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

void initGraph(unsigned num_nodes, unsigned* node_data, double* edge_data, const double capacity){
    ::num_nodes = num_nodes;
    ::capacity = capacity;
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

void labelling(double const * dual, const bool farkas, const bool elementary, unsigned* result){
    queue<Label*> q;
    vector<std::list<Label>> labels;
    labels.resize(num_nodes);
    Label start {0,0,0,0};
    labels[0].push_back(start);
    q.push(&(labels[0].back()));

    double lowest_red_cost = -1e-6;
    bool success = false;

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
                // newlabel.pred_ptr = x;
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
        double newcost = x->cost - dual[num_nodes-1];
        newcost = farkas ? newcost: newcost + edges[x->v][0];

        if ((newcost < lowest_red_cost) && (x->v != 0)){
            // cout << "Found Path with negative reduced cost" << endl;

            unsigned path_len = 2;
            Label* current_label = x;
            while(current_label->pred > 0){
                // Path with capacity + 1 edges has visited capacity + 2 nodes, of which start and end node don't have a demand
                if(path_len > (capacity + 2)){
                    cout << "PRICER_C ERROR: Path length exceeds maximum. Current value of path_len is " << path_len << endl;
                    return;
                }
                ++path_len;
                current_label = current_label->pred_ptr;
            }

            current_label = x;
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
            success = true;
        }
    }

    if(!success){
        result[0] = 1;
    }
}
