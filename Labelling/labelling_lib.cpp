#include <vector>
#include <list>
#include <iostream>
#include <cmath>
#include <algorithm>
#include <set>
#include <bitset>
#include <chrono>

#include "labelling_lib.h"

using std::list;
using std::cout;
using std::endl;
using std::multiset;
using namespace std::chrono;

struct less_than {
    // Provides the ability to sort the labels using algorithms from the standard library
    bool operator()(const Label& label1, const Label& label2) const{
        if(label1.load == label2.load)
            return (label1.cost < label2.cost);
        return (label1.load < label2.load);
    }
};

struct cyc2_dominant_labels{
    // 2-cycle elimination has a different
    // label1->cost <= label2->cost should always be true
    unsigned num_labels;
    multiset<Label, less_than>::const_iterator label1;
    multiset<Label, less_than>::const_iterator label2;
    cyc2_dominant_labels(){
        num_labels = 0;
    }
};

vector<unsigned> nodes;
vector<vector<double> > edges;
vector<vector<bitset<neighborhood_size> >> neighborhoods;
vector<unsigned> neighborhood_indices;
unsigned num_nodes;
double capacity;
unsigned max_path_len;
vector<vector<cyc2_dominant_labels>> cyc2_dominators;

Label::Label(){}

Label::Label(unsigned v, unsigned pred, double cost, unsigned load):v{v}, pred{pred}, cost{cost}, load{load}, farley_val{0} {
    pred_field[0] = 1;
    ng_memory = bitset<neighborhood_size>();
}

Label::Label(unsigned v, unsigned pred, double cost, unsigned load, Label* pred_ptr):v{v}, pred{pred}, cost{cost}, load{load}, pred_ptr{pred_ptr} {
    pred_field = pred_ptr->pred_field;
    pred_field[v] = 1;
}

Label::Label(unsigned v, unsigned pred, double cost, unsigned load, Label* pred_ptr, bitset<neighborhood_size>& ng_memory):v{v}, pred{pred}, cost{cost}, load{load}, pred_ptr{pred_ptr}, ng_memory{ng_memory}{
    pred_field = pred_ptr->pred_field;
    pred_field[v] = 1;
}

Label::Label(unsigned v, unsigned pred, double cost, unsigned load, Label* pred_ptr, bitset<neighborhood_size>& ng_memory, double farley_val):v{v}, pred{pred}, cost{cost}, load{load}, farley_val{farley_val},  pred_ptr{pred_ptr}, ng_memory{ng_memory}{
    pred_field = pred_ptr->pred_field;
    pred_field[v] = 1;
}

Label::Label(unsigned v, unsigned pred, double cost, unsigned load, Label* pred_ptr, double farley_val):v{v}, pred{pred}, cost{cost}, load{load}, farley_val{farley_val}, pred_ptr{pred_ptr}{
    pred_field = pred_ptr->pred_field;
    pred_field[v] = 1;
}

