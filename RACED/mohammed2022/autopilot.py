"""
    AUTOPILOT
    ~> returns 'k' nodes that node 'n' should connect to
"""

import random
import networkx as nx
import numpy as np
import graph_creation as gc
import parallel_autopilot as pap
import utils
import time
import math
import sys


def start_autopilot(graph, n, k, metric='random', weight=None, weight_value=None, edges=None, pair_dist=None,
                    node_map=None, dist_matrix=None, cpus=None):
    """
        Input:  'graph', new node 'n', no. of new connections 'k', 'metric' to be used, possibly weight name + value,
                possibly pre-calculated data (useful for
        Output: list of 'k' candidates that 'n' should connect to

        ~> computes nodes 'n' could possibly be connected to
        if less than 'k' candidates: connect to all of them
        else: sort according to respective 'metric'/ execute resp. algorithm and return the 'k' most suitable candidates
    """
    if k == 0:
        return []

    g = graph.copy()
    # reduce graph to largest component:
    max_comp = max(nx.strongly_connected_components(g), key=len)
    g = g.subgraph(max_comp).copy()
    print("Autopilot reduced graph to largest strongly connected component ({} nodes)".format(g.number_of_nodes()))
    if n not in g.nodes():  # add new node (again)
        g.add_node(n, key='connected_using_autopilot', alias='new_node')

    nodes = g.nodes()
    # (removing n's neighbors from the candidates set assumes that it's not useful to open multiple channels to a node)
    nodes = list((set(nodes) - set(g.neighbors(n))) - {n})  # remove nodes that 'n' is already connected to (and 'n')
    if len(nodes) <= k:
        return nodes

    sorted_nodes = []

    # call procedure depending on 'metric' given
    if metric == 'random':
        return choose_random(k, nodes)
    elif metric == 'k-center_gon':
        return k_center(g, n, k, 'gon')
        # return k_center(g, n, k, 'gon', weight, weight_value)  -> no weighted version implemented yet
    elif metric == 'k-center_gon_deg':
        return k_center(g, n, k, 'gon_deg')
    elif metric == 'k-center_hs':
        return k_center(g, n, k, 'hs', edges, weight, weight_value)
    elif metric == 'k-center_mr':
        return k_center(g, n, k, 'mr', edges, weight, weight_value)
    elif metric == 'k-median':
        return k_median(g, n, k, nodes, weight=weight, w_val=weight_value)
    elif metric == 'k-median_deg':
        return k_median(g, n, k, nodes, algorithm='deg', weight=weight, w_val=weight_value)
    elif metric == 'k-median_par':
        return pap.k_median_parallel(g, n, k, nodes, weight=weight, w_val=weight_value, c=cpus)
    elif metric == 'k-median_par_deg':
        return pap.k_median_parallel(g, n, k, nodes, algorithm='deg', weight=weight, w_val=weight_value, c=cpus)
    elif metric == 'k-median_reverse':
        return k_median(g, n, k, nodes, algorithm='reverse', weight=weight, w_val=weight_value,
                        pair_dist=pair_dist, node_map=node_map, dist_matrix=dist_matrix)
    elif metric == 'greedy_mbi':
        if weight is None:
            return greedy_mbi(g, n, k, nodes)
        else:
            if weight_value is None:
                print("No weight value for new edges given!")
                return -1
            return greedy_mbi(g, n, k, nodes, weight, weight_value)
    elif metric == 'greedy_mbi_par':
        return pap.greedy_mbi_parallel(g, n, k, nodes, weight=weight, weight_value=weight_value, c=cpus)
    elif metric == 'bc':
        if weight is None:
            sorted_nodes = sort_by_centrality(g, n, nodes)
        else:
            sorted_nodes = sort_by_centrality(g, n, nodes, weight=weight)
    elif metric == 'bc_approx_10':
        if weight is None:
            sorted_nodes = sort_by_centrality_approx(g, factor=0.1)
        else:
            sorted_nodes = sort_by_centrality_approx(g, weight=weight, factor=0.1)
    elif metric == 'bc_approx_50':
        if weight is None:
            sorted_nodes = sort_by_centrality_approx(g, factor=0.5)
        else:
            sorted_nodes = sort_by_centrality_approx(g, weight=weight, factor=0.5)
    # elif metric == 'wealth':
    #    sorted_nodes = sort_by_wealth(g, nodes)
    elif metric == 'highest_degree':
        sorted_nodes = sort_by_degree(g, nodes, 'high_to_low')
    # elif metric == 'lowest_degree':
    #    sorted_nodes = sort_by_degree(g, nodes, 'low_to_high', True)
    # elif metric == 'page_rank':
    #    sorted_nodes = sort_by_page_rank(g, nodes)
    else:
        print("Given metric could not be assigned to an existing procedure!")
        return -1

    if sorted_nodes:
        print(list(sorted_nodes)[:20], "...")
        candidates = []  # list of possible candidates to connect 'n' to
        while len(candidates) < k:
            i = sorted_nodes[0][1]  # store best value
            deg_i = [node for node in sorted_nodes if (node[1] == i)]  # calculate nodes with value i
            if len(candidates) + len(deg_i) > k:
                # if more nodes have value 'i' than fit into 'candidates' (length k),
                # randomly (-> random.shuffle) add some of them (to fill the list):
                random.shuffle(deg_i)
                candidates.extend(deg_i[:(k - len(candidates))])
                break
            candidates.extend(deg_i)  # store nodes with value i
            sorted_nodes = sorted_nodes[-(len(sorted_nodes) - len(deg_i)):]  # nodes with value i are processed

        return list(dict(candidates).keys())  # return list of nodes


def choose_random(k, nodes):
    """
        choose RANDOM nodes
    """
    print("choosing", k, "random node(s)...")

    return random.sample(nodes, k)


