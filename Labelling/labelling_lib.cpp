#include <vector>
#include <queue>
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

bool Label::dominates(const Label& x){
    if((this->cost <= x.cost) && (this->load <= x.load)){
        return true;
    } else{
        return false;
    }
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
    cout << "Graph data successfully copied to C." << endl;
}

void labelling(double const * dual,const bool farkas, unsigned* result){
    queue<Label> q;
    vector<vector<Label>> labels;
    labels.resize(num_nodes);
    Label start {0,0,0,0};
    q.push(start);

    while(!q.empty()){
        Label *x = &q.front();
        q.pop();

        for(unsigned i=1;i<num_nodes -1;++i){
            if(i != x->v){
                double newload = x->load + nodes[i];
                if(newload > capacity)
                    continue;
                bool dominated = false;
                double newcost = x->cost - dual[i-1];
                newcost = farkas ? newcost: newcost + edges[x->v][i];
                Label newlabel {i,x->v,newcost, newload, x};
                for(auto& label: labels[i]){
                    if(label.dominates(newlabel)){
                        dominated = true;
                        break;
                    }
                }
                if(!dominated){
                    q.push(newlabel);
                    labels[i].push_back(newlabel);
                    // TODO: Hier könnte man prüfen, ob ein anderes Label dominiert wird und sich dieses deshalb entfernen lässt
                }
            }
        }

        // Check if the path to the last node has negative reduced cost
        double newcost = x->cost - dual[num_nodes-1];
        newcost = farkas ? newcost: newcost + edges[x->v][num_nodes - 1];

        if ((newcost < 0) && (x->v != 0)){
            // cout << "Found Path with negative reduced cost" << endl;

            unsigned path_len = 2;
            Label* current_label = x;
            while(current_label->pred != 0){
                // Path with capacity + 1 edges has visited capacity + 2 nodes, of which start and end node don't have a demand
                if(path_len >= capacity + 1){
                    cout << "ERROR: Path length exceeds maximum." << endl;
                    break;
                }
                ++path_len;
                current_label = current_label->pred_ptr;
            }

            current_label = x;
            result[path_len] = num_nodes - 1;
            result[0] = 0;
            for(unsigned i = path_len - 1; i > 0; --i){
                result[i] = current_label->v;
                if(current_label->v == 0){
                    cout << "WARNING: Start label in path when writing result" << endl;
                    break;
                }
                current_label = current_label->pred_ptr;
            }

            return;
        }


    }
    // cout << "There are not paths with negative reduced costs" << endl;
    result[0] = 1;
}