bool Label::dominates(const Label& x, const bool elementary, const bool ngPath, const bool farley) const{
    if((this->cost <= x.cost) && (this->load <= x.load)){
        if(x.v == 0  || this->v == 0)
            cout << "PRICER_C ERROR: Dominance check on start label." << endl;
        if(!elementary && !ngPath && !farley)
            return true;
        // TODO: For Farley with ng Paths, this code needs to be adapted
        if(farley && !(this->farley_val >= x.farley_val))
            return false;
            // return (this->farley_val >= x.farley_val);
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

bool cyc2_dominates(multiset<Label, less_than>& q_i, const multiset<Label, less_than>::const_iterator& x){
    // siehe TODO unten für dne Grund des auskommentierten Codes
    // vector<multiset<Label, less_than>::const_iterator> delete_before_finishing;
    bool dominated = false;
    // For whatever reason, this yields wrong results (aka not enough variables are found when doing the pricing)
    // but it works correctly for i <= x->load
    for(unsigned i = x->load;i <= x->load; ++i){
        cyc2_dominant_labels& comparators = cyc2_dominators[x->v][i];
        if(comparators.num_labels == 0){
            ++comparators.num_labels;
            comparators.label1 = x;
            continue;
        }
        // cout << "Dominance check: " << comparators->label1->cost << endl;
        // if(comparators->label1->cost <= x->cost){
        //     if(x->load == i)
        //         dominated = true;
        //     break;
        // }
        // // Wieso ist das hier problematisch? Es müsste doch immer eine absteigende Folge sein?
        // // if(comparators.label1->load == i)
        // //     delete_before_finishing.push_back(comparators.label1);
        // comparators->label1 = x;
        // continue;

        if(comparators.num_labels == 1){
            if(comparators.label1->pred == x->pred){
                if(comparators.label1->cost <= x->cost){
                    if(x->load == i)
                        dominated = true;
                    continue;
                } else {
                    // if(comparators.label1->load == i)
                    //     delete_before_finishing.push_back(comparators.label1);
                    comparators.label1 = x;
                    continue;
                }
            }
            //see invariant in definiton
            if(comparators.label1->cost <= x->cost){
                comparators.label2 = x;
            } else {
                comparators.label2 = comparators.label1;
                comparators.label1 = x;
            }
            ++comparators.num_labels;
            continue;
        }
        if(comparators.label2->cost <= x->cost ||
            (comparators.label1->pred == x->pred && comparators.label1->cost <= x->cost)){
            if (x->load == i)
                dominated = true;
            continue;
        }
        if(comparators.label1->pred == x->pred && comparators.label1->cost > x->cost){
            // if(comparators.label1->load == i)
            //     delete_before_finishing.push_back(comparators.label1);
            comparators.label1 = x;
            continue;
        }
        if(comparators.label1->cost > x->cost){
            // if(comparators.label2->load == i)
            //     delete_before_finishing.push_back(comparators.label2);
            comparators.label2 = comparators.label1;
            comparators.label1 = x;
            continue;
        }
        // if(comparators.label1->cost <= x->cost){

            comparators.label2 = x;
            continue;
            // if(comparators.label2->load == i)
            //     delete_before_finishing.push_back(comparators.label2);

        // }
        cout << "SHOULD NOT HAPPEN!" << endl;
        return false;
    }
    // TODO: Mögliche Verbesserung: Im Moment werden Labels beim rausschmeissen aus der Datenstruktur nicht aus q gelöscht.
    // Der Grund ist: Es ist unklar, wann der letzte Iterator von einem Label entfernt wird.
    // Von daher ist es auch nicht klar, wann das Element gelöscht werden kann.
    // cout << "successfull dominance check" << endl;
    // for(auto it : delete_before_finishing){
    //     q_i.erase(it);
    // }
    return dominated;

}

bool Label::check_whether_in_path(const unsigned node, const bool ngPath) const{
    if(node == 0)
        cout << "PRICER_C ERROR: Path check with node 0." << endl;

    bitset<neighborhood_size> mask(0);
    mask[node] = 1;

    auto& comparator = ngPath ? this->ng_memory : this->pred_field;
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
    unsigned min_index = 2*num_nodes;
    double min_load = capacity + 1;
    for(unsigned i = 0; i < num_nodes; ++i){
        if(!q[i].empty() && q[i].begin()->load < min_load){
            min_index = i;
            min_load = q[i].begin()->load;
        }
    }
    if(min_index >= num_nodes)
        cout << "PRICER_C ERROR: Couldnt find valid minimal index in labelling queue." << endl;
    return min_index;
}

bool queue_empty(const vector<multiset<Label, less_than>>& q){
    for(unsigned i = 0; i < num_nodes; ++i){
        if(!q[i].empty())
            return false;
    }
    return true;
}

vector<bitset<neighborhood_size> > init_neighborhoods(const unsigned num_nodes, const unsigned ngParam){
    // There are num_nodes -1 nodes without the depot, so ngParam needs to be less than that
    if(ngParam >= num_nodes - 1){
        cout << "PRICER_C ERROR: ngParam > num_nodes" << endl;
    }

    if(ngParam == 0){
        cout << "PRICER_C ERROR: ngParam can't be 0" << endl;
    }

    vector<bitset<neighborhood_size> > neighborhoods;
    // Initialize neighborhoods for ng-Path Relaxations
    neighborhoods.push_back(0);
    for(unsigned i =1; i<num_nodes;++i){
        bitset<neighborhood_size> neighborhood;

        // Initialize neighborhood with ngParam first nodes
        double edge_bound = i == 1 ? edges[1][2] : edges[i][1];
        neighborhood[i] = 1;
        const unsigned upper_index = (i <= ngParam) ? ngParam + 1 : ngParam;
        for(unsigned j=1; j<= upper_index; ++j){
            neighborhood[j] = 1;
            edge_bound = (edges[i][j] > edge_bound) ? edges[i][j] : edge_bound;
        }

        // Search the rest of the nodes for cheaper neighbors
        unsigned start_index = (i <= ngParam) ? ngParam + 2 : ngParam + 1;

        for(unsigned j = start_index; j < num_nodes; ++j){
            if(j==i || neighborhood[j]) continue;
            if(edges[i][j] < edge_bound){
                neighborhood[j] = 1;
                for(unsigned l = 1;l <= num_nodes;++l){
                    if(l==num_nodes){
                        cout << "PRICER_C ERROR: Index out of range when initializing neighborhoods" << endl;
                    }
                    if(l==i) continue;
                    if((edges[i][l] == edge_bound) && neighborhood[l] == 1){
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
    return neighborhoods;
}

void initGraph(const unsigned num_nodes, const unsigned* node_data, const double* edge_data, const double capacity, const unsigned max_path_len, const unsigned* ngParams){
    // copy the data from the python code to the C code, so that it does not need to be passed as an argument during labelling.
    if(num_nodes > neighborhood_size){
        cout << "PRICER_C ERROR: The number of nodes is to large for the Label struct. Abort." << endl;
        return;
    }
    ::num_nodes = num_nodes;
    ::capacity = capacity;
    ::max_path_len = max_path_len;
    nodes.clear();
    edges.clear();
    neighborhoods.clear();
    neighborhood_indices.clear();

    for(unsigned i=0;i<num_nodes;++i){
        nodes.push_back(node_data[i]);
        vector<double> v;
        for(unsigned j=0;j<num_nodes;++j){
            v.push_back(edge_data[i*num_nodes + j]);
        }
        edges.push_back(v);
    }

    // The first element of ngParams should be the size of the list.
    const unsigned size_ngParams = ngParams[0];

    for(unsigned i =1; i<=size_ngParams;++i){
        const unsigned ngParam = ngParams[i];
        if(ngParam >= neighborhood_indices.size())
            neighborhood_indices.resize(ngParam+1);
        neighborhoods.push_back(init_neighborhoods(num_nodes,ngParams[i]));
        neighborhood_indices[ngParam] = i-1;
    }

    cout << "PRICER_C: Graph data successfully copied to C." << endl;
}

unsigned labelling(const double * dual, const bool farkas, const unsigned time_limit, const bool elementary, const unsigned long max_vars, const bool cyc2, unsigned* result, unsigned* additional_information, const unsigned ngParam, double* farley_res, const bool ESPPRC_heur){
    // This function implements algorithm 1 from the thesis. Start here for understanding the file. Alternatively look at initGraph() fist and then here.
    auto t0= high_resolution_clock::now();
    unsigned total_time;
    duration<double> time_propagated_dominance {0};
    duration<double> time_unpropagated_dominance {0};

    // Initialize the data structures of the labelling algorithm
    vector<multiset<Label, less_than>> q;
    vector<list<Label> > propagated;
    vector<Label*> new_vars;
    propagated.resize(num_nodes);
    q.resize(num_nodes);
    q[0].insert(Label {0,0,0,0});
    if(cyc2){
        cyc2_dominators.clear();
        cyc2_dominators.resize(num_nodes);

        for(auto& load_vector: cyc2_dominators){
            load_vector.resize(capacity+1, cyc2_dominant_labels());
        }
    }

    double red_cost_bound = -1e-6;
    double best_farley_val = 0;
    const bool farley = (*farley_res == 1);
    const bool ngPath = (ngParam != 0);
    unsigned num_paths = 0;

    if(farley && neighborhoods.size() == 0){
        cout << "PRICER_C ERROR: neighborhood cant be empty for farley."  << endl;
    }

    // Propagate labels in the queue as long as possible
    // See algorithm 1 in the thesis
    while(!queue_empty(q)){
        unsigned queue_index = index_minimum_load_in_queue(q);
        auto it_q = q[queue_index].begin();
        propagated[it_q->v].push_back(*it_q);
        Label& x = propagated[it_q->v].back();
        q[queue_index].erase(it_q);

        // Consider all labels reachable.
        for(unsigned i=1;i<num_nodes;++i){
            if (i == x.v || dual[i-1] <= 0 )
                continue;
            if((elementary || ngPath || ESPPRC_heur) && x.check_whether_in_path(i, ngPath))
                continue;
            if(cyc2 && x.pred == i)
                continue;

            // Create new label
            const unsigned newload = x.load + nodes[i];
            if(newload > capacity)
                continue;
            bool dominated = false;
            double newcost;
            if(farley){
                newcost = x.cost + edges[x.v][i];
            } else {
                newcost = farkas ? x.cost - dual[i-1]: x.cost - dual[i-1] + edges[x.v][i];
            }
            bitset<neighborhood_size> neighborhood;
            Label newlabel;
            if(ngPath){
                neighborhood = neighborhoods[neighborhood_indices[ngParam]][i] & x.ng_memory;
                neighborhood[i] = 1;
                if(farley){
                    const double new_farley_val = x.farley_val + dual[i-1];
                    newlabel = Label{i, x.v, newcost, newload, &x, neighborhood, new_farley_val};
                } else {
                    newlabel = Label{i, x.v, newcost, newload, &x, neighborhood};
                }
            } else{
                if(farley){
                    const double new_farley_val = x.farley_val + dual[i-1];
                    newlabel = Label{i, x.v, newcost, newload, &x, new_farley_val};
                } else {
                    newlabel = Label{i, x.v, newcost, newload, &x};
                }
            }
            // Dominance check when using 2-cycle elimination.
            if(cyc2){
                const auto& new_label_it = q[i].insert(newlabel);
                if(cyc2_dominates(q[i], new_label_it))
                    q[i].erase(new_label_it);
                continue;
            }
            // Dominance check otherwise
            auto t5 = high_resolution_clock::now();
            for(Label& label: propagated[i]){
                if(label.dominates(newlabel, elementary, ngPath, farley)){
                    dominated = true;
                    break;
                }
            }

            auto t6 = high_resolution_clock::now();
            time_propagated_dominance += t6 - t5;

            // Add undominated labels
            if(!dominated){
                for(auto it = q[i].begin(); it != q[i].end(); ){
                    if(it->load <= newlabel.load && it->dominates(newlabel, elementary, ngPath, farley)){
                        dominated = true;
                        break;
                    }
                    // TODO: Hier müsste nicht jedes Mal auf die load überprüft werden. Das könnte optimiert werden.
                    if(it->load >= newlabel.load && newlabel.dominates(*it, elementary, ngPath, farley)){
                        it = q[i].erase(it);
                        continue;
                    }
                    ++it;
                }
            }

            auto t7 = high_resolution_clock::now();
            time_unpropagated_dominance += t7-t6;

            if(!dominated){
                q[i].insert(newlabel);
            }

        }

        auto t9 = high_resolution_clock::now();
        total_time = duration_cast<seconds>(t9-t0).count();
        if(total_time > time_limit){
            additional_information[0] = 1;
            break;
        }

        // Check if the path to the last node has negative reduced cost
        // In case of farley: calculate the coefficent and check whether it is positive
        if(x.v == 0)
            continue;
        if(farley){
            double final_farley = x.farley_val + dual[num_nodes - 1];
            if(final_farley <= 0)
                continue;
            double final_cost = x.cost + edges[x.v][0];
            double candidate = final_cost / final_farley;
            if(candidate < best_farley_val || best_farley_val == 0)
                best_farley_val = candidate;
        } else{
            double newcost = x.finishing_cost(dual,farkas);
            if((newcost < -1e-6))
                ++num_paths;
            if((newcost < red_cost_bound)){
                if(new_vars.size() == max_vars){
                    new_vars[index_of_max_red_cost(dual,farkas,new_vars)] = &x;
                    red_cost_bound = maximal_cost(dual,farkas,new_vars);
                } else {
                    new_vars.push_back(&x);
                }
            }
        }
    }
    if(farley){
        *farley_res = best_farley_val;
    } else {
        for(unsigned i=0;i<new_vars.size();++i){
            new_vars[i]->write_path_to_output(result+i*max_path_len);
        }
    }
    auto end= high_resolution_clock::now();
    additional_information[1] = duration_cast<milliseconds>(end - t0).count();
    additional_information[2] = duration_cast<milliseconds>(time_propagated_dominance).count();
    additional_information[3] = duration_cast<milliseconds>(time_unpropagated_dominance).count();
    if(cyc2)
        cyc2_dominators.clear();
    return num_paths;

}
