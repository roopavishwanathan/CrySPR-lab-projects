"""
    Collection of procedures to CREATE different GRAPHS:
    - parse Lightning snapshot and create MultiDiGraph
    - create fee graph
"""

import json
import networkx as nx
import numpy as np
import math


def parse_json(file='./lngraph_2020_05_01__10_00.json'):
    """
        Input: .json file with snapshot of Lightning Network
        Output: set of edges (Lightning channels)
                set of nodes

        ~> opens file, reads in data, closes file and stores edges & nodes
    """
    print("opening", file, "...")
    with open(file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    edges = data['edges']
    nodes = data['nodes']

    return edges, nodes


def add_nodes(nodes, g):
    """
        Input:  node list 'nodes', graph 'g' to which nodes should be added
        Output: dict 'node_dict' mapping node id to its public key

        ~> adds nodes, stores public key and aliases
    """
    node_dict = {}
    for n in range(len(nodes)):
        g.add_node(n, key=nodes[n]['pub_key'], alias=nodes[n]['alias'])
        node_dict[nodes[n]['pub_key']] = n
    #print(g.nodes)
    return node_dict


def parse_multi_di_graph(file=None, exclude_disabled=False):
    """
        Input:  .json file to be read
                if 'disabled' channels should be excluded
                    - assumption:   if at least one node's policy says that the channel is disabled, it is assumed that
                                    it is disabled completely and not added to the graph (if exclude_disabled == True)
                                    or both edges are set as 'disabled' (if exclude_disabled == False)
        Output: MultiDiGraph 'g' representing the Lightning Network:
                - Node attributes (g.nodes[n]): public_key and alias of the Lightning node
                - Two directed edges for every Lightning channel (total capacity = sum of both edges' capacities)
                - Edge attributes (g[u][v]): u's shares of the channel balance and its policies (fees...)

        ~> creates a MultiDiGraph from Lightning snapshot
    """
    if file is None:
        edges, nodes = parse_json()
    else:
        edges, nodes = parse_json(file)
    #print(nodes)
    g = nx.MultiDiGraph()  # create directed multi graph
    node_dict = add_nodes(nodes, g)
    print("the number of node : "+ str(len(nodes)))
    print(node_dict)
    total_coins = 0
    #print(edges)
    # add two directed edges for every channel (that is not 'disabled'):
    for e in range(len(edges)):
        inactive = False
        if ((edges[e]['node1_policy'] is not None) and bool(edges[e]['node1_policy']['disabled'])) \
                or ((edges[e]['node2_policy'] is not None) and bool(edges[e]['node2_policy']['disabled'])):
            inactive = True  # both edges are going to be set as 'disabled'
            if exclude_disabled:
                # channel cannot be used in either direction -> no edge is going to be added
                continue
        total_coins += int(edges[e]['capacity'])
        #print(total_coins)
        # set capacity for node1 and node2:
        c1 = int(edges[e]['capacity']) / 2  # both parties have same share of the channel balance
        c2 = int(edges[e]['capacity']) / 2  # both parties have same share of the channel balance
        # c1 = randint(0, int(edges[e]['capacity']))  # node1's share of the channel balance
        # c2 = int(edges[e]['capacity']) - c1  # node2's share of the channel balance
        if edges[e]['node1_policy'] is not None:
            g.add_edge(node_dict[edges[e]['node1_pub']], node_dict[edges[e]['node2_pub']], capacity=c1,
                       base_fee=float(edges[e]['node1_policy']['fee_base_msat']),
                       fee_rate=float(edges[e]['node1_policy']['fee_rate_milli_msat']),
                       delay=edges[e]['node1_policy']['time_lock_delta'],
                       disabled=edges[e]['node1_policy']['disabled'])
        else:
            g.add_edge(node_dict[edges[e]['node1_pub']], node_dict[edges[e]['node2_pub']], capacity=c1,
                       base_fee=1000, fee_rate=1, delay=144, disabled=False)  # default values if policy is unknown
        if edges[e]['node2_policy'] is not None:
            g.add_edge(node_dict[edges[e]['node2_pub']], node_dict[edges[e]['node1_pub']], capacity=c2,
                       base_fee=float(edges[e]['node2_policy']['fee_base_msat']),
                       fee_rate=float(edges[e]['node2_policy']['fee_rate_milli_msat']),
                       delay=edges[e]['node2_policy']['time_lock_delta'],
                       disabled=edges[e]['node2_policy']['disabled'])
        else:
            g.add_edge(node_dict[edges[e]['node2_pub']], node_dict[edges[e]['node1_pub']], capacity=c2,
                       base_fee=1000, fee_rate=1, delay=144, disabled=False)  # default values if policy is unknown
    #print(g.edges)
    return g


def directed_fee_graph(g, tx_amount, exclude_edges=True, multi_graph=True):
    """
        Input:  directed (multi-)graph 'g', transaction amount (in satoshi),
                if insufficiently funded edges should be excluded and if the fee graph should be a multigraph
        Output: directed graph with edge weights representing the fees (in msat) that have to be paid to use this edge
                - if exclude_edges == True, the output graph is not necessarily connected

        ~> Fee calculation: fee = base fee + transaction amount * proportional fee
            (first transform to same unit)
    """
    fee_graph = nx.DiGraph(g)  # copy graph (especially all nodes with attributes)
    if multi_graph:
        fee_graph = nx.MultiDiGraph(g)

    fee_graph.remove_edges_from(g.edges())  # remove all edges

    g_temp = g
    if not g.is_multigraph():
        g_temp = nx.MultiDiGraph(g)

    for (n1, n2) in g_temp.edges():
        if fee_graph.has_edge(n1, n2):
            # all edges between n1 and n2 have already been processed
            continue
        min_fee = math.inf
        for i in g_temp[n1][n2]:  # loop through all edges between n1 and n2
            if exclude_edges and (g_temp[n1][n2][i]['capacity'] + g_temp[n2][n1][i]['capacity'] < tx_amount):
                # exclude channels (capacities of both edges belonging to it) with insufficient capacity
                continue
            # calculate tx fee in (sat):
            f = tx_amount * (int(g_temp[n1][n2][i]['fee_rate']) / 10**6) + (int(g_temp[n1][n2][i]['base_fee']) / 1000)
            if f == 0:
                f = np.finfo(np.float32).eps  # avoid edges of weight 0 -> might lead to inf. number of shortest paths
            f *= 1000  # sat -> msat
            if f < min_fee:
                min_fee = f
            if multi_graph:
                fee_graph.add_edge(n1, n2, fee=f)  # add fee as edge weight
        if not multi_graph:
            if not fee_graph.has_edge(n1, n2) and min_fee < math.inf:
                fee_graph.add_edge(n1, n2, fee=min_fee)

    return fee_graph


def multi_to_largest_di_graph(g):
    """
        Input:  MultiDiGraph 'g'
        Output: DiGraph 'di_g'

        ~> chooses channel with largest capacity if multiple channels between two nodes exist
            - choose pair of edges (=channel) that has highest summed capacity, not individual capacities
            - however: the chosen edge might have 'worse' channel settings than others
    """
    print("reducing MultiDiGraph to largest DiGraph...")

    di_g = nx.DiGraph(g)  # copy graph (especially all nodes with attributes)
    di_g.remove_edges_from(g.edges())  # remove all edges

    for (n1, n2) in g.edges():
        c = (-1, -1)  # (capacity, index)
        for i in g[n1][n2]:  # loop through all edges between n1 and n2
            if (g[n1][n2][i]['capacity'] + g[n2][n1][i]['capacity']) > c[0]:
                c = (g[n1][n2][i]['capacity'] + g[n2][n1][i]['capacity'], i)  # update max. capacity and index
        if (not di_g.has_edge(n1, n2)) and (c[1] != -1):
            di_g.add_edge(n1, n2, capacity=g[n1][n2][c[1]]['capacity'], fee_rate=g[n1][n2][c[1]]['fee_rate'],
                          base_fee=g[n1][n2][c[1]]['base_fee'], delay=g[n1][n2][c[1]]['delay'],
                          disabled=g[n1][n2][c[1]]['disabled'])
            di_g.add_edge(n2, n1, capacity=g[n2][n1][c[1]]['capacity'], fee_rate=g[n2][n1][c[1]]['fee_rate'],
                          base_fee=g[n2][n1][c[1]]['base_fee'], delay=g[n2][n1][c[1]]['delay'],
                          disabled=g[n2][n1][c[1]]['disabled'])

    return di_g


def multi_to_summed_di_graph(g):
    """
        Input:  MultiDiGraph
        Output: DiGraph

        ~> sums up capacities (chooses fees of 'first' edge) if multiple edges between two nodes exist
            (useful if it is assumed that multi-route payments are possible)
    """
    di_g = nx.DiGraph(g)  # copy graph (especially all nodes with attributes)
    di_g.remove_edges_from(g.edges())  # remove all edges

    for (n1, n2) in g.edges():
        c = 0  # capacity
        for i in g[n1][n2]:  # loop through all edges between n1 and n2
            c += g[n1][n2][i]['capacity']
        if not di_g.has_edge(n1, n2):
            di_g.add_edge(n1, n2, capacity=c, fee_rate=g[n1][n2][0]['fee_rate'],
                          base_fee=g[n1][n2][0]['base_fee'], delay=g[n1][n2][0]['delay'])

    return di_g


def multi_to_undirected_graph(mg, summed=False):
    """
        Input:  MultiDiGraph
                summed == True: multiple edges -> sum up capacities
                summed == False: multiple edges -> choose edge with highest capacity
        Output: (undirected) graph

        ~> realistic representation of LN as only total channel balance (not its distribution) is publicly known
    """
    g = nx.Graph(mg)  # copy graph (especially all nodes with attributes)
    g.remove_edges_from(g.edges())  # remove all edges
    if summed:
        di_g = multi_to_summed_di_graph(mg)
    else:
        di_g = multi_to_largest_di_graph(mg)

    for (n1, n2) in di_g.edges():
        if not di_g.has_edge(n2, n1):
            print("ERROR. No back-edge for", n1, "->", n2, "found")
            continue
        if not g.has_edge(n1, n2):
            g.add_edge(n1, n2, capacity=di_g[n1][n2]['capacity'] + di_g[n2][n1]['capacity'])

    return g