def sort_by_degree(g, nodes, ordering='high_to_low', exclude_deg_0=False):
    """
        sort according to HIGH/LOW DEGREE (depends on ordering ('high_to_low' or 'low_to_high'))
    """
    print("sorting nodes by degree...")
    sorted_by_deg = sorted(nx.degree(g), key=lambda x: x[1])  # sort nodes by degree (smallest to highest)
    if ordering == 'high_to_low':
        sorted_by_deg.reverse()  # sort nodes by degree (highest to smallest)
    elif ordering != 'low_to_high':
        print("Error! No valid parameter given!")
        return
    if exclude_deg_0:
        # exclude nodes from list 'nodes' and those with degree 0 as it is not useful to connect to those
        sorted_by_deg = [node for node in sorted_by_deg if (node[0] in nodes) and (node[1] > 0)]
    else:
        sorted_by_deg = [node for node in sorted_by_deg if (node[0] in nodes)]  # only take nodes from list 'nodes'

    return sorted_by_deg


def sort_by_centrality_approx(g, weight=None, factor=0.5):
    """
        calculates BC approximately (using 'factor'*100 percent of all nodes) and returns nodes sorted according to
        their BC score
        ~> faster than sort_by_centrality
    """
    if factor < 0 or factor > 1:
        print("Factor has to be between 0 and 1!")
        return []
    print("sorting by betweenness centrality (approximate with {} percent of all nodes)...".format(factor * 100))
    if weight is None:
        bc = nx.betweenness_centrality(g, normalized=False, k=int(g.number_of_nodes() * factor))
    else:
        bc = nx.betweenness_centrality(g, normalized=False, weight=weight, k=int(g.number_of_nodes() * factor))
    sorted_bc = (sorted(list(bc.items()), key=lambda x: x[1], reverse=True))

    return sorted_bc


def sort_by_centrality(g, exclude_n=None, nodes=None, weight=None, max_elem=False, edges=False):
    """
        sort according to (EDGE) BETWEENNESS CENTRALITY
            - max_elem=True: only return node with highest (e)bc
            - edges: calculate edge bc
    """
    print("sorting by betweenness centrality...")
    di_g = nx.DiGraph(g)
    if g.is_multigraph():  # convert MultiDiGraph to DiGraph (with largest or summed capacity)
        di_g = gc.multi_to_largest_di_graph(g)
        # di_g = gc.multi_to_summed_di_graph(g)
    if exclude_n is not None:
        di_g.remove_node(exclude_n)

    # store subgraphs (each consisting of a strongly connected component of di_g) in subs
    comp = list(nx.strongly_connected_components(di_g))
    print("{} strongly connected component(s)".format(len(comp)))
    subs = {}
    i = 0
    for c in comp:
        subs[i] = di_g.subgraph(c).copy()
        i += 1

    # calculate BC for each subgraph separately:
    bc = {}  # bc of di_g
    for s in subs:
        bc_sub = {}
        if edges:  # calculate EBC
            if weight is None:
                bc_sub = nx.edge_betweenness_centrality(subs[s], normalized=False)
                # bc_sub = utils.shortest_path_edge_betweenness(subs[s])  # faster option
            else:
                bc_sub = nx.edge_betweenness_centrality(subs[s], normalized=False, weight=weight)
                # bc_sub = utils.shortest_path_edge_betweenness(subs[s], True, weight)  # faster option
        else:  # calculate BC
            if weight is None:
                # bc2 = nx.betweenness_centrality(subs[s], normalized=False)
                bc_sub = utils.shortest_path_vertex_betweenness(subs[s])  # faster option
            else:
                # bc2 = nx.betweenness_centrality(subs[s], normalized=False, weight=weight)
                bc_sub = utils.shortest_path_vertex_betweenness(subs[s], True, weight)  # faster option
        bc.update(bc_sub)  # merge bc_sub into bc (no overwriting of values since every node is in exactly one subgraph)
    # print("BC: ", bc)
    if max_elem:
        return max(bc, key=lambda j: bc[j])  # faster than sorting and then only taking the first element
    sorted_by_bc = sorted(list(bc.items()), key=lambda x: x[1])  # sort nodes according to BC (lowest to highest)
    if nodes is not None:
        sorted_by_bc = [node for node in sorted_by_bc if (node[0] in nodes)]  # only take nodes from list 'nodes'
    sorted_by_bc.reverse()  # sort highest to lowest BC

    return sorted_by_bc

    # without shuffling of nodes with same BC value:
    # node_bc = sorted(bc, key=lambda x: bc[x])  # sort nodes according to BC (lowest to highest)
    # node_bc = [node for node in node_bc if (node in nodes)]  # only take nodes from list 'nodes'
    # return node_bc[-k:]  # return last k elements (nodes with highest BC)


def sort_by_page_rank(g, nodes, weight='capacity'):
    """
        sort according to Google's PAGE RANK
    """
    print("sorting nodes by PageRank...")
    pr = nx.pagerank_numpy(g, weight=weight)
    sorted_by_pr = sorted(list(pr.items()), key=lambda x: x[1])  # sort nodes according to PageRank (lowest to highest)
    sorted_by_pr = [node for node in sorted_by_pr if (node[0] in nodes)]  # only take nodes from list 'nodes'
    sorted_by_pr.reverse()  # sort highest to lowest PageRank

    return sorted_by_pr


def sort_by_wealth(g, nodes):
    """
        sort according to WEALTH
        wealth (=capacity) of a node calculated as sum of channels' capacities
        -> as exact shares are not known, capacities of edges in both directions are added
            -> therefore, this is just an estimate of a node's wealth
    """
    print("sorting nodes by wealth (=total summed capacity of their channels")
    sorted_by_capacity = {}
    for n in g.nodes():
        sorted_by_capacity[n] = 0
        for m in g.neighbors(n):
            if g.get_edge_data(n, m) is not None:
                if g.is_multigraph():
                    for i in g[n][m]:
                        sorted_by_capacity[n] += (g[n][m][i]['capacity'] + g[m][n][i]['capacity'])
                else:
                    sorted_by_capacity[n] += (g[n][m]['capacity'] + g[m][n]['capacity'])
    sorted_by_capacity = sorted(list(sorted_by_capacity.items()), key=lambda x: x[1])  # sort nodes
    sorted_by_capacity = [node for node in sorted_by_capacity if (node[0] in nodes)]  # exclude 'nodes'
    sorted_by_capacity.reverse()  # sort from highest to lowest capacity

    return sorted_by_capacity


