"""
    Procedures PLOTTING the simulation results
"""

# imports
import matplotlib.pyplot as plt
import matplotlib.colors as colors
# from matplotlib2tikz import save as tikz_save  -> renamed to tikzplotlib
from tikzplotlib import save as tikz_save
import numpy as np
import glob
import os


color = {'highest_degree': '#CCBB44', 'random': '#228833', 'k-center_gon': '#1965B0', 'bc': '#EE6677',
         'k-center_gon_deg': '#1965B0', 'k-median': '#4477AA', 'k-median_deg': '#66CCEE', 'greedy_mbi': '#AA3377',
         'bc_approx_10': '#EE6677'}

marker = {'highest_degree': 'd', 'random': '*', 'k-center_gon': '^', 'bc': '.', 'k-center_gon_deg': 'v',
          'k-median': '^', 'k-median_deg': '^', 'greedy_mbi': 'x', 'bc_approx_10': '.'}

name = {'highest_degree': 'Highest Degree', 'random': 'Random', 'bc': 'Betweenness', 'k-center_gon_deg': 'k-Center',
        'k-center_gon': 'k-Center', 'k-median': 'k-Median', 'k-median_deg': 'k-Median', 'greedy_mbi': 'MBI',
        'bc_approx_10': 'Betweenness'}

labels = ['MBI', 'Highest Degree', 'Random', 'Betweenness', 'k-Center', 'k-Median', 'Network Average']
# labels3 = ['Highest Degree', 'Random', 'Betweenness', 'k-Center', 'k-Median']
labels3 = ['Highest Degree', 'Random', 'Betweenness', 'k-Center', 'k-Median']
labels2 = ['Highest Degree', 'Random', 'k-Center']


def gini_coefficient(data):
    """
        calculates the gini coefficient of the data
        ~> ranges between 0 and 1 (the larger the coefficient is, the higher is the unevenness of the data)
    """
    g_c = 0
    for i in range(len(data)):
        g_c += sum([abs(data[i] - data[j]) for j in range(len(data))])
    g_c = g_c / (2 * len(data) * sum(data))
    return g_c


def plot_betweenness_centralization_old(strategies):
    fig, ax = plt.subplots()
    plt.xlabel('Nodes added')
    plt.ylabel('Betweenness Centralization')
    plt.title('Central Point Dominance and Gini Coefficient')
    before = centrality_dicts('./simulation_results_centralization/betweenness_centrality_before.txt')
    # plt.axis([0, 15, 0.45, 0.7])
    for strategy in strategies:
        print('Calculate Betweenness Centralization for: {}'.format(strategy))
        data = centrality_dicts('./simulation_results_centralization/{}/betweenness_centrality.txt'.format(strategy))
        data.insert(0, before[0])
        cpds, cpds_norm = [], []
        # cent_idcs = []
        gini = []
        x = []  # x axis -> number of nodes added
        for i in data:
            x.append(len(i) - 6689)  # 6689 = total number of Lightning nodes
            if strategy == 'highest_degree':
                top10nodes = [i[n] for n in [2331, 4104, 343, 5221, 1647, 5932, 916, 5435, 5718, 5380]]
                print("Top 10 nodes bc:", sum(top10nodes) / sum(i.values()))
            d = {j: i[j] * (len(i) - 1) * (len(i) - 2) for j in i}  # 'undo' normalization of the data
            cpd_norm = max(i.values())  # central point dominance (normalized)
            cpd = max(d.values())  # central point dominance ('absolute')
            cpds_norm.append(cpd_norm)
            cpds.append(cpd)

            # calculate betweenness centralization index:
            # centralization_idx = sum([cpd - j for j in d.values()])
            # centralization_idx = centralization_idx / (((len(i) - 1) ** 2) * (len(i) - 2) / 2)
            # cent_idcs.append(centralization_idx)

            # calculate gini coefficient:
            gini.append(gini_coefficient(list(i.values())))
        print("cpd", cpds_norm)
        # print("centralization", cent_idcs)
        print("gini:", gini, "\n")
        # ax.plot(x, cpds_norm, label='cpds_norm')  # , c[strategy], marker=m[strategy], label=strategy)
        # ax.plot(x, cpds, label='cpds')
        ax.plot(x, cpds_norm, color[strategy], marker='^', label='CPD ' + strategy)
        # ax.plot(x, cent_idcs, label='centralization index')
        ax.plot(x, gini, color[strategy], marker='.', label='Gini ' + strategy)

    ax.legend(loc='best', ncol=1)
    plt.savefig('./figures/betweenness_centralization.png')
    plt.show()


