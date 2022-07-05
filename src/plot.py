import matplotlib.pyplot as plt
import pandas as pd
import src.parse as parse
import os

def plot_all(dfs, time=False, smoothed=True, save=False, ng20=True, pgf=False):
    dfs = [df.copy() for df in dfs]
    plt.figure(figsize=(7.3,4),dpi=400)
    color_map = {"ng20":"b","ng8":"r","cyc2":"c","SPPRC":"k"}

    ymax = max((df["upper_bound"][0] for df in dfs))
    ymin = min((df["upper_bound"].iloc[-1] for df in dfs))

    for df in dfs:
        df['total time'] = df['total time'].cumsum()
    if time:
        xmax = max((df['total time'].iloc[-1] for df in dfs if ng20 or df['method'].iloc[-1] != 'ng20'))
    else:
        xmax = max((df[df['method'].isin(color_map.keys())].shape[0] for df in dfs if ng20 or df['method'].iloc[-1] != 'ng20'))

    for data in dfs:
        method = data['method'].iloc[-1]
        if method == "ng20" and not ng20:
            continue
        init_val = data['upper_bound'][0]
        data = data[data['method'] == method]
        if time:
            x_values = list(data['total time'])
        else:
            x_values = list(range(data.shape[0]))

        if smoothed:
            lower_bounds = []
            best_lb = data['lower_bound'].iloc[0]
            for lb in data['lower_bound']:
                if lb > best_lb:
                    best_lb = lb
                lower_bounds.append(best_lb)
        else:
            lower_bounds = list(data['lower_bound'])
        plt.plot(x_values, lower_bounds, color_map[method], label=f'{method} LB')

        upper_bounds = list(data['upper_bound'])
        if time:
            x_values.insert(0,0)
            upper_bounds.insert(0,init_val)
        plt.plot(x_values, upper_bounds, color_map[method], label="$Z_{" + method + "}$")

        x_values.append(xmax)
        final_val = [upper_bounds[-1] for i in range(len(upper_bounds) + 1)]
        plt.plot(x_values,final_val, "--" + color_map[method], label="$Z^*_{" + method + "}$")

        plt.title(save.split("/")[-1])
        # if pricer.data['farley']:
        #     farley_bounds = pricer.data['farley_bound']
        #     plt.plot(x_values, farley_bounds, label="Farley Bound")

        # T = nx.minimum_spanning_tree(G)
        # K = G.graph['min_trucks']
        # lowest_remaining_edge_weights = [weight for u,v,weight in G.edges().data('weight') if not T.has_edge(u,v)]
        # mst = T.size(weight='weight') + sum(sorted(lowest_remaining_edge_weights)[:K])
        # mst = [mst for i in range(len(upper_bounds))]
        # plt.plot(x_values, mst, "--", label="MST Bound")

    plt.ylim((ymin*0.99,ymax*1.01))

    plt.legend(loc='lower right')
    if time:
        plt.xlabel("Pricing time in s")
    else:
        plt.xlabel("Pricing Iterations")
    plt.ylabel("Solution value")
    save_string = save
    if time:
        save_string += ".time"
    else:
        save_string += ".iterations"
    if not ng20:
        save_string += "-no_ng20"
    if not pgf:
        save_string += ".png"
    else:
        save_string += ".pgf"
    if save is not False:
        plt.savefig(save_string)
    plt.close()

def automatic_plotting(dir):
    files = [file.rstrip(".vrp") for file in os.listdir("Instances/Uchoa") if (not file.endswith("sol"))]

    methods = ["SPPRC","cyc2","ng8","ng20"]

    for file in files:
        print(file)
        data = []
        for log in ( log for log in os.listdir("output_uchoa") if log.startswith(file)):
            log = f"output_uchoa/{log}"
            for method in methods:
                if log.endswith(f"{method}.log") and parse.log_finished(log):
                    data.append(parse.parse_output(log))
        if len(data) > 0:
            plot_all(data,time=True,smoothed=True, save=f"{dir}/{file}")
            plot_all(data,time=True,smoothed=True, save=f"{dir}/{file}", ng20=False)
            plot_all(data,time=False,smoothed=True, save=f"{dir}/{file}")