def dominating_set_approx(g):
    """
        Input:  graph 'g'
        Output: dominating set for 'g'

        ~> calculates approximation of a minimal dominating set in 'g'
            -> pseudocode from [MS05]
    """
    print("calculating a dominating set...", end="")
    dom_set = []
    deg = nx.degree(g)
    cover_cnt = {n: deg[n] + 1 for n in g.nodes()}
    score = cover_cnt.copy()
    for i in range(g.number_of_nodes()):
        x = min(score, key=lambda y: score[y])
        neighbors_covered = {n: cover_cnt[n] for n in nx.neighbors(g, x)}
        if 1 in neighbors_covered.values():
            dom_set.append(x)
            for n in neighbors_covered:
                cover_cnt[n] = 0
        else:
            for n in neighbors_covered:
                if cover_cnt[n] > 0:
                    cover_cnt[n] -= 1
                    score[n] += 1
        cover_cnt[x] -= 1
        score[x] = math.inf
    print("done ({})".format(dom_set))

    return dom_set


def ds_strategy(graph, k, alg='hs', edges=None):
    """
        Input: 'graph', parameter 'k', algorithm 'alg', pre-calculated 'edges' of complete distance graph
        Output: k-center in 'g'

        ~> calculates a k-center in the graph using different dominating set strategies:
            - 'hs' -> [HS85]  (finding independent set in squared bottleneck graph)
            - 'mr' -> [MR05]  (DS approximation algorithm)
        References:
            [HS85]  Hochbaum, Dorit S., and Shmoys,David B.: A best possible heuristic for the k-center problem.
                    Mathematics of operations research 10.2 (1985): 180-184.
            [MR05]  Robič, Borut, and Mihelič, Jurij: Solving the k-center problem efficiently with a dominating set
                    algorithm. Journal of computing and information technology 13.3 (2005): 225-234.
                    -> or use DS approximation algorithm provided by nx

    """
    start = time.perf_counter()
    g = nx.Graph(graph)  # make graph undirected (assume symmetry of directed edges)
    if edges is None:
        edges = {}  # dict w/ all distances and the corresponding edges (edges[x]: list with all edges of weight x)
        for n in g.nodes():
            d = nx.single_source_shortest_path_length(g, n)  # distance of 'n' to all other nodes
            for i in d:
                if d[i] in edges:
                    if n < i:  # only add every edge once!
                        edges[d[i]].append((n, i))  # add (n,i) to list of node pairs w/ dist[i]
                else:
                    if n < i:
                        edges[d[i]] = [(n, i)]  # new list for node pairs w/ dist d[i] -> first one: (n,i)

    for e in edges:
        random.shuffle(edges[e])  # random ordering among edges with same weight

    candidates = []
    low = 1
    high = sum([len(edges[e]) for e in edges])  # total number of edges
    mid = 0  # -> necessary for first loop iteration as graph is still empty

    # create first bottleneck graph g_i:
    g_i = nx.Graph()
    g_i.add_nodes_from(g.nodes())

    # find smallest 'i' such that g_i has a dom. set of size <= k
    while high != low + 1:  # binary search (-> faster)
        mid_old = mid
        mid = int((high + low) / 2)
        edges_added = 0

        # create new bottleneck graph g_i (by updating the old one -> saves time):
        if mid > mid_old:  # (mid - mid_old) edges have to be added to g_i
            for e in edges:
                length_e = len(edges[e])
                if (length_e + edges_added) <= mid_old:
                    edges_added += length_e  # edges are already part of g_i (do not have to be added)
                else:
                    start_idx = max(0, mid_old - edges_added)  # edges[e][:start_idx] are already in g_i
                    if length_e >= mid - edges_added:  # all edges that still have to be added have weight e
                        edges_added += len(edges[e][:start_idx])  # these edges are already part of g_i
                        g_i.add_edges_from(edges[e][start_idx:start_idx + (mid - edges_added)])  # add remaining edges
                        break
                    else:  # all edges with weight e are part of g_i, but also more
                        g_i.add_edges_from(edges[e][start_idx:])  # add edges that are not in g_i yet
                        edges_added += length_e
        else:  # (mid_old - mid) edges have to be removed from g_i
            for e in edges:
                length_e = len(edges[e])
                if (length_e + edges_added) <= mid:  # all edges with weight e remain in g_i
                    edges_added += length_e
                else:
                    start_idx = max(0, mid - edges_added)
                    if length_e >= mid_old - edges_added:  # all edges that still have to be removed have weight e
                        edges_added += len(edges[e][:start_idx])  # these edges stay part of g_i
                        g_i.remove_edges_from(edges[e][start_idx:start_idx + (mid_old - edges_added)])
                        break
                    else:  # edges with weight e have to be removed from g_i, but also more
                        g_i.remove_edges_from(edges[e][start_idx:])
                        edges_added += length_e

        print("bottleneck graph has {} (mid={}) edges".format(g_i.number_of_edges(), mid))
        """
        ##### old version (always created new bottleneck graph) #####
        mid = int((high + low) / 2)

        # create bottleneck graph g_i:
        g_i = nx.Graph()
        g_i.add_nodes_from(g.nodes())
        edges_added = 0
        for e in edges:
            if (len(edges[e]) + edges_added) <= mid:  # add all edges with weight e
                g_i.add_edges_from(edges[e])
                edges_added += len(edges[e])
            else:  # add edges with weight e until g_i has 'mid' edges
                g_i.add_edges_from(edges[e][:mid - edges_added])
                break
        """
        candidates_temp = []
        if alg == 'mr':
            # candidates_temp = nx.dominating_set(g_i)    # find (approx.) dominating set (OPTION 1!)
            candidates_temp = dominating_set_approx(g_i)  # find (approx.) dominating set (OPTION 2!)
            # print("dominating set:", candidates_temp)
        elif alg == 'hs':
            print("finding independent set in squared graph...", end="")
            # find maximal independent set in squared graph (OPTION 3!)
            # nodes = list(g_i.nodes())
            nodes = set(g_i.nodes())
            while nodes and len(candidates_temp) <= k:
                x = random.choice(list(nodes))  # select random node 'x'
                # nodes.remove(x)
                nodes = nodes - {x}
                candidates_temp.append(x)  # add 'x' to the candidate set
                # also delete x's neighbors and their neighbors (in g_mid = (V, E_mid)):
                # (-> 'candidates' is independent set in square graph)
                for y in nx.neighbors(g_i, x):
                    # nodes.remove(y)
                    nodes = nodes - {y}
                    for z in nx.neighbors(g_i, y):
                        # nodes.remove(z)
                        nodes = nodes - {z}
            print("done")
        else:
            print("no valid algorithm given!")
            return []

        if len(candidates_temp) <= k:  # a feasible solution was found
            high = mid  # can a better solution in a smaller bottleneck graph be found?
            candidates = candidates_temp
            if len(candidates_temp) == k:
                print("Dominating set:", candidates_temp, "g_i for i = ", mid)
        else:
            low = mid

    print("")
    end = time.perf_counter()
    print("DS-Strategy took {} seconds".format(end - start))

    return candidates