def plot_betweenness_centralization(strategies, x, ax=None, cpd=False):
    """
        plots (average) 'central point dominance' (if 'cpd') or 'gini coefficient' after 'x[i]' nodes were added
        using the given 'strategies'
    """
    print("Plotting Betweenness Centralization...")
    if not ax:
        fig, ax = plt.subplots()
    if cpd:
        ax.set(xlabel='Nodes Added', ylabel='Central Point Dominance')
    else:
        ax.set(xlabel='Nodes Added', ylabel='Gini Coefficient Betweenness')
    # plt.xlabel('Nodes Added')
    # plt.title('Central Point Dominance and Gini Coefficient (dashed)')
    # plt.ylabel('Gini Coefficient (Betweenness)')
    # plt.axis([0, 5100, 0, 1])
    avg, avg2 = [], []
    legend = []
    for strategy in strategies:
        print("Plotting Results for Strategy: ", strategy)
        cpds = [[] for j in range(30)]
        values = []
        print("len(data)=", end=" ")
        for i in range(1, 31):
            data = centrality_dicts('./centralization_results/{}_{}/betweenness_centrality.txt'.format(strategy, i))
            idx = 0
            print(len(data), end=" ")
            for d in data:
                cpds[i-1].append(max(d.values()))  # central point dominance (normalized)
                if i == 1:  # fill list 'values'
                    values.append({n: d[n] / 30 for n in d})  # calc mean by only adding 1/30th of the value
                elif idx == len(values):
                    break
                else:  # update list 'values' by calculating mean values
                    values[idx] = {n: values[idx][n] + (d[n] / 30) for n in d}  # calc mean by only adding 1/30th
                idx += 1
            #if strategy == 'highest_degree':
            #    break  # 'degree' always chooses the same nodes -> yields same results in all 30 iterations
        print("")
        # calculate mean CPD and Gini coefficient
        if strategy == 'bc_approx_10':
            if not avg2 and not avg:
                print("ERROR!!")
            else:  # un-do mistake that k=0 was not evaluated for 'bc_approx_10'
                avg = [avg[0]]
                if not cpd:
                    avg2 = [avg2[0]]
        else:
            avg, avg2 = [], []
        # avg = [np.mean([(cpds[i][j]) for i in range(30)]) for j in range(len(x)) if j < len(cpds[0])]
        avg.extend([np.mean([(cpds[i][j]) for i in range(30) if j < len(cpds[i])]) for j in range(len(cpds[0]))])  # calc mean
        print(avg)
        if not cpd:
            for val in values:
                avg2.append(gini_coefficient(list(val.values())))
            print(avg2)
        if cpd:
            leg = ax.plot(x[:len(avg)], avg, color[strategy], marker=marker[strategy], label=name[strategy])
        else:
            # ax.plot(x[:len(avg2)], avg2, color[strategy], marker=marker[strategy], linestyle='dashed')
            leg = ax.plot(x[:len(avg2)], avg2, color[strategy], marker=marker[strategy], label=name[strategy])
        legend.append(leg[0])
    ax.legend(loc='best', ncol=1)
    plt.grid(axis='y')
    # plt.savefig('./figures/betweenness.pdf')
    # plt.savefig('./figures/betweenness.pgf')
    # tikz_save('./figures/betweenness.tex')
    # plt.show()

    return legend


def centrality_dicts(file):
    with open(file, "r", encoding='utf-8') as f:
        res = []
        data = f.read()
        data = data.strip('}')
        data = data.strip('{')
        data = data.split('}{')
        for i in range(len(data)):
            d = data[i].split(',')
            d = {int(d[i].split(':')[0]): float(d[i].split(':')[1]) for i in range(len(d))}
            # d = {i: d[i]*(len(d)-1)*(len(d)-2) for i in d}  # 'undo' normalization of the data
            res.append(d)

    return res


def plot_degree(strategies, x, ax=None):
    """
        plots Gini coefficient of degree distribution
    """
    if not ax:
        fig, ax = plt.subplots()
    ax.set(xlabel='Nodes Added', ylabel='Gini Coefficient (Degree)')
    # plt.xlabel('Nodes Added')
    # plt.ylabel('Gini Coefficient (Degree)')
    avg = []
    for strategy in strategies:
        print("Plotting Results for Strategy: ", strategy)
        values = []
        print("len(data)=", end=" ")
        for i in range(1, 31):
            data = centrality_dicts('./centralization_results/{}_{}/degrees.txt'.format(strategy, i))
            idx = 0
            print(len(data), end=" ")
            for d in data:
                if i == 1:  # fill list 'values'
                    values.append({n: d[n] / 30 for n in d})  # calc mean by only adding 1/30th of the value
                elif idx == len(values):
                    continue
                else:  # update list 'values' by calculating mean values
                    values[idx] = {n: values[idx][n] + (d[n] / 30) for n in d}  # calc mean
                idx += 1
        print("")
        # calculate Gini coefficient:
        if strategy == 'bc_approx_10':
            if not avg:
                print("ERROR!!")
            else:
                avg = [avg[0]]  # un-do mistake that k=0 was not evaluated
        else:
            avg = []
        for val in values:
            avg.append(gini_coefficient(list(val.values())))
        print(avg)
        ax.plot(x[:len(avg)], avg, color[strategy], marker=marker[strategy], label=name[strategy])
    ax.legend(loc='best', ncol=1)
    plt.grid(axis='y')
    # plt.savefig('./figures/degrees.pdf')
    # plt.savefig('./figures/degrees.pgf')
    # tikz_save('./figures/degrees.tex')
    # plt.show()


