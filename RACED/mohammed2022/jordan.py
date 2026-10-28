"""
    Collection of useful procedures
"""

import networkx as nx
import time
import random
import math
import numpy as np
from itertools import count
from heapq import heappush, heappop


def copy_matrices(di_g, dist_temp, dist, sigma_temp, sigma, sigma_n_temp, sigma_n):
    """
        resets temp matrices by replacing their entries with the entries from 'dist'/'sigma'/'sigma_n'
    """

    for x in di_g.nodes():
        if dist[x] != dist_temp[x]:
            dist_temp[x].update(dist[x])
        if sigma[x] != sigma_temp[x]:
            sigma_temp[x].update(sigma[x])
        if sigma_n[x] != sigma_n_temp[x]:
            sigma_n_temp[x].update(sigma_n[x])


def copy_matrices2(dist_temp, dist, sigma_temp, sigma, sigma_n_temp, sigma_n, changes):
    """
        copies matrices into temp matrices, but only for the 'changes' indices given
        -> much faster if the matrices are huge and only a few entries changed
    """
    for i in changes:
        dist_temp[i[0]][i[1]] = dist[i[0]][i[1]]
        sigma_temp[i[0]][i[1]] = sigma[i[0]][i[1]]
        sigma_n_temp[i[0]][i[1]] = sigma_n[i[0]][i[1]]


def calc_bc(n, sigma, sigma_n):
    """
        calculates and returns betweenness centrality of 'n' using 'sigma' and 'sigma_n'
    """
    bc_n = 0
    for s in sigma:
        for t in sigma:
            if s != t and t != n and s != n:
                if sigma[s][t] != 0:
                    bc_n += (sigma_n[s][t] / sigma[s][t])
    return bc_n


def choose_channel(g, v, u, amt):
    """
        Input:  MultiDiGraph 'g', channel endpoints 'v' and 'u', amount 'amt' (in sat) to be sent via the channel
        Output: fee (in sat), index of corresponding channel or 'None, None' if routing in v-u direction is not possible

        ~> chooses channel to be used in routing:
            - disabled channels and those with too low capacity are excluded
            - channel that generates lowest fee is chosen (if multiple candidates, lowest-index-channel is chosen)
    """
    f = (math.inf, -1)  # (fee, index)
    for i in g[v][u]:  # loop through all edges between v and u
        if not g[v][u][i]['disabled'] and ((g[v][u][i]['capacity'] + g[u][v][i]['capacity']) >= amt):
            fee = amt * (g[v][u][i]['fee_rate'] / 10 ** 6) + (g[v][u][i]['base_fee'] / 1000)
            if fee < f[0]:
                f = (fee, i)
    if f[1] == -1:  # no channel has enough capacity and is active
        return None, None
    return f[0], f[1]


def create_initial_connection(g, n, weight=None, weight_value=None, metric='random'):
    """
        Input:  graph 'g', new node 'n', possibly weight data, 'metric' to choose node
        Output: node 'n2' to which the initial connection was created

        ~> creates initial connection for node 'n' to the network graph 'g' using the given 'metric'
    """
    if nx.degree(g, n) > 0:
        print("n is already connected to the network!")
        return

    if metric == 'random':
        n2 = random.choice(list(set(g.nodes()) - {n}))  # select random node (except 'n')
    elif metric == 'degree':
        n2 = max(nx.degree(g), key=lambda x: x[1])[0]  # get node with highest degree
    elif metric == 'deg_over20':
        n2 = random.choice([n for n in g.nodes() if nx.degree(g, n) >= 20])  # random node with at least 10 channels
    elif metric == 'deg_over200':
        n2 = random.choice([n for n in g.nodes() if nx.degree(g, n) >= 200])  # random node with at least 100 channels
    elif metric == 'bc':
        bc = nx.betweenness_centrality(g, weight=weight)
        n2 = max(bc, key=lambda x: bc[x])  # get node with highest betweenness centrality
    else:
        print("No valid connection metric")
        return

    g.add_edge(n, n2)
    g.add_edge(n2, n)
    if weight is not None:
        g[n][n2][weight] = weight_value
        g[n2][n][weight] = weight_value

    return n2


