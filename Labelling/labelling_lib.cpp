#include <vector>
#include <queue>
#include <iostream>
#include <cmath>
#include "labelling_lib.h"

using std::vector;
using std::queue;
using std::cout;
using std::endl;

vector<myProcessor> myProcessors;
vector<unsigned> nodes;
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

myProcessor::myProcessor(int size, double* data){
    this->size = size;
    this->data = data;
}

int myProcessor::process(double *d, int size){
    for (int i=0; i<size; i++){
        d[i] = d[i] * d[i];
    }
    return 0;
}

unsigned int myProcessorInit(int size, double* data){
    unsigned int id;
    myProcessor tmpInst(size, data);
    myProcessors.push_back(tmpInst);
    id = myProcessors.size() -1;
    return id;
}

int myProcessorProcess(unsigned int id, double*d, int size){
    return myProcessors[id].process(d,size);
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
    // Wo gehen prints hin mit cffi?
    cout << "Graph data successfully copied to C." << endl;
}

void labelling(double const * dual,const bool farkas, unsigned* result){
    queue<Label> q;
    vector<vector<Label>> labels;
    labels.resize(num_nodes);
    Label start {0,0,0,0};
    q.push(start);

    while(!q.empty()){
        Label &x = q.front();
        q.pop();

        for(unsigned i=1;i<num_nodes -1;++i){
            if(i != x.v){
                double newload = x.load + nodes[i];
                if(newload > capacity)
                    continue;
                bool dominated = false;
                double newcost = x.cost + edges[x.v][i] - dual[i-1];
                Label newlabel {i,x.v,newcost, newload, &x};
                // newlabel.pred_ptr = &x;
                // cout << "Created label at node " << newlabel.v << " and pred is " << newlabel.pred << endl;
                // cout << "Otherwise pred_ptr points to " << (newlabel.pred_ptr)->v << endl;
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
        double newcost = x.cost + edges[x.v][num_nodes - 1];
        // cout << "current node before loop is " << x.v << " and pred is " << x.pred << endl;


        if (newcost < 0){
            cout << "Found Path with negative reduced cost" << endl;
            cout << "current node in loop is " << x.v << " and pred is " << x.pred << endl;
            cout << "Otherwise pred_ptr points to " << (x.pred_ptr)->v << endl;

            unsigned path_len = 2;
            Label& current_label = x;
            while(current_label.pred != 0){
                if(path_len >= capacity)
                    break;
                ++path_len;
                current_label = *(current_label.pred_ptr);
                cout << "current node in path_len is " << current_label.v << " and pred is " << current_label.pred << endl;

            }
            cout << "path length is " << path_len << endl;

            current_label = x;
            result[path_len - 1] = num_nodes - 1;
            result[0] = 0;
            for(unsigned i = path_len - 2; i > 0; --i){
                result[i] = current_label.v;
                current_label = *(current_label.pred_ptr);
            }

            return;
        }


    }
    cout << "There are not paths with negative reduced costs" << endl;
}