def plot_clustering(strategies, x):
    """
        plots Gini coefficient of LCC
    """
    fig, ax = plt.subplots()
    plt.xlabel('Nodes Added')
    plt.ylabel('Gini Coefficient (LCC)')
    for strategy in strategies:
        print("Plotting Results for Strategy: ", strategy)
        values = []
        cpds = [[] for j in range(30)]
        print("len(data)=", end=" ")
        for i in range(1, 31):
            data = centrality_dicts('./centralization_results/{}_{}/clustering.txt'.format(strategy, i))
            idx = 0
            print(len(data), end=" ")
            for d in data:
                # cpds[i - 1].append(np.mean(list(d.values())))

                if i == 1:  # fill list 'values'
                    values.append({n: d[n] / 30 for n in d})  # calc mean by only adding 1/30th of the value
                elif idx == len(values):
                    continue
                else:  # update list 'values' by calculating mean values
                    values[idx] = {n: values[idx][n] + (d[n] / 30) for n in d}  # calc mean
                idx += 1

        print("")
        # calculate Gini coefficient:
        # avg = [np.mean([(cpds[i][j]) for i in range(30)]) for j in range(len(x)) if j < len(cpds[0])]
        avg = []
        for val in values:
            avg.append(0)
            # avg.append(gini_coefficient(list(val.values())))
        print(avg)
        ax.plot(x[:len(avg)], avg, color[strategy], marker=marker[strategy], label=name[strategy])
    ax.legend(loc='best', ncol=1)
    plt.grid(axis='y')
    # plt.savefig('./figures/degrees.pdf')
    # plt.savefig('./figures/degrees.pgf')
    # tikz_save('./figures/degrees.tex')
    plt.show()