def connect(g, i, connect_to, cap, fee_rate=1, base_fee=1000):
    """
        Input:  graph 'g', node 'i', list of nodes to 'connect_to', edge attributes 'cap' and fees

        ~> connects 'i' with each node in 'connect_to' and sets edge attributes
            - chooses default values if fees are not given
            - assumes that both parties deposit 'cap' coins (otherwise 'i' could not be a routing node)
    """
    for n in connect_to:
        g.add_edge(i, n, capacity=cap, fee_rate=fee_rate, base_fee=base_fee, delay=144, disabled=False)
        g.add_edge(n, i, capacity=cap, fee_rate=fee_rate, base_fee=base_fee, delay=144, disabled=False)


def check_path_lengths(di_g, dist, sigma, weight=None):
    """
        only for testing correct calculation of shortest paths
    """
    for u in di_g.nodes():
        for v in di_g.nodes():
            p = list(nx.all_shortest_paths(di_g, u, v, weight))
            if weight is not None:
                w = 0
                for i in range(len(p[0])-1):
                    w += di_g[p[0][i]][p[0][i+1]][weight]
                if not np.isclose(w, dist[u][v]):
                    print("Distance between", u, "and", v, "was calculated incorrectly: ", dist[u][v], w)
                    print("Path:", p[0])
            if weight is None and (dist[u][v] != len(p[0]) - 1):
                print("Distance between", u, "and", v, "was calculated incorrectly: ", dist[u][v], len(p[0]) - 1)
            if sigma[u][v] != len(p):
                print("#shortest paths between", u, "and", v, "was calculated incorrectly: ", sigma[u][v], len(p))
                print(p)


def update_dist_weighted(g, u, v, dist, w):
    """
        Input:  graph 'g', nodes 'u' and 'v', old distance vector 'dist', weight 'w' of u-v channel
        Output: 0 if 'dist' has been updated successfully
                -1 if 'dist' cannot be updated because 'u-v' edge does not exist
        ~> updates u's distance vector 'dist' after edges between 'u' and 'v' with weight 'w' have been
            - uses pruned BFS to avoid unnecessary re-calculation of distances that did not change
    """
    if not g.has_edge(u, v):
        return -1
    if dist[v] > g[u][v][w]:  # new edge changed distance to v
        dist[v] = g[u][v][w]
        q = []
        for x in g.successors(v):
            if dist[x] > dist[v] + g[v][x][w]:
                dist[x] = dist[v] + g[v][x][w]
                q.append(x)
        while q:
            y = q.pop()
            for z in g.successors(y):
                if dist[z] > dist[y] + g[y][z][w]:
                    dist[z] = dist[y] + g[y][z][w]
                    q.append(z)
    return 0


def update_dist_unweighted(g, u, v, dist):
    """
        Input:  graph 'g', nodes 'u' and 'v', old distance vector 'dist'
        Output: 0 if 'dist' has been updated successfully
                -1 if 'dist' cannot be updated because 'u-v' edge does not exist
        ~> updates u's distance vector 'dist' after edges between 'u' and 'v' have been added
            - unweighted -> dist[x] is the number of hops 'u' needs to reach 'v'
            - uses pruned BFS to avoid unnecessary re-calculation of distances that did not change
    """
    if not g.has_edge(u, v):
        return -1
    if dist[v] > 1:  # new edge changed distance to v
        dist[v] = 1
        q = []
        for x in g.successors(v):
            if dist[x] > dist[v] + 1:
                dist[x] = dist[v] + 1
                q.append(x)
        while q:
            y = q.pop()
            for z in g.successors(y):
                if dist[z] > dist[y] + 1:
                    dist[z] = dist[y] + 1
                    q.append(z)
    return 0


