import matplotlib.pyplot as plt
import pandas as pd

def plot_all(dfs, time=False, smoothed=True):
    plt.figure(figsize=(7.3,4),dpi=200)
    ymax = max((df["upper_bound"][0] for df in dfs))
    ymin = min((df["upper_bound"].iloc[-1] for df in dfs))
    if time:
        xmax = max((df['total time'].sum() for df in dfs))
    else:
        xmax = max((df.shape[0] for df in dfs))

    for data in dfs:
        method = data['method'][0]
        if time:
            x_values = list(data['total time'].copy().cumsum())
        else:
            x_values = list(range(data.shape[0]))

        # data = pd.concat((data,data.iloc[-1:]))

        upper_bounds = data['upper_bound']
        plt.plot(x_values, upper_bounds, label="$Z_{" + method + "}$")

        if smoothed:
            lower_bounds = []
            best_lb = data['lower_bound'][0]
            for lb in data['lower_bound']:
                if lb > best_lb:
                    best_lb = lb
                lower_bounds.append(best_lb)
            method = data['method'][0]
        else:
            lower_bounds = data['lower_bound']
        plt.plot(x_values, lower_bounds, label=f'{method} LB')

        # optimal = [13332 for i in range(len(upper_bounds))]
        # plt.plot(x_values, optimal, "--", label="$Z_{CVRP}$")

        x_values.append(xmax)
        final_val = [upper_bounds.iloc[-1] for i in range(len(upper_bounds) + 1)]
        plt.plot(x_values,final_val, "--", label="$Z^*_{" + method + "}$")

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
    # plt.savefig("plots/X-n120-k6.zoomed-combined.pgf")
    plt.show()
