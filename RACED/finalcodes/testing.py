import networkx as nx
import sys
import time
import utils
import math
import numpy as np
from random import seed
from pathlib import Path
import graph_creation as gc
from random import choice, seed
from queue import PriorityQueue
import utils
def creategraph():
    """
        Input:  'strategy' that is to be evaluated for k from 'k_start' to k=15

        ~> starts autopilot and simulator for given strategy and saves results
    """
    # folder:
    #file = './simulation_results/' + str(strategy)

    # open file and create multigraph model of the Lightning Network:
    # g = gc.parse_multi_di_graph('./lngraph_2020_05_01__10_00.json', exclude_disabled=False)
    # baseline_transactions(g)

    g = gc.parse_multi_di_graph('./lngraph_2020_05_01__10_00.json', exclude_disabled=True)  # EXCLUDE DISABLED EDGES!
    print("G has {} nodes and {} edges (={} active channels)".format(g.number_of_nodes(), g.number_of_edges(),
                                                                     g.number_of_edges() / 2))
    source = choice(list(g.nodes()))
    target = choice(list(set(g.nodes()) - {source}))
    print("Mohammed")
    print(source)
    print(target)
    print("mohammed")
    print("The higher the degree, the more central the node is.")
    print(nx.degree_centrality(g))
    if nx.has_path(g,source,target):
        print([p for p in nx.all_shortest_paths(g, source=source, target=target, weight="capacity", method='dijkstra')])
    else:
        print("Sorry No path")
    #print(nx.degree_centrality(g))
    #print(nx.voterank(g,10))
    #print(nx.maximum_flow_value(g, source, target, capacity='capacity'))

creategraph()