def plot_success_rate_fees(feature, strategies, amt, x, ax=None):
    """
        plots 'success_rate'/ average 'fees' after 'x[i]' nodes were added using the given 'strategies'
    """
    if not ax:
        fig, ax = plt.subplots()
    # plt.xlabel('Nodes Added')

    if feature == 'success_rate':
        # plt.title('Mean Success Rate after adding x Nodes')
        ax.set(xlabel='Nodes Added', ylabel='Success Rate (in %)')
        # plt.ylabel('Mean Success Rate')
        # plt.axis([0, 5100, 0, 1])
    elif feature == 'fees':
        ax.set(xlabel='Nodes Added', ylabel='Fees (in %)')
        # plt.ylabel('Mean Fees')
        # plt.axis([0, 5100, 0, 0.12])
    else:
        print("No valid feature given!")
        return

    # retrieve stats before any node was added (x=0):
    # baseline = retrieve_data_all_nodes('./simulation_results/baseline/baseline_{}.txt'.format(amt))
    # avg_success_rate = sum([baseline[n][1] for n in baseline]) / sum([baseline[n][0] for n in baseline]) * 100  # in %
    # avg_fees = sum([baseline[n][2] for n in baseline]) / sum([baseline[n][1] for n in baseline]) / amt * 100  # in %
    avg_success_rate = []
    avg_fees = []
    for idx in range(1, 31):
        stats = retrieve_data_all_nodes('./simulation_results/baseline/baseline_{}_{}.txt'.format(amt, idx))
        # % of successful transactions (of all attempted transactions):
        overall_success_rate = sum([stats[n][1] for n in stats]) / sum([stats[n][0] for n in stats])
        # average fees paid per successful transaction (in % of transaction amount):
        average_fees = (sum([stats[n][2] for n in stats]) / sum([stats[n][1] for n in stats])) / amt * 100
        avg_success_rate.append(overall_success_rate)
        avg_fees.append(average_fees)
    avg_success_rate = np.mean(avg_success_rate) * 100  # in percent
    avg_fees = np.mean(avg_fees)
    legend = []
    for strategy in strategies:
        print(strategy)
        data = [[] for j in range(30)]
        for i in range(1, 31):
            with open('./centralization_results/{}_{}/stats.txt'.format(strategy, i), "r", encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    line = line.split('\t')
                    if feature == 'success_rate':
                        data[i - 1].append(float(line[1].split(':')[1]) * 100)  # in %
                    else:  # fees
                        data[i - 1].append((float(line[2].split(':')[1])) / amt * 100)  # in %
        avg = [np.mean([(data[i][j]) for i in range(30) if j < len(data[i])]) for j in range(len(data[0]))]  # calc mean
        if feature == 'success_rate':
            avg.insert(0, avg_success_rate)
        else:  # fees
            avg.insert(0, avg_fees)
        leg = ax.plot(x[:len(avg)], avg, color[strategy], marker=marker[strategy], label=name[strategy])
        legend.append(leg[0])
    if feature == 'success_rate':
        ax.legend(loc='best', ncol=1)
    plt.grid(axis='y')
    # plt.savefig('./figures/{}_centralization.pdf'.format(feature))
    # plt.savefig('./figures/{}_centralization.pgf'.format(feature))
    # tikz_save('./figures/{}_centralization.tex'.format(feature))
    # plt.show()

    return legend


def plot_diameter_transitivity(feature, strategies, x, ax=None):
    """
       plots 'diameter'/ 'transitivity' after 'x[i]' nodes were added using the given 'strategies'
    """
    if not ax:
        fig, ax = plt.subplots()
        # plt.xlabel('Nodes Added')
    ax.set(xlabel='Nodes Added', ylabel='Diameter')

    if feature == 'diameter':
        print("plotting mean diameter...")
        # plt.title('LN Diameter after adding x nodes')
        # plt.ylabel('Mean Diameter')
        # plt.axis([0, 5100, 0, 14])
    elif feature == 'transitivity':
        plt.ylabel('Mean Transitivity')
        # plt.axis([0, 5100, 0, 0.12])
    else:
        print("No valid feature given!")
        return
    legend = []
    for strategy in strategies:
        data = [[] for j in range(30)]
        for i in range(1, 31):
            with open('./centralization_results/{}_{}/{}.txt'.format(strategy, i, feature), "r", encoding='utf-8') as f:
                if strategy == 'bc_approx_10' and feature == 'diameter':
                    data[i - 1].append(13.)  # add initial diameter (13)
                if strategy == 'bc_approx_10' and feature == 'transitivity':
                    data[i - 1].append(0.11004759769667093)  # add initial transitivity
                for line in f:
                    data[i - 1].append(float(line))
        avg = [np.mean([(data[i][j]) for i in range(30) if j < len(data[i])]) for j in range(len(data[0]))]  # calc mean
        leg = ax.plot(x[:len(avg)], avg, color[strategy], marker=marker[strategy], label=name[strategy])
        legend.append(leg[0])
    ax.legend(loc='best', ncol=1)
    plt.grid(axis='y')
    plt.savefig('./figures/{}.pdf'.format(feature))
    # plt.savefig('./figures/{}.pgf'.format(feature))
    tikz_save('./figures/{}.tex'.format(feature))
    plt.show()

    return legend


def plot_centralization_all(strategies):
    """
        retrieves 'tx_amt', 'n' and 'interval' from results.txt -> creates x-axis
        calls procedures to plot all centralization metrics
    """
    for strategy in strategies:
        with open('./centralization_results/{}_1/results.txt'.format(strategy), "r", encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if 'tx_amt' in line:
                    amt = int(line[7:])
                elif 'n=' in line:
                    n = int(line[2:])
                elif 'interval' in line:
                    interval = int(line[9:])
                    x = [i * interval for i in range(int(n / interval) + 1)]
                    break
    plot_diameter_transitivity('transitivity', strategies, x)
    # plot_diameter_transitivity('diameter', strategies, x)
    # plot_success_rate_fees('success_rate', strategies, x)
    # plot_success_rate_fees('fees', strategies, amt, x)
    # plot_degree(strategies, x)
    # plot_clustering(strategies, x)
    # plot_betweenness_centralization(strategies, x)


def retrieve_data_all_nodes(file):
    """
        Input:  'file' with tx data (e.g. './simulation_results/baseline_transactions.txt')
        Output: statistics about all nodes that participated in transactions
                    - stats[node] = [tx_attempts, tx_sent, fees_paid, tx_routed, fees_earned]

        ~> reads tx data; allows to create baseline for tx success rate/ fees and to identify important routing nodes
    """
    with open(file, "r", encoding='utf-8') as f:
        stats = {}
        for line in f:
            if len(line) > 5 and line[5] == '[':  # node statistics
                line = line.strip()
                line = line.split('[')
                node = int(line[0])
                line = line[1].split(',')
                stats[node] = [int(line[0]), int(line[1]), float(line[2]), int(line[3]), float(line[4].strip(']'))]
    return stats


def retrieve_execution_times(file):
    """
        Input:  'file' with execution times  ('./simulation_results/execution_times/execution_times_all.txt')
                    - file has form: <strategy>:<exe_time_k1>,<exe_time_k2>, ..., <exe_time_k15>
        Output:  dict 'stats': stats[strategy][k] = exe_time for 'strategy' selecting 'k' nodes

        ~> reads autopilot strategies' execution times from file and returns them in a dict
    """
    with open(file, "r", encoding='utf-8') as f:
        stats = {}
        for line in f:
            line = line.strip()
            line = line.split(':')
            name = line[0]
            line = line[1].split(',')
            stats[name] = [float(line[i]) for i in range(len(line))]
    return stats


def retrieve_stats(strategies, amt=100, routing=False):
    stats = {}
    for strategy in strategies:
        stats_k = {}
        for k in range(1, 16):
            file = './simulation_results/{}/amt_{}/k_{}/{}_k{}_stats.txt'.format(strategy, amt, k, strategy, k)
            stats_k[k] = []
            successes, test = 0, 0
            with open(file, 'r', encoding='utf-8') as f:
                i = 0
                for line in f:
                    line = line.strip()  # remove '\n'
                    line = line.split('] ')
                    if not routing and line[0][:5] == '[1000':
                        stats_k[k].append((int(line[0].split(',')[1]), float(line[0].split(',')[2])))
                    elif routing and line[0][:5] != '[1000':
                        stats_k[k].append((int(line[0].split(',')[3]), float(line[0].split(',')[4])))
                        successes += int(line[1].split('/')[0])
                        test += int(line[1].split('/')[1])
                    """
                    if routing and i % 2 == 0:
                        stats_k[k].append((int(line[0].split(',')[3]), float(line[0].split(',')[4])))
                    if not routing and i % 2 == 1:  # -> doesn't work as stats are not sorted due to parallel execution
                        stats_k[k].append((int(line[0].split(',')[1]), float(line[0].split(',')[2])))
                    """
                    i += 1
                if i != 60:
                    print(file)
                if routing:
                    if test != 30000:
                        print("Oooops... that have not been 30000 transactions")
                    stats_k[k].append(successes)
        stats[strategy] = stats_k
    print("done..")
    return stats


def retrieve_data(strategies, amt=100, node=6801, routing=False):
    """
        Input:  list of 'strategies', tx 'amt', 'node' to evaluate,
                'fees' -> retrieve fee data instead of success rate
                'routing' -> retrieve statistics about how often the 'node' functioned as a routing node (-> profit?)
        Output: dict 'stats' => stats[x][y]: all results (from all iterations) for strategy x and k=y

        ~> opens all files, retrieves statistics about given 'node' and stores them in a dict
    """
    stats = {}
    for strategy in strategies:
        print("reading data from strategy: {}".format(strategy))
        if strategy == 'greedy_mbi_990' or strategy == 'greedy_mbi_2000' or strategy == 'greedy_mbi_5000' or \
                strategy == 'greedy_mbi_10000':
            amt_temp = '100_fees_' + strategy.split('_')[2]
            folder = './simulation_results/greedy_mbi/amt_{}/'.format(amt_temp)
        else:
            folder = './simulation_results/{}/amt_{}/'.format(strategy, amt)
        stats_k = {}
        for k in range(1, 16):
            folder_k = folder + 'k_{}/'.format(k)
            results = []
            successes = 0
            test = 0
            for file in glob.glob(os.path.join(folder_k, '*.txt')):
                with open(file, "r", encoding='utf-8') as f:
                    part_1 = True  # indicates if the first 1000 tx (random src) are still searched
                    res_routing = None
                    for line in f:
                        line = line.strip()  # remove '\n' at the end of the line
                        #if line[:13] == 'seed value 2:' and line[-11:] == '(fixed src)':
                        #    part_1 = False  # start searching second 1000 tx (fixed src)
                        if line[:20] == '--------------------':
                            part_1 = False
                        if routing:
                            if part_1 and len(line) > 5:
                                if line[5] == '[':
                                    success = line.split(",")
                                    successes += int(success[1])
                                    test += int(success[0][len(success[0])-1])
                                if line[:len(str(node)) + 2] == str(node) + ' [':
                                    # 'node' routed tx or was randomly selected as src
                                    line = line.strip("]")  # remove ']' at the end of the line
                                    d = line.split(",")
                                    res = (float(d[3]), float(d[4]))
                                    if res != (0, 0) and float(d[0].split('[')[1]) < 1000:
                                        results.append(res)
                        else:
                            # if line[:len(str(node)) + 7] == str(node) + ' [1000,':  # found line containing node's stats
                            if line[:len(str(node)) + 2] == str(node) + ' [':  # found line containing node's stats
                                d = line.split(",")
                                res = (float(d[1]), float(d[2]))
                                if float(d[0].split('[')[1]) < 1000:  # 'node' routed tx or was randomly selected as src
                                    res_routing = res
                                else:
                                    if res_routing and strategy != 'highest_degree':
                                        res = (res[0] - res_routing[0], res[1] - res_routing[1])
                                    results.append(res)
            if not routing:
                if len(results) == 0:
                    print("No data for strategy {} with k={}!".format(strategy, k))
                    # results = [0] * 30
                elif len(results) != 30:
                    print("This have not been exactly 30 files (k={})!!!".format(k))
            else:
                results.append(successes)
            stats_k[k] = results
            if routing and test != 30000:
                print("Oooops... that have not been 30000 transactions")
        stats[strategy] = stats_k

    return stats


def retrieve_failure_type(strategies, amt):
    """
        iterates through all 1000 random source transactions and stores how many transactions were successful and how
        many failed (due to temporary channel failure or non-existing route)
        ~> returns 'stats' (per strategy and k) and successes_all, tcf_all, nsfr_all (sum over all txs)
    """
    stats = {}
    successes_all, tcf_all, nsfr_all = 0, 0, 0
    for strategy in strategies:
        print("reading data from strategy: {}".format(strategy))
        stats_k = []
        for k in range(1, 16):
            successes, tcf, nsfr = 0, 0, 0
            for i in range(1, 31):
                file = './simulation_results/{}/amt_{}/k_{}/{}_k{}_{}.txt'.format(strategy, amt, k, strategy, k, i)
                with open(file, "r", encoding='utf-8') as f:
                    idx = 0
                    for line in f:
                        if idx < 3:
                            idx += 1
                            continue  # no useful information in the first three lines
                        if idx > 1002:
                            break  # first 1000 txs finished
                        if ('S (Route' in line) or ('S (direct' in line):
                            successes += 1
                            successes_all += 1
                        else:
                            if 'temporary channel failure' in line:
                                tcf += 1
                                tcf_all += 1
                            else:
                                nsfr += 1
                                nsfr_all += 1
                        # print(idx-2, line[23])
                        idx += 1
            if (successes + tcf + nsfr) != 30000:
                print("oops. that have not been 30000 transactions!")
            stats_k.append((successes, tcf, nsfr))
        stats[strategy] = stats_k

    return stats, (successes_all, tcf_all, nsfr_all)


def network_avg_success_rate(strategies, ax=None):
    """
        retrieves average success rate from all strategies' random source - random target transactions and plots them
        ~> uses boxplots and bar plot
    """
    data = []
    for amt in [100, 10000, 1000000]:
        # stats = retrieve_stats(strategies, amt=amt, routing=True)
        stats, stats_compact = retrieve_failure_type(strategies, amt)
        data.append(stats_compact)
        # d = []
        # for strategy in strategies:
            # for i in range(1, 16):
                # d.append(stats[strategy][i][30] / 30000)
        #data.append(d)
        # plt.boxplot(d)
        # plt.savefig('./figures/boxplot_{}.pdf'.format(amt))
        # plt.show()
    # plt.boxplot(data)
    # plt.savefig('./figures/boxplot_all.pdf'.format())
    # plt.show()
    # data_mean = [np.mean(i) for i in data]
    # data_err = [np.std(i) for i in data]

    total_tx = sum(list(data[0]))
    y1 = [data[i][0] / total_tx for i in range(3)]
    y2 = [data[i][1] / total_tx for i in range(3)]
    y3 = [data[i][2] / total_tx for i in range(3)]
    x = ['100', '10000', '1000000']

    if not ax:
        fig, ax = plt.subplots()
    # plt.bar(x, y1, label='y1')
    # stack y2 on top of y1.
    # plt.bar(x, y2, bottom=y1, label='y2')
    #ax.bar(x, y1, alpha=0.5, capsize=10)
    #ax.bar(x, y2, bottom=y1, alpha=0.5, capsize=10)
    #ax.bar(x, y3, bottom=[y1[i]+y2[i] for i in range(3)], alpha=0.5, capsize=10)
    ax.barh(x, y1, alpha=0.5, capsize=10, color='#228833', label='Success')
    ax.barh(x, y2, left=y1, alpha=0.5, capsize=10, color='#EE6677', label='Temporary Channel Failure')
    ax.barh(x, y3, left=[y1[i] + y2[i] for i in range(3)], alpha=0.5, capsize=10, color='#AA3377', label='No Route')
    ax.set_ylabel('Transaction Amount (in Satoshi)')
    plt.xticks([])
    # ax.set_xlabel('Success Rate (in %)')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    # ax.yaxis.grid(True)
    plt.tight_layout()
    ax.legend(ncol=3, loc=8, frameon=False, borderaxespad=-2.)
    # plt.savefig('./figures/barplot.pdf')
    # tikz_save('./figures/barplot.tex')
    # plt.show()


def boxplot(data, title, fees=False):
    """
        creates a boxplot for the given 'data'
    """
    if fees:
        plt.ylabel('Fees (in % of transaction amount)')
        plt.title('Fees paid on average per successful transaction ({})'.format(title))
    else:
        plt.title('Transaction Success Rate using Strategy: {}'.format(title))
        plt.ylabel('Success Rate')
    plt.xlabel('k')

    # plt.axis([0, 16, 0.5, 0.75])
    d = []
    for i in data.values():
        if fees:
            f = [(j[1] / j[0]) for j in i]
            d.append(f)
        else:
            d.append([j[0] / 1000 for j in i])
    plt.boxplot(d)
    # plt.savefig('../simulation_results/figures/boxplot_fees_{}.png'.format(title))
    plt.show()


def plot_side_by_side(strategies, tx_amt, baseline, plots):
    """
        puts two plots into one figure/file with shared legend
        possible combinations:
            - plots = 'fees_routing' -> plots average fees and routing success
            - plots = 'success_rate_bars' -> plots success rate for strategies and network average for 'tx_amt' and bars
            - plots = 'bc_gini_diameter' -> plots Gini Coefficient of BC and Diameter (for long-term eval)
            - plots = 'success_rate_fees' -> plots average success rate and fees (for long-term eval)
            - plots = 'degree_gini_diameter' -> plots Gini Coefficient of Degrees and Diameter (for long-term eval)
            - plots = 'bc_gini_cpd' -> plots Gini Coefficient of BC and Central Point Dominance (for long-term eval)
            - plots = 'success_rate_all' -> plots success rate for strategies and network average for all tx_amts
                -> needs 'baseline' as list of three baseline values
    """
    x = []
    for strategy in strategies:
        with open('./centralization_results/{}_1/results.txt'.format(strategy), "r", encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if 'tx_amt' in line:
                    amt = int(line[7:])
                elif 'n=' in line:
                    n = int(line[2:])
                elif 'interval' in line:
                    interval = int(line[9:])
                    x = [i * interval for i in range(int(n / interval) + 1)]
                    break

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
    # fig, (ax1, ax2) = plt.subplots(1, 2)
    if plots == 'fees_routing':
        d1 = retrieve_stats(strategies, amt=amount, routing=False)
        a = plot(d1, tx_amt, fees=True, baseline=baseline, ax=ax1)  # plot fees
        ax1.yaxis.set_major_formatter(plt.ScalarFormatter(useOffset=False))
        ax1.ticklabel_format(style='sci', axis='y', scilimits=(0, 0))
        # ax1.set_yticks([0., 0.005, 0.01, 0.015, 0.02, 0.025])
        d2 = retrieve_stats(strategies, amt=tx_amt, routing=True)
        b = plot(d2, tx_amt, fees=False, routing=True, ax=ax2)
        fig.legend(a + b, labels=labels, loc=9, ncol=7, mode='expand', frameon=False, borderaxespad=-0.4)
    elif plots == 'success_rate_bars':
        d1 = retrieve_stats(strategies, amt=amount, routing=False)
        plot(d1, tx_amt, fees=False, baseline=baseline, ax=ax1)
        network_avg_success_rate(strategies, ax=ax2)
        # fig.legend(a, labels=labels, loc='upper left', ncol=4, frameon=False, borderaxespad=-0.2)
    elif plots == 'success_rate_all':
        fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(10, 4))
        d1 = retrieve_stats(strategies, amt=100, routing=False)
        plot(d1, tx_amt=100, fees=False, baseline=baseline[0], ax=ax1)
        d2 = retrieve_stats(strategies, amt=10000, routing=False)
        plot(d2, tx_amt=10000, fees=False, baseline=baseline[1], ax=ax2)
        d3 = retrieve_stats(strategies, amt=1000000, routing=False)
        plot(d3, tx_amt=1000000, fees=False, baseline=baseline[2], ax=ax3)
    elif plots == 'bc_gini_diameter':
        a = plot_betweenness_centralization(strategies, x, ax=ax1)
        b = plot_diameter_transitivity('diameter', strategies, x, ax=ax2)
        # fig.legend(a + b, labels=labels, loc=9, ncol=5, mode='expand', frameon=False, borderaxespad=-0.2)
    elif plots == 'success_rate_fees':
        a = plot_success_rate_fees('success_rate', strategies, tx_amt, x, ax=ax1)
        b = plot_success_rate_fees('fees', strategies, tx_amt, x, ax=ax2)
        # fig.legend(a + b, labels=labels3, loc=9, ncol=6, mode='expand', frameon=False, borderaxespad=-0.2)
    elif plots == 'degree_gini_diameter':
        a = plot_degree(strategies, x, ax=ax1)
        b = plot_diameter_transitivity('diameter', strategies, x, ax=ax2)
        # fig.legend(a + b, labels=labels, loc=9, ncol=5, mode='expand', frameon=False, borderaxespad=-0.2)
    elif plots == 'bc_gini_cpd':
        a = plot_betweenness_centralization(strategies, x, ax=ax1, cpd=False)
        b = plot_betweenness_centralization(strategies, x, ax=ax2, cpd=True)
    else:
        print("ERROR! Unknown 'plots' name")
        return
    # ax2.spines['left'].set_color('red')
    plt.subplots_adjust(wspace=0.9)
    ax1.grid(axis='y')
    ax2.grid(axis='y')
    plt.tight_layout()
    tikz_save('./figures/{}.tex'.format(plots))
    plt.savefig('./figures/{}.pdf'.format(plots))
    plt.show()
    print("test")


def fill_y(data, strategy, tx_amt, fees, routing, times):
    """
        helper function for 'plot()' filling the 'y' vector
    """
    y = []
    if times:
        y = data[strategy]
    else:
        for j in data[strategy].values():
            if not j:
                if routing:
                    y.append(0)  # no tx routed
                else:
                    y.append(np.NaN)  # no values
            else:
                res = []
                if routing:  # -> j[len(j)-1] stores only one value (number of successful tx)
                    if fees:
                        res = sum([i[1] for i in j[:-1]])
                    else:
                        res = sum([i[0] for i in j[:-1]]) / j[len(j) - 1] * 100  # in % of all 30000 txs
                        print("{} routed {} ({}) of {} successful transaction".format(strategy,
                                                                                       sum([i[0] for i in j[:-1]]), res,
                                                                                       j[len(j) - 1]))
                else:
                    if fees:
                        res = np.mean([(i[1] / i[0]) for i in j if i[0] != 0]) / tx_amt * 100  # fees in % (of tx_amt)
                    else:
                        res = [i[0] / 1000 for i in j]
                        print("{}: min={}, max={}".format(strategy, np.min(res), np.max(res)))
                        res = np.mean(res)
                        # res = np.mean([i[0] / 1000 for i in j])  # divide by number of transactions (=1000)
                y.append(res)
                # print("{}: min={}, max={}".format(strategy, np.min(res), np.max(res)))

    return y


def plot(data, tx_amt, fees=False, routing=False, times=False, baseline=None, ax=None):
    """
        plots the data as a line graph
    """
    filename = ""
    if ax is None:
        fig, ax = plt.subplots()
        # plt.xlabel('k')
    if times:
        ax.set(xlabel='k', ylabel='Seconds')
        # plt.ylabel('Seconds')
        plt.title('Execution time (in Seconds)')
        filename += "exe_time"
    elif fees:
        if routing:
            ax.set(xlabel='k', ylabel='Fees (in Satoshis)')
            # plt.ylabel('Fees (in satoshis)')
            # plt.title('Fees earned by successful routing')
            filename += "routing_fees"
        else:
            ax.set(xlabel='k', ylabel='Fees')
            # plt.ylabel('Fees')
            # plt.title('Fees paid on average per successful transaction')
            filename += "fees"
            # plt.axis([-1, 15, 0, 0.0004])
    else:
        if routing:
            ax.set(xlabel='k', ylabel='Routed Transactions')
            # plt.ylabel('Routed Transactions (in %)')
            # plt.title('Proportion of all successfully routed transactions')
            filename += "routing_success"
        else:
            ax.set(xlabel='k', ylabel='Success Rate')
            # plt.ylabel('Success Rate')
            # plt.title('Transaction Success Rate')
            filename += "success_rate"
    # plt.axis([0, 15, 0, 12])
    x = [str(i) for i in range(1, 16)]
    idx = 0
    legend = []
    for strategy in data:
        y = fill_y(data, strategy, tx_amt, fees, routing, times)
        # y = [np.mean(j) / 1000 for j in data[strategy].values()]
        leg = ax.plot(x, y, color[strategy], marker=marker[strategy], label=name[strategy])
        legend.append(leg[0])
        idx += 1
    if baseline:
        # ax.plot(x, [baseline] * 15, color='black', linestyle='dashed', label='Network Average')
        ax.axhline(baseline, color='gray', linestyle='--', label='Network Average')
        # legend.append(leg[0])
    plt.grid(axis='y')
    ax.legend(loc='best', ncol=1)
    # plt.savefig('./figures/{}_{}.pdf'.format(filename, tx_amt))
    #plt.savefig('./figures/{}_{}.pgf'.format(filename, tx_amt))
    # tikz_save('./figures/{}_{}.tex'.format(filename, tx_amt))
    # plt.show()

    return legend


if __name__ == '__main__':

    amounts = [100, 10000, 1000000]
    amount = 100
    # amount = 10000
    # amount = 1000000

    # strategies:
    s = ['highest_degree', 'random', 'k-center_gon', 'bc', 'k-center_gon_deg', 'k-median', 'k-median_deg', 'greedy_mbi']
    # s = ['highest_degree', 'random', 'k-center_gon', 'bc', 'k-center_gon_deg', 'k-median', 'k-median_deg']
    s = ['greedy_mbi', 'highest_degree', 'random', 'bc', 'k-center_gon_deg', 'k-median_deg']
    # s = ['highest_degree', 'random', 'bc', 'k-center_gon_deg', 'k-median_deg']
    s = ['highest_degree', 'random', 'bc_approx_10', 'k-center_gon_deg', 'k-median_deg']
    # s = ['highest_degree', 'random', 'bc_approx_10', 'bc', 'k-center_gon_deg', 'k-median_deg']

    # network_avg_success_rate(s)
    # statistics = retrieve_data(s, amt=amount, routing=False)
    # statistics = retrieve_stats(s, amt=amount, routing=False)
    # statistics = retrieve_stats(s, amt=amount, routing=True)
    plot_centralization_all(s)

    # calculate the network's average success rate and fees (for all tx_amts):
    baseline_success = []
    baseline_fees = []
    """for a in amounts:
        for idx in range(1, 31):
            stats = retrieve_data_all_nodes('./simulation_results/baseline/baseline_{}_{}.txt'.format(a, idx))
            # % of successful transactions (of all attempted transactions):
            overall_success_rate = sum([stats[n][1] for n in stats]) / sum([stats[n][0] for n in stats])
            # average fees paid per successful transaction (in % of transaction amount):
            average_fees = (sum([stats[n][2] for n in stats]) / sum([stats[n][1] for n in stats])) / a * 100
            baseline_success.append(overall_success_rate)
            baseline_fees.append(average_fees)"""

    # plot_side_by_side(s, amount, average_fees, 'fees_routing')
    # plot_side_by_side(s, amount, overall_success_rate, 'success_rate_bars')
    # plot_side_by_side(s, amount, None, 'bc_gini_diameter')
    # plot_side_by_side(s, amount, None, 'success_rate_fees')
    # plot_side_by_side(s, amount, None, 'degree_gini_diameter')
    # plot_side_by_side(s, amount, baseline_success, 'success_rate_all')
    # plot_side_by_side(s, amount, None, 'bc_gini_cpd')

    # time_stats = retrieve_execution_times()
    # plot(time_stats, amount, times=True)

    # statistics = retrieve_data(s, amt=amount, routing=False)
    # plot(statistics, amount, fees=False, routing=False, baseline=overall_success_rate)
    # plot(statistics, amount, fees=True, routing=False, baseline=average_fees)
    # plot(statistics, amount, fees=False, routing=True)
    # plot(statistics, amount, fees=True, routing=True)
    # boxplot(statistics[s[0]], s[0], fees=False)