def calc_avg_dist(g, n, v, dist, weight):
    """
        Input: graph 'g', nodes 'n' and 'v', old distance vector 'dist', name of edge 'weight'
        Output: average distance of 'n' to all other nodes in 'g'

        ~> calculates average distance of 'n' to all other nodes after edge to 'v' has been added/ deleted
            - if 'weight' is None, number of hops is taken as distance, otherwise 'weight'
            - updates 'dist' vector, if possible using a pruned BFS (-> faster)
            - average distance = sum over all distances / number of nodes
    """
    if weight is None:
        # _, _, _, d = single_source_shortest_paths(g, n)
        if update_dist_unweighted(g, n, v, dist) != 0:
            print("Edge (n,v) does not exist in the graph!")
            dist = single_source_shortest_paths(g, n)
    else:
        # _, _, _, d = single_source_shortest_paths_weighted(g, n, weight)
        if update_dist_weighted(g, n, v, dist, weight) != 0:
            print("Edge (n,v) does not exist in the graph!")
            dist = single_source_shortest_paths(g, n)
    s = sum(dist.values())

    return s


def single_source_shortest_paths(g_new, s):
    """
        Input:  graph 'g_new', source node 's'
        Output: 'stack': reverse order in which nodes have been visited
                paths[v]: predecessors on shortest paths to v
                o[v]: number of shortest paths from s to v
                d[v]: distance (=length of shortest path(s)) from s to v

        ~> finds shortest paths from source 's' to every target node
            -> solves single-source shortest-paths problem (unweighted) -> BFS (-> O(m))
    """
    stack = []
    paths = {}
    for node in g_new.nodes():
        paths[node] = []
    o = dict.fromkeys(g_new, 0)
    o[s] = 1
    dist = dict.fromkeys(g_new, -1)
    dist[s] = 0
    q = [s]  # queue
    while q:
        v = q.pop(0)
        stack.insert(0, v)
        for w in list(nx.neighbors(g_new, v)):
            if dist[w] < 0:  # path discovery (w found for first time)
                q.append(w)
                dist[w] = dist[v] + 1
            if dist[w] == dist[v] + 1:  # path counting ({v,w} on a shortest path?)
                o[w] = o[w] + o[v]
                paths[w].append(v)
    return stack, paths, o, dist


def single_source_shortest_paths_weighted(g_new, s, weight):
    """
        Input:  graph 'g_new', source node 's', edge 'weight'
        Output: 'stack': reverse order in which nodes have been visited
                paths[v]: predecessors on shortest paths to v
                o[v]: number of shortest paths from s to v (*2)
                d[v]: distance (=length of shortest path(s)) from s to v

        ~> solves single-source shortest-paths (SSSP) problem on a weighted graph -> BFS + fibonacci heap
                -> heap makes procedure slower than unweighted SSSP (-> O(m + n log n))
        - used code from networkx documentation ('_single_source_dijkstra_path_basic' procedure)
        https://networkx.github.io/documentation/stable/_modules/networkx/algorithms/centrality/betweenness.html#
        betweenness_centrality
    """
    stack = []
    paths = {}
    for node in g_new.nodes():
        paths[node] = []
    o = dict.fromkeys(g_new, 0.0)  # o[v]=0 for v in g_new
    o[s] = 1.0
    d = {}
    seen = {s: 0}
    c = count()
    q = []  # use q as heap with (distance,node id) tuples
    heappush(q, (0, next(c), s, s))
    while q:
        (dist, _, pred, v) = heappop(q)
        if v in d:
            continue  # already searched this node.
        o[v] += o[pred]  # count paths
        stack.append(v)
        d[v] = dist
        for w, edge_data in g_new[v].items():
            vw_dist = dist + edge_data.get(weight, 1)
            if w not in d and (w not in seen or vw_dist < seen[w]):
                seen[w] = vw_dist
                heappush(q, (vw_dist, next(c), v, w))
                o[w] = 0.0
                paths[w] = [v]
            elif vw_dist == seen[w]:  # handle equal paths
                o[w] += o[v]
                paths[w].append(v)
    stack.reverse()

    return stack, paths, o, d