def gonzalez(g, n, k):
    """
        Input: graph 'g', node 'n', number of candidates to select ('k')
        Output: 'k' nodes that minimize the longest shortest path to all other nodes in the UNWEIGHTED graph 'g'

        ~> executes modified first step of a variant [PBG13] of Gonzalez' algorithm [Gon85]
            -> always connects 'n' to the node that is farthest (= most hops) away

        References:
            [Gon85] Gonzalez, Teofilo F.: Clustering to minimize the maximum intercluster distance.
                    Theoretical Computer Science 38 (1985): 293-306.
            [PBG13] Perumal, Senni, Prithwish Basu, and Ziyu Guan: Minimizing eccentricity in composite networks via
                    constrained edge additions. IEEE Military Communications Conference (MILCOM’13): 1894-1899.
    """
    # print("starting Gonzalez' algorithm...")
    if nx.degree(g, n) < 1:
        print("Cannot execute gonzalez' algorithm. Node does not have any neighbor yet!")
        return []
    candidates = []
    while len(candidates) != k:
        # calculate distance from 'n' to all other nodes in 'g' (= number of hops):
        # _, _, _, dist = utils.single_source_shortest_paths(g, n)
        dist = nx.single_source_shortest_path_length(g, n)
        # get node that is farthest away and connect 'n' to it:
        # new = max(dist, key=lambda j: dist[j])  # -> disregards multiple maximal elements (but a bit faster)
        max_dist = max(dist.values())
        candidate_temp = []
        for i in dist:
            if dist[i] == max_dist:
                candidate_temp.append(i)
        new = random.choice(candidate_temp)  # choose a random candidate among those with maximal distance to 'n'
        g.add_edge(n, new)
        g.add_edge(new, n)
        candidates.append(new)

    return candidates


def k_center(g, n, k, algorithm='gon', edges=None, weight=None, weight_value=None):
    """
        Input:  graph 'g', node 'n', parameter 'k', 'algorithm' to use ([Gon85] or HS)
        Output: 'k' candidates that 'n' should connect to

        metric: minimize n's eccentricity (=max distance from n to all other nodes in g)
        motivation: k-center problem
            -> NP-complete
            -> solve using approx. algorithm (2-approximations)
                -> only work on undirected, unweighted graph (minimize number of hops)
                    (weighted fee graph of LN is no metric space)
    """
    print("starting k-center_{} algorithm...".format(algorithm), end=" ")
    di_g = g.copy()
    if g.is_multigraph():  # convert MultiDiGraph to DiGraph (with largest capacity)
        di_g = gc.multi_to_largest_di_graph(g)
    max_comp = max(nx.strongly_connected_components(di_g), key=len)
    di_g = di_g.subgraph(max_comp).copy()  # reduce graph to largest connected component
    print("using largest strongly connected component ({} nodes)".format(di_g.number_of_nodes()))

    candidates = []  # list of candidates that 'n' should connect to

    if algorithm == 'hs' or algorithm == 'mr':
        # node 'n' is not considered yet, only the 'k' centers are calculated
        candidates = ds_strategy(di_g, k, alg=algorithm, edges=edges)
        if len(candidates) == k:
            return candidates
        else:
            # if a set with less than 'k' candidates is returned, [GON85] is executed to determine the remaining nodes
            print("Only", len(candidates), "candidate(s) returned. Gonzalez' algorithm executed to find remaining "
                                           "node(s).")

    if n not in di_g.nodes():
        di_g.add_node(n)

    for v in candidates:
        di_g.add_edge(n, v)
        di_g.add_edge(v, n)
        di_g[n][v][weight] = weight_value
        di_g[v][n][weight] = weight_value
        k -= 1

    deg_n = nx.degree(di_g, n)  # store degree of node n
    if deg_n == 0:  # 'n' was newly added and does not have neighbors yet
        # create initial connection of 'n' to the network (otherwise n cannot reach any other node):
        n2 = utils.create_initial_connection(di_g, n, weight, weight_value, metric='degree')
        if algorithm == 'gon_deg':  # connect to node with highest degree and keep the channel
            candidates.append(n2)
            k -= 1
            print("Added (permanent) channel from", n, "to", n2, "(initial connection to the network)")
        else:
            print("Added (temporary) channel from", n, "to", n2, "(initial connection to the network)")

    if weight is None:
        candidates.extend(gonzalez(di_g, n, k))
    else:
        print("No weighted version of k-center implemented yet")
        print("P.S.: How does it work given a non-metric space, anyway?")
        return []

    return candidates


