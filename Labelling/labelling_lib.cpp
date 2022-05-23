#include <vector>
#include <list>
#include <iostream>
#include <cmath>
#include <algorithm>
#include "labelling_lib.h"

using std::vector;
using std::list;
using std::cout;
using std::endl;

vector<double> nodes;
vector<vector<double> > edges;
unsigned num_nodes;
double capacity;
unsigned max_path_len;

Label::Label(unsigned v, unsigned pred, double cost, double load):v{v}, pred{pred}, cost{cost}, load{load} {
    pred_field[0] = 1;
    //     unsigned size = (num_nodes % 32 == 0) ? num_nodes / 32 : num_nodes / 32 + 1;
    //     pred_field = new unsigned[size];
}

Label::Label(unsigned v, unsigned pred, double cost, double load, Label* pred_ptr):v{v}, pred{pred}, cost{cost}, load{load}, pred_ptr{pred_ptr} {
        for (unsigned i = 0; i<2; ++i){
            pred_field[i] = pred_ptr->pred_field[i];
        }
        pred_field[v/64] = pred_field[v/64] | 1 << (63 - v%64);
        //     unsigned size = (num_nodes % 32 == 0) ? num_nodes / 32 : num_nodes / 32 + 1;
        //     pred_field = new unsigned[size];
}

Label::~Label(){}//delete[] pred_field;}

bool Label::dominates(const Label& x, const bool elementary){
    if((this->cost <= x.cost) && (this->load <= x.load)){
        if(!elementary)
            return true;
        if(x.v == 0  || this->v == 0)
            cout << "PRICER_C ERROR: Dominance check on start label." << endl;

        if(((this->pred_field[0] & x.pred_field[0]) == this->pred_field[0]) && ((this->pred_field[1] & x.pred_field[1]) == this->pred_field[1])){
            return true;
        } else {
            return false;
        }
    }
    return false;
}

bool Label::check_whether_in_path(const unsigned node) const{
    if(node == 0)
        cout << "PRICER_C ERROR: Path check with node 0." << endl;

        unsigned long mask = 1 << (63 - node%64);
        if((this->pred_field[v/64] & mask) == mask){
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

list<Label>::iterator erase_Label(list<Label*>& q, vector<list<Label>>& labels, list<Label>::iterator& it, unsigned i);

void erase_child_label(list<Label*>& q, vector<list<Label>>& labels, Label* label, unsigned i){
    auto it = labels[i].begin();
    while(it != labels[i].end()){
        if(&(*it) == label){
            erase_Label(q,labels,it, i);
            return;
        }
    }
}

list<Label>::iterator erase_Label(list<Label*>& q, vector<list<Label>>& labels, list<Label>::iterator& it, unsigned i){
    // Remove the label from the queue
    for(auto q_it = q.begin(); q_it != q.end();++q_it){
        if (*q_it == &(*it)){
            q.erase(q_it);
            break;
        }
    }

    // All child nodes have to been deleted as well.
    for(auto child_it = it->childs.begin(); child_it != it->childs.end();){
        erase_child_label(q,labels, *child_it, (*child_it)->v);
        child_it = it->childs.erase(child_it);
    }

    return labels[i].erase(it);
}

void initGraph(unsigned num_nodes, unsigned* node_data, double* edge_data, const double capacity, const unsigned max_path_len){
    if(num_nodes > 120){
        cout << "PRICER_C Error: The number of nodes is to large for the Label struct. Abort." << endl;
        return;
    }
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

unsigned labelling(double const * dual, const bool farkas, const bool elementary, const unsigned long max_vars, const bool cyc2, unsigned* result){
    list<Label*> q;
    vector<list<Label>> labels;
    vector<Label*> new_vars;
    labels.resize(num_nodes);
    labels[0].push_back(Label {0,0,0,0});
    q.push_back(&(labels[0].back()));

    double red_cost_bound = -1e-6;
    unsigned num_paths = 0;

    while(!q.empty()){
        Label* x = q.front();
        q.pop_front();

        for(unsigned i=1;i<num_nodes;++i){
            if(elementary && x->check_whether_in_path(i))
                continue;
            if (i == x->v)
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
            Label newlabel {i, x->v, newcost, newload, x};

            for(auto& label: labels[i]){
                if(label.dominates(newlabel, elementary)){
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
                newlabel_ref->pred_ptr->childs.push_back(newlabel_ref);
                q.push_back(newlabel_ref);

                auto it = labels[i].begin();
                while(it != labels[i].end()){
                    if(newlabel_ref->dominates(*it, elementary) && newlabel_ref != &(*it)){
                        // cout << "Found newlabel dominating an old one" << endl;
                        // cout << "Newlabel v = " << newlabel_ref->v << " and pred is " << newlabel_ref->pred << endl;
                        // cout << "Newlabel cost = " << newlabel_ref->cost << " and load is " << newlabel_ref->load << endl;
                        // cout << "dominated v = " << it->v << " and pred is " << it->pred << endl;
                        // cout << "dominated cost = " << it->cost << " and load is " << it->load << endl;


                        // Remove the label from the queue
                        for(auto q_it = q.begin(); q_it != q.end();++q_it){
                            if (*q_it == &(*it)){
                                q.erase(q_it);
                                break;
                            }
                        }
                        // Reset the pred_ptr of the child nodes
                        // TODO: An dieser STelle könnten alle Kinder des dominierten Labels entfernt werden.
                        // for(auto child : it->childs){
                        //     child->pred_ptr = newlabel_ref;
                        // }
                        //
                        // it = labels[i].erase(it);
                        it = erase_Label(q, labels, it, i);
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
                // break;

            } else {
                new_vars.push_back(x);
            }
        }
    }
    // cout << "SPPRC finished: now writing output" << endl;
    for(unsigned i=0;i<std::min(max_vars,new_vars.size());++i){
        new_vars[new_vars.size()-i-1]->write_path_to_output(result+i*max_path_len);
    }

    return num_paths;

}