def accumulation_edges(stack, paths, o, s, p, bc):
    """
        visits all nodes in reverse order, accumulates dependencies, calculates EBC
    """
    d = dict.fromkeys(stack, 0.0)  # d[v]: dependency of 's' on 'v'
    while stack:
        w = stack.pop(0)
        path = paths[w]
        for v in path:
            c = (o[v] / o[w]) * (d[w] + p[w] + p[s] + p[w] * p[s] + 1.0)
            if (v, w) not in bc:
                bc[(w, v)] += c / 2.0
            else:
                bc[(v, w)] += c / 2.0
            d[v] += c
        # if w != s:
            # bc[w] += (d[w] * (p[s] + 1)) / 2


def accumulation(stack, paths, o, s, p, bc):
    """
        visits all nodes in reverse order, accumulates dependencies, calculates BC
    """
    d = dict.fromkeys(stack, 0.0)  # d[v]: dependency of 's' on 'v'
    while stack:
        w = stack.pop(0)
        path = paths[w]
        for v in path:
            d[v] += (o[v] / o[w]) * (d[w] + p[w] + 1.0)
        if w != s:
            bc[w] += (d[w] * (p[s] + 1.0)) / 2.0


def brandes_modified(g, g_new, p, bc, edges=False):
    """
        Input:  (un-)directed graph 'g' and subgraph 'g_new' of it, pre-calculated 'bc' and 'p', EBC?
        Output: betweenness centrality for every node (or edge) in 'g'

        ~> calculates shortest-path betweenness centrality for remaining nodes (or edges, if 'edges' == True)
            - finds shortest paths from every source 's' to every target node and updates betweenness (-> O(nm))
            - only difference to Brandes: bc[v] and d[v] also use 'p' (see [1])
    """
    for s in g_new.nodes():

        stack, paths, o, _ = single_source_shortest_paths(g_new, s)

        if edges:
            accumulation_edges(stack, paths, o, s, p, bc)
        else:
            accumulation(stack, paths, o, s, p, bc)

    if g.is_directed():  # rescale for directed graphs
        for i in bc:
            bc[i] *= 2

    return bc


def brandes_weighted_modified(g, g_new, p, bc, edges=False, weight='fee'):
    """
        Input:  (un-)directed weighted graph 'g' and subgraph 'g_new' of it, pre-calculated 'bc' and 'p'
        Output: betweenness centrality for every node in 'g'

        ~> calculates shortest-path betweenness centrality for remaining nodes (or edges, if 'edges' == True)
            - finds shortest paths from every source 's' to every target node and updates bc (-> O(nm + n^2 log n))
            - only difference to Brandes: bc[v] and d[v] also uses 'p' (see [1])
    """
    for s in g_new.nodes():

        stack, paths, o, _ = single_source_shortest_paths_weighted(g_new, s, weight)

        if edges:
            accumulation_edges(stack, paths, o, s, p, bc)
        else:
            accumulation(stack, paths, o, s, p, bc)

    if g.is_directed():  # rescale for directed graphs
        for i in bc:
            bc[i] *= 2

    return bc