def k_median_reverse_greedy(g, n, k, nodes, weight=None, w_val=None, pair_dist=None, node_map=None, dist_matrix=None):
    """
        Input:  graph 'g', node 'n', parameter 'k', candidates 'nodes', maybe pre-calculated distance information
        Output: 'k' candidates that 'n' should connect to

        ~> solves the k-median problem on 'g' using the reverse greedy approximation algorithm described in [CKY05]
            - focuses on minimizing n's average shortest path length -> minimizes sum of n's distance vector
            - so far only unweighted version implemented (-> 'weight' and 'w_val' not really needed)

        References:
            [CKY05] Chrobak, Marek, Claire Kenyon, and Neal Young.: The reverse greedy algorithm for the metric
                    k-median problem. Information Processing Letters 97.2 (2006): 68-72.
    """
    candidates = nodes.copy()
    g.remove_node(n)
    if not nx.is_strongly_connected(g):  # 'g' w/o 'n' has to be strongly connected to conduct distance calculations
        print("Error! The graph (without n) is not strongly connected!")
        return []

    if pair_dist is None or node_map is None or dist_matrix is None:  # pre-calculated input not (fully) given...

        node_map = {}  # maps (non-continuous) node indices to (continuous) indices used in dist_matrix
        idx = 0
        for node in g.nodes():
            node_map[node] = idx
            idx += 1

        dist_matrix = np.empty((g.number_of_nodes(), g.number_of_nodes()))

        start = time.perf_counter()
        pair_dist = {i: {j: 0 for j in g.nodes()} for i in g.nodes()}  # pairwise distances
        # fill distance matrix with pairwise distances:
        for s in g.nodes():
            sys.stdout.write("\r" + str(s))
            if weight is None:
                d = nx.single_source_shortest_path_length(g, s)
            else:
                print("Reverse Greedy Algorithm does not work for weighted graphs, yet (they often don't constitute a "
                      "metric space anyway)! Furthermore, it would not be possible to calculate the best possible "
                      "distance vector (for real edge weights) and therefore the calculation would take MUCH LONGER!")
                # in principle this procedure could be easily be extended for weighted graphs, but I haven't found a
                # way to speed up the computation, yet
                return []
            pair_dist[s] = d
            for t in d:
                if s == t:
                    dist_matrix[node_map[s]][node_map[t]] = math.inf
                    # -> allows to search for the minimum in the row and find the closest node (!= s)
                else:
                    dist_matrix[node_map[s]][node_map[t]] = pair_dist[s][t]
        end = time.perf_counter()
        print("Calculating pairwise distances took", end - start, "seconds!")

    g.add_node(n)

    # connect 'n' to all nodes that 'n' is not connected to yet:
    for n2 in nodes:
        g.add_edge(n, n2)
        g.add_edge(n2, n)
        g[n][n2][weight] = w_val
        g[n2][n][weight] = w_val

    dist = {i: math.inf for i in g.nodes()}  # n's distances to all other nodes

    # remove nodes from 'candidates' until only 'k' candidates are left:
    while len(candidates) > k:
        min_dist = (math.inf, -1)
        d = nx.single_source_shortest_path_length(g, n)
        bfs_tree = nx.bfs_tree(g, n)
        random.shuffle(candidates)  # first edge to be deleted is chosen randomly
        for v in candidates:
            sys.stdout.write("\r" + str(v))
            dist.update(d)  # reset distance vector
            g.remove_edge(n, v)
            g.remove_edge(v, n)
            bfs_tree.remove_edge(n, v)
            conn_comp = list(nx.weakly_connected_components(bfs_tree))  # exactly two components
            for c in conn_comp:
                if n not in c:
                    # update 'dist' and 'bfs_tree' for all nodes in a different connected component than 'n'
                    # update average distance -> stop loop if the average distance is already higher than min_dist[0]
                    summed_dist = sum(dist.values())  # summed distance (before edge was deleted)
                    for i in c:
                        dist_matrix[node_map[i]][node_map[v]] = math.inf  # i cannot be reached via v
                        new = min(dist_matrix[node_map[i]]) + 1
                        dist_matrix[node_map[i]][node_map[v]] = pair_dist[i][v]  # reset dist value
                        old_dist_i = dist[i]
                        dist[i] = new
                        summed_dist += new - old_dist_i  # update summed distance
                        if summed_dist > min_dist[0]:
                            # average distance is already higher than current min_dist -> discard this iteration
                            # -> saves unnecessary computations
                            break
            bfs_tree.add_edge(n, v)
            s = sum(dist.values())
            if s < min_dist[0]:  # update minimal average distance
                min_dist = (s, v)
            g.add_edge(n, v)
            g.add_edge(v, n)
            g[n][v][weight] = w_val
            g[v][n][weight] = w_val
            # if weight is None and np.isclose(s, (((len(dist)-len(candidates))/(len(dist)-1)) + 1)):
            if weight is None and np.isclose(s, ((len(dist) + (len(dist) - len(candidates))) - 1)):
                print("\n", s, ((len(dist) + (len(dist) - len(candidates))) - 1), end="\t")
                # best: every node c not in 'candidates' has dist[c] = 2
                #   len(dist) ... -1    => every node has at least dist = 1, except n (dist[n]=0)
                #   ... + len(dist) - len(candidates) ...   => nodes not in 'candidates' have dist = 2
                break  # best possible value has been reached?!
        # remove node from candidate set whose deletion generates minimal average distance:
        g.remove_edge(n, min_dist[1])
        g.remove_edge(min_dist[1], n)
        candidates.remove(min_dist[1])
        dist_matrix[:, node_map[min_dist[1]]] = math.inf  # set this column to infinite distance
        print("Removed channel between", n, "and", min_dist[1])

    return candidates


