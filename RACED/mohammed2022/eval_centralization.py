"""
    Procedure starting Network Simulator that adds many nodes using specified autopilot strategy and evaluates the
    effects on the centralization of the network
"""

import sys
import time
import graph_creation as gc
import networkx as nx
import network_simulator as ns
from pathlib import Path


def start_eval(strategy='random', tx_amt=100, interval=1000, n=10000, cpus=None, seed_val=23):
    """
        Input:  'strategy' used by the autopilot to connect 'n' new nodes to the network
            ~>  starts simulator and adds nodes one after the other; evaluates centralization of the network
                every 'interval' steps (including 1000 transactions with 'tx_amt' satoshis)
    """
    # folder:
    file = './centralization_results/' + str(strategy) + '_' + str(s) + '/'
    Path(file).mkdir(parents=True, exist_ok=True)

    # open file and create multigraph model of the Lightning Network:
    # g = gc.parse_multi_di_graph('./lngraph_2020_05_01__10_00.json', exclude_disabled=False)
    g = gc.parse_multi_di_graph('./lngraph_2020_05_01__10_00.json', exclude_disabled=True)  # EXCLUDE DISABLED!!!
    print("G has {} nodes and {} edges (={} active channels)".format(g.number_of_nodes(), g.number_of_edges(),
                                                                     g.number_of_edges() / 2))

    # reduce graph to largest component:
    max_comp = max(nx.strongly_connected_components(g), key=len)
    g = g.subgraph(max_comp).copy()
    print("Largest connected component has {} nodes and {} edges".format(g.number_of_nodes(), g.number_of_edges()))

    start = time.perf_counter()
    ns.start_simulator(g, tx_amt, strategy, n, file, None, i=interval, c=cpus, s=seed_val)
    print("Simulation took {} seconds".format(time.perf_counter()-start))


if __name__ == '__main__':
    list_of_strategies = ['random', 'highest_degree', 'k-center_gon_deg', 'k-center_gon', 'k-median', 'k-median_deg',
                          'k-median_par', 'k-median_par_deg', 'bc', 'bc_approx_10', 'bc_approx_50', 'greedy_mbi',
                          'greedy_mbi_par']
    if len(sys.argv) > 1:
        m = str(sys.argv[1])
        if m in list_of_strategies:
            if len(sys.argv) > 2:
                amt = int(sys.argv[2])
                if amt in [100, 10000, 1000000]:
                    if len(sys.argv) > 3:
                        i = int(sys.argv[3])
                        if len(sys.argv) > 4:
                            num = int(sys.argv[4])
                            if len(sys.argv) > 5:
                                c = int(sys.argv[5])
                                if len(sys.argv) > 6:
                                    s = int(sys.argv[6])
                                    start_eval(strategy=m, tx_amt=amt, interval=i, n=num, cpus=c, seed_val=s)
                                else:
                                    start_eval(strategy=m, tx_amt=amt, interval=i, n=num, cpus=c)
                            else:
                                start_eval(strategy=m, tx_amt=amt, interval=i, n=num)
                        else:
                            start_eval(strategy=m, tx_amt=amt, interval=i)
                    else:
                        start_eval(strategy=m, tx_amt=amt)
                else:
                    print("Warning, tx_amt is not in [100, 10000, 1000000]!")
            else:
                start_eval(strategy=m)
        else:
            print("No valid strategy given!")
    else:
        print("Parameters: <metric> <tx_amt> <eval_interval> <nodes_to_add> <cpus> <seed>")
        print("Defaults (if no parameters are given): strategy='random', tx_amt=100, interval=1000, n=10000")
        start_eval()