def shortest_path_vertex_betweenness(g, weighted=False, weight='fee'):
    """
        Input:  (un-)directed (weighted) graph 'g'
        Output: betweenness centrality (not normalized) for every node in 'g'

        ~> computes (vertex) betweenness centrality faster for sparse networks
            - iteratively removes nodes with degree 1 and updates affected BC-values
            - then calls (modified) Brandes algorithm
        based on pseudocode in [1]
            - difference: resulting BC values are halved in order to get same results as nx.betweenness_centrality()

        References (for this and all related procedures):
        [1] Baglioni, Miriam, et al.: Fast exact computation of betweenness centrality in social networks.
        IEEE/ACM International Conference on Advances in Social Networks Analysis and Mining. IEEE, 2012.
        [2] Ulrik Brandes: On Variants of Shortest-Path Betweenness Centrality and their Generic Computation.
        Social Networks 30(2):136-145, 2008.
    """
    # print("Calculating shortest_path_vertex_betweenness...")
    # start = time.perf_counter()
    g_new = nx.Graph(g)

    if not nx.is_connected(g_new):
        print("Algorithm does not work properly if graph is not connected. "
              "Call procedure for every connected component separately.")
        return

    deg_1 = [n[0] for n in nx.degree(g_new) if n[1] == 1]  # list of all nodes with degree 1

    bc = dict.fromkeys(g, 0.0)  # bc[i]: betwenness centrality of node i
    p = dict.fromkeys(g, 0.0)  # p[i]: ~no. nodes in subtrees of i (shortest paths between them don't affect bc[i])

    while deg_1 and g_new.number_of_nodes() > 1:  # last condition necessary in case g is a tree
        v = deg_1.pop()
        u = list(nx.neighbors(g_new, v)).pop()  # u: v's (only) neighbor
        bc[u] += (g.number_of_nodes() - p[v] - p[u] - 2.0) * (p[v] + 1.0)
        p[u] += p[v] + 1.0
        g_new.remove_edge(u, v)
        g_new.remove_node(v)
        if nx.degree(g_new, u) == 1:
            deg_1.append(u)
    # end = time.perf_counter()
    # print("excluding nodes took:", end-start, "seconds")
    if g.is_directed() and weighted:
        g_new = nx.DiGraph(g_new)
        for (n1, n2) in g_new.edges():
            g_new[n1][n2][weight] = g[n1][n2][weight]
    if g_new.number_of_nodes() > 1:
        # start = time.time()
        if weighted:
            bc = brandes_weighted_modified(g, g_new, p, bc, False, weight)
            # end = time.time()
            # print("brandes_weighted_modified took:", end - start, "seconds")
        else:
            bc = brandes_modified(g, g_new, p, bc)
            end = time.time()
            # print("brandes_modified took:", end - start, "seconds")
    elif g.is_directed():
        for i in bc:
            bc[i] *= 2

    return bc