def k_median(g, n, k, nodes, algorithm=None, weight=None, w_val=None, pair_dist=None, node_map=None, dist_matrix=None):
    """
        Input: graph 'g', node 'n', parameter 'k'
        Output: 'k' candidates that 'n' should connect to

        ~> metric: minimize n's average shortest path length
            -> k-median problem
                -> NP-hard => greedy approximation algorithm:
                    - always add channel that minimizes average shortest path length
                -> if algorithm == 'reverse', executes reverse greedy approximation algorithm
    """
    print("starting k-median algorithm...", end=" ")
    di_g = g.copy()
    if g.is_multigraph():  # convert MultiDiGraph to DiGraph (with largest or summed capacity)
        di_g = gc.multi_to_largest_di_graph(g)
        # di_g = gc.multi_to_summed_di_graph(g)
    if not nx.is_strongly_connected(di_g):
        max_comp = max(nx.strongly_connected_components(di_g), key=len)
        di_g = di_g.subgraph(max_comp).copy()  # reduce graph to largest connected component
        print("using largest strongly connected component ({} nodes)".format(di_g.number_of_nodes()))
        nodes = list(di_g.nodes())

    candidates = []  # list of possible candidates to connect 'n' to

    if n not in di_g.nodes():
        di_g.add_node(n)

    if algorithm == 'reverse':
        return k_median_reverse_greedy(di_g, n, k, nodes, weight, w_val, pair_dist, node_map, dist_matrix)

    deg_n = nx.degree(di_g, n)  # store degree of node n
    if deg_n == 0:  # 'n' was newly added and does not have neighbors yet
        # create initial connection of 'n' to the network (otherwise n cannot reach any other node):
        n2 = utils.create_initial_connection(di_g, n, weight, w_val, metric='degree')
        if algorithm == 'deg':
            candidates.append(n2)
            k -= 1
            print("Added (permanent) channel from", n, "to", n2, "(initial connection to the network)")
        else:
            print("Added (temporary) channel from", n, "to", n2, "(initial connection to the network)")
        nodes.remove(n2)
    dist = {i: math.inf for i in di_g.nodes()}  # n's distances to all other nodes

    # loop finding remaining k-1 channels:
    for i in range(k):
        min_dist = (math.inf, -1)
        min_dist_list = []
        if weight is None:
            # _, _, _, d = utils.single_source_shortest_paths(di_g, n)
            d = nx.single_source_shortest_path_length(di_g, n)
        else:
            # _, _, _, d = utils.single_source_shortest_paths_weighted(di_g, n, weight)
            d = nx.single_source_dijkstra_path_length(di_g, n, weight=weight)
        for v in nodes:
            sys.stdout.write("\r" + str(v))
            dist.update(d)
            di_g.add_edge(n, v)
            di_g.add_edge(v, n)
            di_g[n][v][weight] = w_val
            di_g[v][n][weight] = w_val
            s = utils.calc_avg_dist(di_g, n, v, dist, weight)  # (faster)
            if s == min_dist[0]:  # another node creates (current) minimal average distance
                min_dist_list.append(v)
            if s < min_dist[0]:  # update minimal average distance
                min_dist = (s, v)
                min_dist_list = [v]

            di_g.remove_edge(n, v)
            di_g.remove_edge(v, n)

        print("")
        # connect to node that creates minimal average distance from 'n' to all other nodes:
        if len(min_dist_list) > 1:
            # if multiple nodes come into question, choose randomly among them:
            #print("NON DETERMINISTIC!!!")
            min_dist = (min_dist[0], random.choice(min_dist_list))
        di_g.add_edge(n, min_dist[1])
        di_g.add_edge(min_dist[1], n)
        di_g[n][min_dist[1]][weight] = w_val
        di_g[min_dist[1]][n][weight] = w_val
        candidates.append(min_dist[1])
        nodes.remove(min_dist[1])
        # print("Added channel from", n, "to", min_dist[1])
    # print("max(dist):", max(dist, key=lambda j: dist[j]), dist[max(dist, key=lambda j: dist[j])])
    # print("Diameter:", nx.diameter(di_g))

    return candidates


def update_sigma_eq(s, t, u, v, sigma, sigma_n):
    """
        update shortest s-t-paths (through 'n') when new edge (u,v) creates new shortest s-t-paths with equal distance
    """
    sigma[s][t] += sigma[s][u] * sigma[v][t]
    sigma_n[s][t] += sigma_n[s][u] * sigma[v][t] + sigma[s][u] * sigma_n[v][t]


def update_sigma_gr(s, t, u, v, sigma, sigma_n):
    """
        update shortest s-t-paths (through 'n') when new edge (u,v) reduces distance between 's' and 't'
    """
    sigma[s][t] = sigma[s][u] * sigma[v][t]
    sigma_n[s][t] = sigma_n[s][u] * sigma[v][t] + sigma[s][u] * sigma_n[v][t]


def find_affected_sources(g, u, v, dist, w):
    """
        pruned BFS rooted in 'u' finding and returning affected sources
    """
    sources = [u]
    vis = {i: False for i in g.nodes()}
    vis[u] = True
    vis[v] = True
    q = [u]
    while q:
        s = q.pop(0)
        for x in g.predecessors(s):
            if not vis[x] and (dist[x][v] >= w + dist[x][u]):
                sources.append(x)
                q.append(x)
                vis[x] = True

    return sources


def update_i_bet(g, n, u, v, dist, sigma, sigma_n, bc_n, weight=None):
    """
        Input:  Graph 'g', new edge (u,v), pairwise distances and number of shortest paths ('dist', 'sigma'),
                number of shortest paths through node 'n' ('sigma_n'), 'n's bc, weighted graph?
        Output: New betweenness centrality of 'n'

        Algorithm 2 [Ber+18]: Update bc[n] after insertion of edge (u,v)
            - use pruned BFS to find affected (s,t)-pairs
            - update dist, sigma and sigma_n matrices
            - use matrices to update bc[n]
    """
    changes = []
    if weight is None:
        w = 1  # unweighted graph -> new edge shortens dist[u][v] to 1
    else:
        w = g[u][v][weight]  # weighted graph

    if dist[u][v] >= w:
        changes.append((u, v))
        if dist[u][v] > w:
            dist[u][v] = w  # update distance between 'u' and 'v'
            update_sigma_gr(u, v, u, v, sigma, sigma_n)
        else:
            update_sigma_eq(u, v, u, v, sigma, sigma_n)

    sources = {i: [] for i in g.nodes()}  # affected sources
    sources[v] = find_affected_sources(g, u, v, dist, w)
    q = [v]  # queue
    vis = {i: False for i in g.nodes()}
    vis[v] = True
    p = {i: -1 for i in g.nodes()}  # predecessors
    p[v] = v

    # bfs rooted in v to find affected targets for u
    while q:
        t = q.pop(0)
        for s in sources[p[t]]:
            if s == u and t == v:  # sigma[u][v] has already been updated above
                continue
            if dist[s][t] >= dist[s][u] + w + dist[v][t]:  # edge (u,v) created new shortest s-t-path
                changes.append((s, t))
                if n != s and n != t:
                    bc_n -= (sigma_n[s][t] / sigma[s][t])  # subtract old betweenness contribution of s-t-paths
                if np.isclose(0.0, (dist[s][t] - (dist[s][u] + w + dist[v][t]))):
                    update_sigma_eq(s, t, u, v, sigma, sigma_n)
                else:
                    update_sigma_gr(s, t, u, v, sigma, sigma_n)
                    dist[s][t] = dist[s][u] + w + dist[v][t]
                """
                if dist[s][t] > dist[s][u] + w + dist[v][t]:  # (u,v) decreases s-t distance
                    update_sigma_gr(s, t, u, v, sigma, sigma_n)
                    dist[s][t] = dist[s][u] + w + dist[v][t]
                else:  # (u,v) creates new shortest s-t-paths (equal distance)
                    update_sigma_eq(s, t, u, v, sigma, sigma_n)
                """
                if n != s and n != t:
                    bc_n += (sigma_n[s][t] / sigma[s][t])  # add new betweenness contribution of s-t-paths
                if t != v:
                    sources[t].append(s)

        # add t's neighbors to queue, if they are also affected targets
        for x in g.successors(t):
            if not vis[x] and (dist[u][x] >= w + dist[v][x]):  # w + dist[v][x]: new dist from 'u' to 'x'
                # Changed pseudocode in the next line!
                if np.isclose(dist[v][x] - (dist[v][t] + dist[t][x]), 0.0):
                    # t's neighbors are only enqueued if 't' is the predecessor of x on the new shortest u-x-path
                    # only then 'x' has a subset of t's affected sources as its own affected sources (Lemma 6.1[Ber+18])
                    q.append(x)
                    vis[x] = True
                    p[x] = t

    return bc_n, changes