def shortest_path_edge_betweenness(g, weighted=False, weight='fee'):
    """
        Input:  (un-)directed (weighted) graph 'g'
        Output: betweenness centrality (not normalized) for every edge in 'g'

        (Assumption: if (u,v) is an edge, then (v,u) is also an edge)
        ~> modification of SPVB algorithm -> calculates betweenness for EDGES

        References (for this and all related procedures):
        [1] Baglioni, Miriam, et al.: Fast exact computation of betweenness centrality in social networks.
        IEEE/ACM International Conference on Advances in Social Networks Analysis and Mining. IEEE, 2012.
        [2] Ulrik Brandes: On Variants of Shortest-Path Betweenness Centrality and their Generic Computation.
        Social Networks 30(2):136-145, 2008.
    """
    # print("Calculating shortest_path_edge_betweenness...")
    # start = time.perf_counter()
    g_new = nx.Graph(g)

    if not nx.is_connected(g_new):
        print("Algorithm does not work properly if graph is not connected. "
              "Call procedure for every connected component separately.")
        return

    if g.is_directed():
        g_new = nx.DiGraph(g)
        deg_1 = [n[0] for n in nx.degree(g) if n[1] == 2]  # list of all nodes with degree 1 (one in-/out-edge each)
    else:
        deg_1 = [n[0] for n in nx.degree(g) if n[1] == 1]  # list of all nodes with degree 1
    # bc = dict.fromkeys(g, 0)  # bc[n] = 0 for every node 'n'
    bc = {}
    bc.update(dict.fromkeys(g.edges(), 0))  # bc[(u,v)] = 0 for every edge '(u,v)'
    p = dict.fromkeys(g, 0.0)  # p[i]: ~no. nodes in subtrees of i (shortest paths between them don't affect bc[i])

    while deg_1 and g_new.number_of_nodes() > 1:  # last condition necessary in case g is a tree
        v = deg_1.pop()
        u = list(nx.neighbors(g_new, v)).pop()  # u: v's (only) neighbor
        # bc[u] += (g.number_of_nodes() - p[v] - p[u] - 2) * (p[v] + 1)
        # update bc of edge {v, u}:nx.degree(g)
        if g.is_directed():
            bc[(u, v)] += ((g.number_of_nodes() - p[v] - 1) * (p[v] + 1)) / 2  # /2 as it is multiplied by 2 later
            bc[(v, u)] += ((g.number_of_nodes() - p[v] - 1) * (p[v] + 1)) / 2
            g_new.remove_edge(v, u)
        elif (v, u) not in bc:
            bc[(u, v)] += (g.number_of_nodes() - p[v] - 1) * (p[v] + 1)
        else:
            bc[(v, u)] += (g.number_of_nodes() - p[v] - 1) * (p[v] + 1)
        p[u] += p[v] + 1
        g_new.remove_edge(u, v)
        g_new.remove_node(v)
        if nx.degree(g_new, u) == 1 or (g.is_directed() and nx.degree(g_new, u) == 2):
            deg_1.append(u)
    # end = time.perf_counter()
    # print("excluding nodes took:", end - start, "seconds")
    if g_new.number_of_nodes() > 1:
        start = time.perf_counter()
        if weighted:
            bc = brandes_weighted_modified(g, g_new, p, bc, True, weight)
            end = time.perf_counter()
            print("brandes_weighted_modified took:", end - start, "seconds")
        else:
            bc = brandes_modified(g, g_new, p, bc, True)
            end = time.perf_counter()
            print("brandes_modified took:", end - start, "seconds")
    elif g.is_directed():
        for i in bc:
            bc[i] *= 2

    return bc


def find_stars(g):
    """
        Input:  (un-)directed (multi-)graph 'g'
                (if the graph is directed, symmetry of the edges is assumed)
        Output: reduced_node_list
                reduced_node_list[v]: list of all nodes that can be represented by 'v'
                    -> nodes in this list have the same edge (weights) as 'v' has to the common neighbor
                    -> nodes in this list are not listed in 'reduced_node_list' anymore

        ~> finds star sub-structures in 'g' and merges degree-1 nodes connected to central nodes into one node
        -> further reduces number of nodes in the network
    """
    reduced_node_list = {}
    for n in g.nodes:
        reduced_node_list[n] = []
    deg_1 = [(n[0], list(nx.neighbors(g, n[0]))) for n in nx.degree(g) if n[1] == 2]  # list of all nodes with degree 1
    deg_1 = sorted(deg_1, key=lambda x: x[1])
    reduced_node_list[deg_1[0][0]].append(deg_1[0][0])
    rep = {deg_1[0][1][0]: [deg_1[0][0]]}
    for i in range(1, len(deg_1)):
        n = deg_1[i]  # node and its only neighbor
        reduced_node_list[n[0]].append(n[0])
        if n[1] == deg_1[i-1][1]:
            rep[n[1][0]].append(n[0])
            for v in rep[n[1][0]]:  # loop through all possible representatives
                if v != n[0] and (g[n[0]][n[1][0]] == g[v][n[1][0]] and g[n[1][0]][n[0]] == g[n[1][0]][v]):
                    reduced_node_list.pop(n[0])
                    reduced_node_list[v].append(n[0])
                    rep[n[1][0]].remove(n[0])
                    break
            continue
        rep[n[1][0]] = [n[0]]

    return reduced_node_list