def init_matrices(di_g, weight, n):
    """
        initializes matrices 'dist', 'sigma' and 'sigma_n'
    """
    print("Initialize matrices", end="")
    # initialization:
    sigma = {i: {j: 0 for j in di_g.nodes()} for i in di_g.nodes()}
    dist = {i: {j: 0 for j in di_g.nodes()} for i in di_g.nodes()}
    sigma_n = {i: {j: 0 for j in di_g.nodes()} for i in di_g.nodes()}
    # print(".", end="")
    print(".")
    # fill matrices:
    for s in di_g.nodes():
        sys.stdout.write("\r" + str(s))
        if weight is None:
            _, _, o, d = utils.single_source_shortest_paths(di_g, s)
        else:
            _, _, o, d = utils.single_source_shortest_paths_weighted(di_g, s, weight)
            o = {i: o[i] / 2 for i in o}
        sigma[s] = o
        dist[s] = d
    print(".", end="")
    if nx.degree(di_g, n) == 2:  # exactly one neighbor -> no shortest paths go through it
        for u in di_g.nodes():
            if u == n:
                for v in di_g.nodes():
                    sigma_n[u][v] = sigma[u][v]  # shortest paths starting in 'n' also go through it
            else:
                sigma_n[u][n] = sigma[u][n]  # shortest paths ending in 'n' also go through it
    else:  # more than one neighbor
        for u in di_g.nodes():
            for v in di_g.nodes():
                if dist[u][v] == dist[u][n] + dist[n][v]:
                    sigma_n[u][v] = sigma[u][n] * sigma[n][v]  # calculate shortest paths going through 'n'
                elif np.isclose(0, abs(dist[u][v] - (dist[u][n] + dist[n][v]))):
                    if n in nx.dijkstra_path(di_g, u, v, 'fee'):
                        print("check {}-{} again!!!({}, {})".format(u, v, dist[u][v], (dist[u][n] + dist[n][v])))
    print(".")

    return dist, sigma, sigma_n


def greedy_mbi(g, n, k, nodes, weight=None, weight_value=1):
    """
        Input:  graph 'g', new node 'n', number of candidates needed ('k'), possibly weight name + value
        Output: 'k' candidates that 'n' should connect to

        ~> finds 'k' connections that MAXIMIZE BETWEENNESS CENTRALITY of node 'n'
        => greedy approx. algorithm:
            - connect 'n' to node with highest bc (initial connection to the network)
            - initialize 3 matrices:
                + 'dist': pairwise distances
                + 'sigma': number of shortest paths from u to v
                + 'sigma_n': number of shortest paths from u to v that go through n
            - for each new channel: test every possible endpoint and calculate bc
                + do not re-compute bc but use faster update from iBet
            - if name of edge 'weight' is given, create edge with value 'weight_value'

        References (for this and all related procedures):
        [Ber+18] Bergamini, Elisabetta, et al.: Improving the Betweenness Centrality of a Node by Adding Links.
        Journal of Experimental Algorithmics (JEA) 23 (2018): 1-32.
    """
    start = time.perf_counter()
    di_g = g.copy()
    if g.is_multigraph():
        # convert MultiDiGraph to DiGraph (with largest or summed capacity)
        di_g = gc.multi_to_largest_di_graph(g)
        # di_g = gc.multi_to_summed_di_graph(g)

    if not nx.is_strongly_connected(di_g):
        # reduce graph to largest strongly connected component (add 'n' again)
        max_comp = max(nx.strongly_connected_components(di_g), key=len)
        di_g = di_g.subgraph(max_comp).copy()
        if n not in di_g.nodes():
            di_g.add_node(n)  # attributes don't matter as di_g is only temporary

    nodes = list(set(nodes).intersection(set(di_g.nodes())) - {n})
    candidates = []  # list of possible candidates to connect 'n' to

    t0 = time.process_time()
    nodes_reduced = utils.find_stars(di_g)  # reduce 'nodes' list by reducing star sub-structures
    print("exploiting star sub-structures:", len(nodes), "nodes before,", len(nodes_reduced), "nodes now")
    nodes = list(set(nodes).intersection(set(nodes_reduced.keys())))
    t1 = time.process_time()
    print("-> took", t1 - t0, "seconds")

    bc_n = -1  # variable storing betweenness centrality of node 'n'
    deg_n = nx.degree(di_g, n)  # store degree of node n
    if deg_n == 0:  # 'n' was newly added and does not have neighbors yet
        bc_n = 0
        # create initial connection of 'n' to the network (otherwise bc(n) will be 0 after first loop)
        n2 = utils.create_initial_connection(di_g, n, weight, weight_value, metric='degree')
        print("Added channel from", n, "to", n2, "(initial connection to the network)")
        nodes.remove(n2)
        candidates.append(n2)
        if nodes_reduced[n2]:
            nodes_reduced = utils.find_stars(di_g)  # reduce 'nodes' list by reducing star sub-structures
            print("exploiting star sub-structures:", len(nodes), "nodes before,", len(nodes_reduced), "nodes now")
            nodes = set(nodes).intersection(set(nodes_reduced.keys()))
            nodes = list(nodes.union(set(nodes_reduced[n])))

    # initialize matrices:
    dist, sigma, sigma_n = init_matrices(di_g, weight, n)

    if bc_n == -1:  # 'n' was not newly added but already has neighbours -> bc_n has to be calculated
        if deg_n == 2:  # 'n' has only one neighbor (-> in- and out-edge)
            bc_n = 0
        else:
            bc_n = utils.calc_bc(n, sigma, sigma_n)
    # utils.check_path_lengths(di_g, dist, sigma, weight)
    ibet, copying = 0, 0
    t0 = time.time()

    # initialize temporary matrices:
    dist_temp = {i: {j: 0 for j in di_g.nodes()} for i in di_g.nodes()}
    sigma_temp = {i: {j: 0 for j in di_g.nodes()} for i in di_g.nodes()}
    sigma_n_temp = {i: {j: 0 for j in di_g.nodes()} for i in di_g.nodes()}

    utils.copy_matrices(di_g, dist_temp, dist, sigma_temp, sigma, sigma_n_temp, sigma_n)
    t1 = time.time()
    copying += t1 - t0
    # print("Total entries:", len(di_g.nodes()) * len(di_g.nodes()) * 3)

    for i in range(k - 1):
        # connect to node max_bc[0] s.t 'n' has max. bc value max_bc[1]:
        max_bc = [-1, bc_n]
        max_dist_list = []
        for v in nodes:  # possible candidates (neighbors of 'n' excluded)
            changes = []
            sys.stdout.write("\r" + str(v))
            di_g.add_edge(n, v)
            di_g[n][v][weight] = weight_value
            bc_nv, changes = update_i_bet(di_g, n, n, v, dist_temp, sigma_temp, sigma_n_temp, bc_n, weight=weight)
            di_g.add_edge(v, n)
            di_g[v][n][weight] = weight_value
            bc_nv, changes2 = update_i_bet(di_g, n, v, n, dist_temp, sigma_temp, sigma_n_temp, bc_nv, weight=weight)
            changes = list(set(changes).union(set(changes2)))
            if bc_nv == max_bc[1]:
                max_dist_list.append(v)
            if max_bc[1] < bc_nv:  # update max. possible bc (and corresponding node and matrices)
                # max_bc = (v, bc_nv)
                max_bc[0] = v
                max_bc[1] = bc_nv
                max_dist_list = [v]
            # check_path_lengths(di_g, dist_temp, sigma_temp, weight)  # takes time!!!
            if v != nodes[len(nodes) - 1]:
                utils.copy_matrices2(dist_temp, dist, sigma_temp, sigma, sigma_n_temp, sigma_n, changes)
            di_g.remove_edge(n, v)
            di_g.remove_edge(v, n)
        print(" ")
        if max_bc[0] == -1:  # no bc improvement possible
            print("No new channel would improve bc")
            # connect to random node
            max_bc[0] = random.choice(nodes)
        if len(max_dist_list) > 1:
            # if multiple nodes come into question, choose randomly among them:
            max_bc[0] = random.choice(max_dist_list)
            print("Multiple nodes ({}) cause maximal bc improvement ({})! => {} was randomly chosen".format(
                max_dist_list, max_bc[1], max_bc[0]))
        if len(nodes_reduced[max_bc[0]]) > 1:  # node max_bc[0] represents multiple nodes
            max_bc[0] = random.choice(nodes_reduced[max_bc[0]])  # choose random node from this star sub-structure
            if max_bc[0] not in nodes:  # chosen candidate was not in 'nodes' as it was represented by another node
                nodes.append(max_bc[0])  # append to avoid error when 'nodes.remove(max_bc[0])' is executed
            print("Node from star-like sub-structure was chosen!")
            # -> this does not change the BC as all nodes in nodes_reduced[x] are 'equivalent'
        di_g.add_edge(n, max_bc[0])
        di_g.add_edge(max_bc[0], n)
        di_g[n][max_bc[0]][weight] = weight_value
        di_g[max_bc[0]][n][weight] = weight_value
        candidates.append(max_bc[0])
        nodes.remove(max_bc[0])
        bc_n2, _ = update_i_bet(di_g, n, n, max_bc[0], dist, sigma, sigma_n, bc_n, weight=weight)
        _, _ = update_i_bet(di_g, n, max_bc[0], n, dist, sigma, sigma_n, bc_n2, weight=weight)
        t0 = time.time()
        utils.copy_matrices(di_g, dist_temp, dist, sigma_temp, sigma, sigma_n_temp, sigma_n)
        t1 = time.time()
        copying += t1 - t0
        bc_n = max_bc[1]
        if len(nodes_reduced[max_bc[0]]) > 1:  # node max_bc[0] represents multiple nodes
            nodes_reduced = utils.find_stars(di_g)  # reduce 'nodes' list by reducing star sub-structures
            nodes = set(nodes_reduced.keys()) - {n} - set(nx.neighbors(di_g, n))
            nodes = list(nodes.union(set(nodes_reduced[n])))
        # utils.check_path_lengths(di_g, dist, sigma, weight)  # takes time!
        print("Added channel from", n, "to", max_bc[0], "\nNew BC(n) is now: ", bc_n)
        # nx_bc = nx.betweenness_centrality(di_g, normalized=False, weight=weight)[n]  -> just for checking correctness
    #print("greedy_mbi took", ibet, "seconds. Copying took", copying, "seconds")
    #end = time.perf_counter()
    #print("Whole procedure took", end - start, "seconds (perf_counter())")

    return candidates
