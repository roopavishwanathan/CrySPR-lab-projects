import networkx as nx
import numpy as np
import multiprocessing as mp
import math
import utils
import sys
import time
import random
import graph_creation as gc
import autopilot as ap
import psutil


# global variables (used by 'k-median_parallel'):
min_dist_global = (math.inf, -1)
min_dist_list_global = []

# global variables (used by 'greedy_mbi_parallel'):
dist_global = None
sigma_global = None
sigma_n_global = None
max_bc_global = [-1, 0]
max_bc_list_global = []


def update_dist_weighted2(g, v, dist, w, val):
    """
        ~> same as 'update_dist_weighted' in 'utils.py' but u-v edges have not been added to 'g' (are just assumed
        to exist) -> assumed weight of that edge is given as input 'val'
    """
    if dist[v] > val:  # new edge changed distance to v
        dist[v] = val
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


def find_best_node(di_g, node_set, n, d, weight, w_val):
    """
        ~> similar to last part of 'k-median' in 'autopilot.py' but works on a given 'node_set' and uses
        'update_dist_weighted2' in order to allow parallelization and a potential performance speed-up
    """
    dist = {i: math.inf for i in di_g.nodes()}  # n's distances to all other nodes
    min_dist = (math.inf, -1)  # stores 'local' optimum (for given 'node_set')
    min_dist_list = []
    for v in node_set:
        sys.stdout.write("\r" + str(v))
        dist.update(d)  # reset 'dist' vector
        update_dist_weighted2(di_g, v, dist, weight, w_val)
        s = sum(dist.values())
        if s == min_dist[0]:  # another node creates (current) minimal average distance
            min_dist_list.append(v)
        if s < min_dist[0]:  # update minimal average distance
            min_dist = (s, v)
            min_dist_list = [v]
    if len(min_dist_list) > 1:
        # if multiple nodes come into question, choose randomly among them:
        print("non deterministic...")
        min_dist = (min_dist[0], random.choice(min_dist_list))

    return min_dist


def store_best_node(result):
    """
        ~> callback function for 'k-median_parallel' that takes the 'local' results from 'find_best_node' for all node
        subsets as input and stores the 'global optimum' in the global variable 'min_dist_global'
        (uses 'min_dist_list_global' for storing if various nodes cause optimal result)
    """
    global min_dist_global
    global min_dist_list_global
    if result[0] == min_dist_global[0]:  # another node creates (current) minimal average distance
        min_dist_list_global.append(result[1])
        print("min_dist_list_global:", min_dist_list_global)
    if result[0] < min_dist_global[0]:  # update minimal average distance
        min_dist_global = result
        min_dist_list_global = [result[1]]


def k_median_parallel(g, n, k, nodes, algorithm=None, weight=None, w_val=None, c=None):
    """
        Input: graph 'g', node 'n', parameter 'k', 'nodes' to choose from, 'weight' and value
                -> if 'algorithm' == deg: add permanent channel to node with highest degree
        Output: 'k' candidates that 'n' should connect to

        ~> parallel version of (forward greedy) k-median algorithm in 'autopilot.py'
    """
    start = time.perf_counter()
    print("starting k-median_parallel algorithm...", end=" ")
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

    # loop finding remaining k-1 channels:
    for i in range(k):
        # reset global 'variables':
        global min_dist_global
        global min_dist_list_global
        min_dist_global = (math.inf, -1)
        min_dist_list_global = []

        if weight is None:
            d = nx.single_source_shortest_path_length(di_g, n)
        else:
            d = nx.single_source_dijkstra_path_length(di_g, n, weight=weight)

        cpus = c
        if c is None:
            cpus = mp.cpu_count()
        # Init multiprocessing.Pool()
        pool = mp.Pool(cpus)

        # split 'nodes' into 'cpus' (nearly equally long) separate lists:
        node_split = []
        last_idx = 0
        for loop in range(1, cpus+1):
            if loop == cpus:
                node_split.append(nodes[last_idx:])  # put all remaining nodes into this set
            else:
                new_idx = last_idx + int(len(nodes) / cpus)
                node_split.append(nodes[last_idx:new_idx])
                last_idx = new_idx

        for node_subset in node_split:
            pool.apply_async(find_best_node, args=(di_g, node_subset, n, d.copy(), weight, w_val),
                             callback=store_best_node)

        pool.close()
        pool.join()  # postpones the execution of next line until all processes in the queue are done
        print("")

        # connect to node that creates minimal average distance from 'n' to all other nodes:
        if len(min_dist_list_global) > 1:
            # if multiple nodes come into question, choose randomly among them:
            print("NON DETERMINISTIC!!!")
            min_dist_global = (min_dist_global[0], random.choice(min_dist_list_global))
        # print(min_dist_global)
        # add edge permanently:
        di_g.add_edge(n, min_dist_global[1])
        di_g.add_edge(min_dist_global[1], n)
        di_g[n][min_dist_global[1]][weight] = w_val
        di_g[min_dist_global[1]][n][weight] = w_val
        candidates.append(min_dist_global[1])
        nodes.remove(min_dist_global[1])

    print("took: {} seconds".format(time.perf_counter() - start))
    return candidates


def update_global_matrices(di_g, weight, n):
    """
        updates (global) matrices 'dist_global', 'sigma_global' and 'sigma_n_global'
        ~> avoids re-calculation of pairwise distances and numbers of shortest paths after 'n' was added to 'di_g' w/
           only one channel (-> therefore, 'n' does not affect the pairwise shortest paths of all other nodes yet)
           => sigma_n_global has to be reset and filled with the data for the new node 'n'
    """
    # TODO -> this does not seem to work correctly yet!
    global dist_global
    global sigma_global
    global sigma_n_global
    if len(dist_global) != di_g.number_of_nodes() - 1 or nx.degree(di_g, n) != 2:
        # no easy update (after n was added) is possible:
        # more than n's entries are missing
        # OR n has more than one neighbor (-> might influence other shortest paths -> more entries have to be changed)
        return 1
    if weight is None:
        _, _, o, d = utils.single_source_shortest_paths(di_g, n)
    else:
        _, _, o, d = utils.single_source_shortest_paths_weighted(di_g, n, weight)
        o = {i: int(o[i] / 2) for i in o}  # -> cast to 'int' to save memory (no information loss!)
    sigma_global[n] = o
    dist_global[n] = d
    sigma_n_global = sigma_n_global = {i: {j: 0 for j in di_g.nodes()} for i in di_g.nodes()}
    v = list(nx.neighbors(di_g, n))[0]  # -> n's initial connection
    for s in di_g.nodes():
        sigma_n_global[n][s] = sigma_global[n][s]  # shortest paths starting in 'n' also go through it
        if s != n:
            # all shortest paths to 'n' go through 'v' -> makes dist/sigma calculations easier
            dist_global[s][n] = dist_global[s][v] + di_g[v][n][weight]
            sigma_global[s][n] = sigma_global[s][v]
            sigma_n_global[s][n] = sigma_global[s][n]  # shortest paths ending in 'n' also go through it

    return 0


def init_global_matrices_parallel(di_g, weight, n, c):
    """
        initializes (global) matrices 'dist_global', 'sigma_global' and 'sigma_n_global' using 'c' parallel processes
    """
    cpus = c
    if c is None:
        cpus = mp.cpu_count()
    pool = mp.Pool(cpus)

    # split 'nodes' into 'cpus' (nearly equally long) separate lists:
    node_split = []
    last_idx = 0
    nodes = list(di_g.nodes())
    for loop in range(1, cpus + 1):
        if loop == cpus:
            node_split.append(nodes[last_idx:])  # put all remaining nodes into this set
        else:
            new_idx = last_idx + int(len(nodes) / cpus)
            node_split.append(nodes[last_idx:new_idx])
            last_idx = new_idx

    #for node_subset in node_split:
    # TODO


def init_global_matrices(di_g, weight, n):
    """
        initializes (global) matrices 'dist_global', 'sigma_global' and 'sigma_n_global'
    """
    start = time.time()
    # initialization:
    global dist_global
    global sigma_global
    global sigma_n_global
    # if dist_global is not None:
        # if not update_global_matrices(di_g, weight, n):
            # matrices updated successfully
            # return

    print("Initializing matrices...")
    sigma_global = {i: {j: 0 for j in di_g.nodes()} for i in di_g.nodes()}
    dist_global = {i: {j: 0. for j in di_g.nodes()} for i in di_g.nodes()}
    sigma_n_global = {i: {j: 0 for j in di_g.nodes()} for i in di_g.nodes()}
    # fill matrices:
    for s in di_g.nodes():
        sys.stdout.write("\r" + str(s))
        if weight is None:
            _, _, o, d = utils.single_source_shortest_paths(di_g, s)
        else:
            _, _, o, d = utils.single_source_shortest_paths_weighted(di_g, s, weight)
            o = {i: int(o[i] / 2) for i in o}  # -> cast to 'int' to save memory (no information loss!)
        sigma_global[s] = o
        dist_global[s] = d
    print(" ")
    if nx.degree(di_g, n) == 2:  # exactly one neighbor -> no shortest paths go through it
        for u in di_g.nodes():
            if u == n:
                for v in di_g.nodes():
                    sigma_n_global[u][v] = sigma_global[u][v]  # shortest paths starting in 'n' also go through it
            else:
                sigma_n_global[u][n] = sigma_global[u][n]  # shortest paths ending in 'n' also go through it
    else:  # more than one neighbor
        for u in di_g.nodes():
            for v in di_g.nodes():
                if dist_global[u][v] == dist_global[u][n] + dist_global[n][v]:
                    sigma_n_global[u][v] = sigma_global[u][n] * sigma_global[n][v]  # calculate shortest paths going through 'n'
                # elif np.isclose(dist_global[u][v], (dist_global[u][n] + dist_global[n][v])):
                elif np.isclose(0, abs(dist_global[u][v] - (dist_global[u][n] + dist_global[n][v]))):
                    print("blaa")
                    if n in nx.dijkstra_path(di_g, u, v, 'fee'):
                        print("check {}-{} again!!!({}, {})".format(u, v, dist_global[u][v], (dist_global[u][n] + dist_global[n][v])))
    print("...took", time.time() - start)


def memory_usage():
    current_process = psutil.Process()
    memory = current_process.memory_info().rss
    print(int(memory / (1024 * 1024)), "MB")


def find_affected_sources2(g, u, v, dist, dist_new, w):
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
            d1 = dist[x][v]
            d2 = dist[x][u]
            if (x, v) in dist_new:
                d1 = dist_new[(x, v)]
            if (x, u) in dist_new:
                d2 = dist_new[(x, u)]
            if not vis[x] and (d1 >= w + d2):
                sources.append(x)
                q.append(x)
                vis[x] = True

    return sources


def update_i_bet2(g, n, u, v, dist, sigma, sigma_n, dist_new, sigma_new, sigma_n_new, bc, weight=None):
    """
        ~> same as 'update_i_bet' in 'autopilot.py', but without changing the matrices 'dist', 'sigma' and 'sigma_n'
    """
    if weight is None:
        w = 1  # unweighted graph -> new edge shortens dist[u][v] to 1
    else:
        w = weight  # g[u][v][weight]  # weighted graph

    if (u, v) in dist_new:
        print("ohoh... ")
    if dist[u][v] >= w:
        if dist[u][v] > w:
            dist_new[(u, v)] = w  # update distance between 'u' and 'v'
            sigma_new[(u, v)] = sigma[u][u] * sigma[v][v]
            sigma_n_new[(u, v)] = sigma_n[u][u] * sigma[v][v] + sigma[u][u] * sigma_n[v][v]
            # update_sigma_gr(u, v, u, v, sigma, sigma_n)
        else:
            sigma_new[(u, v)] = sigma[u][v] + (sigma[u][u] * sigma[v][v])
            sigma_n_new[(u, v)] = sigma_n[u][v] + (sigma_n[u][u] * sigma[v][v] + sigma[u][u] * sigma_n[v][v])
            # update_sigma_eq(u, v, u, v, sigma, sigma_n)

    sources = {i: [] for i in g.nodes()}  # affected sources
    sources[v] = find_affected_sources2(g, u, v, dist, dist_new, w)
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
            """
                work with values from '_new' dicts if they exist (i.e. were previously updated), else use global dicts
                -> dist_curr = [d[s][t], d[s][u], d[v][t]] (others defined analogously)
            """
            dist_curr = [dist_new[(a, b)] if (a, b) in dist_new else dist[a][b] for (a, b) in [(s, t), (s, u), (v, t)]]
            sigma_curr = [sigma_new[(a, b)] if (a, b) in sigma_new else sigma[a][b] for (a, b) in
                          [(s, t), (s, u), (v, t)]]
            sigma_n_curr = [sigma_n_new[(a, b)] if (a, b) in sigma_n_new else sigma_n[a][b] for (a, b) in
                            [(s, t), (s, u), (v, t)]]
            if dist_curr[0] >= dist_curr[1] + w + dist_curr[2]:  # edge (u,v) created new shortest s-t-path
                if n != s and n != t:
                    bc -= (sigma_n_curr[0] / sigma_curr[0])  # subtract old betweenness contribution of s-t-paths
                if np.isclose(0.0, (dist_curr[0] - (dist_curr[1] + w + dist_curr[2]))):
                    # update_sigma_eq(s, t, u, v, sigma, sigma_n)
                    if (s, t) in sigma_new:
                        sigma_new[(s, t)] += sigma_curr[1] * sigma_curr[2]
                    else:
                        sigma_new[(s, t)] = sigma_curr[0] + sigma_curr[1] * sigma_curr[2]
                    sigma_curr = [sigma_new[(a, b)] if (a, b) in sigma_new else sigma[a][b] for (a, b) in
                                  [(s, t), (s, u), (v, t)]]  # update (-> is it necessary?)
                    if (s, t) in sigma_n_new:
                        sigma_n_new[(s, t)] += sigma_n_curr[1] * sigma_curr[2] + sigma_curr[1] * sigma_n_curr[2]
                    else:
                        sigma_n_new[(s, t)] = sigma_n_curr[0] + \
                                              (sigma_n_curr[1] * sigma_curr[2] + sigma_curr[1] * sigma_n_curr[2])
                else:
                    # update_sigma_gr(s, t, u, v, sigma, sigma_n)
                    sigma_new[(s, t)] = sigma_curr[1] * sigma_curr[2]
                    sigma_curr = [sigma_new[(a, b)] if (a, b) in sigma_new else sigma[a][b] for (a, b) in
                                  [(s, t), (s, u), (v, t)]]  # update (-> is it necessary?)
                    sigma_n_new[(s, t)] = sigma_n_curr[1] * sigma_curr[2] + sigma_curr[1] * sigma_n_curr[2]
                    dist_new[(s, t)] = dist_curr[1] + w + dist_curr[2]
                if n != s and n != t:
                    bc += (sigma_n_new[(s, t)] / sigma_new[(s, t)])  # add new betweenness contribution of s-t-paths
                if t != v:
                    sources[t].append(s)
            # old code below:
            """if dist[s][t] >= dist[s][u] + w + dist[v][t]:  # edge (u,v) created new shortest s-t-path
                changes.append((s, t))
                if n != s and n != t:
                    bc_n -= (sigma_n[s][t] / sigma[s][t])  # subtract old betweenness contribution of s-t-paths
                if np.isclose(0.0, (dist[s][t] - (dist[s][u] + w + dist[v][t]))):
                    # update_sigma_eq(s, t, u, v, sigma, sigma_n)
                    sigma[s][t] += sigma[s][u] * sigma[v][t]
                    sigma_n[s][t] += sigma_n[s][u] * sigma[v][t] + sigma[s][u] * sigma_n[v][t]
                else:
                    # update_sigma_gr(s, t, u, v, sigma, sigma_n)
                    dist[s][t] = dist[s][u] + w + dist[v][t]
                if n != s and n != t:
                    bc_n += (sigma_n[s][t] / sigma[s][t])  # add new betweenness contribution of s-t-paths
                if t != v:
                    sources[t].append(s)"""

        # add t's neighbors to queue, if they are also affected targets
        for x in g.successors(t):
            d_curr = [dist_new[(a, b)] if (a, b) in dist_new else dist[a][b] for (a, b) in [(u,x), (v,x), (v,t), (t,x)]]
            if not vis[x] and (d_curr[0] >= w + d_curr[1]):  # w + dist[v][x]: new dist from 'u' to 'x'
                # Changed pseudocode in the next line!
                if np.isclose(d_curr[1] - (d_curr[2] + d_curr[3]), 0.0):
                    # t's neighbors are only enqueued if 't' is the predecessor of x on the new shortest u-x-path
                    # only then 'x' has a subset of t's affected sources as its own affected sources (Lemma 6.1[Ber+18])
                    q.append(x)
                    vis[x] = True
                    p[x] = t
            # old code below:
            """if not vis[x] and (dist[u][x] >= w + dist[v][x]):  # w + dist[v][x]: new dist from 'u' to 'x'
                # Changed pseudocode in the next line!
                if np.isclose(dist[v][x] - (dist[v][t] + dist[t][x]), 0.0):
                    # t's neighbors are only enqueued if 't' is the predecessor of x on the new shortest u-x-path
                    # only then 'x' has a subset of t's affected sources as its own affected sources (Lemma 6.1[Ber+18])
                    q.append(x)
                    vis[x] = True
                    p[x] = t"""

    return bc


def find_best_node2(di_g, n, node_set, bc_n, weight_value, dist, sigma, sigma_n):
    """
        ~> similar to last part of 'greedy_mbi' in 'autopilot.py' but works on a given 'node_set' in order to allow
        parallelization and a potential performance speed-up
        (does not change matrices or graph!)
    """
    max_bc = (-1, 0)
    max_bc_list = []
    for v in node_set:
        sys.stdout.write("\r" + str(v))
        dist_temp, sigma_temp, sigma_n_temp = {}, {}, {}
        bc_nv = update_i_bet2(di_g, n, n, v, dist, sigma, sigma_n, dist_temp, sigma_temp, sigma_n_temp, bc_n,
                              weight=weight_value)
        bc_nv = update_i_bet2(di_g, n, v, n, dist, sigma, sigma_n, dist_temp, sigma_temp, sigma_n_temp, bc_nv,
                              weight=weight_value)
        # print(v, bc_nv)
        if bc_nv == max_bc[1]:
            max_bc_list.append(v)
        if max_bc[1] < bc_nv:  # update max. possible bc (and corresponding node and matrices)
            max_bc = (v, bc_nv)
            max_bc_list = [v]

    return max_bc


def store_best_node2(result):
    """
        ~> callback function for 'greedy_mbi_parallel' that takes the 'local' results from 'find_best_node2' for all
        node subsets as input and stores the 'global optimum' in the global variable 'max_bc'
        (uses 'max_bc_list' for storing if various nodes cause optimal result)
    """
    global max_bc_global
    global max_bc_list_global
    if result[1] == max_bc_global[1]:  # another node creates (current) maximal bc
        max_bc_list_global.append(result[0])
        print("max_bc_list_global:", max_bc_list_global)
    if result[1] > max_bc_global[1]:  # update maximal bc
        max_bc_global = [result[0], result[1]]
        max_bc_list_global = [result[0]]


def greedy_mbi_parallel(g, n, k, nodes, weight=None, weight_value=1, c=None):
    """
        Input:  graph 'g', new node 'n', number of candidates needed ('k'), possibly weight name + value
        Output: 'k' candidates that 'n' should connect to

        ~> parallel version of 'greedy_mbi' algorithm in 'autopilot.py'
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
    print("exploiting star sub-structures:", len(nodes), "nodes before,", len(nodes_reduced), "nodes now", end=" ")
    nodes = list(set(nodes).intersection(set(nodes_reduced.keys())))
    print("-> took", time.process_time() - t0, "seconds")

    bc_n = -1  # variable storing betweenness centrality of node 'n'
    deg_n = nx.degree(di_g, n)  # store degree of node n
    if deg_n == 0:  # 'n' was newly added and does not have neighbors yet
        bc_n = 0  # 'n' cannot route payments yet!
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
    global dist_global
    global sigma_global
    global sigma_n_global
    init_global_matrices(di_g, weight, n)

    if bc_n == -1:  # 'n' was not newly added but already has neighbours -> bc_n has to be calculated
        print("calc node's bc...")
        if deg_n == 2:  # 'n' has only one neighbor (-> in- and out-edge)
            bc_n = 0
        else:
            bc_n = utils.calc_bc(n, sigma_global, sigma_n_global)

    for i in range(k - 1):
        # reset global 'variables':
        global max_bc_global
        global max_bc_list_global
        max_bc_global = [-1, 0]
        max_bc_list_global = []

        cpus = c
        if c is None:
            cpus = mp.cpu_count()
        pool = mp.Pool(cpus)

        # split 'nodes' into 'cpus' (nearly equally long) separate lists:
        node_split = []
        last_idx = 0
        for loop in range(1, cpus + 1):
            if loop == cpus:
                node_split.append(nodes[last_idx:])  # put all remaining nodes into this set
            else:
                new_idx = last_idx + int(len(nodes) / cpus)
                node_split.append(nodes[last_idx:new_idx])
                last_idx = new_idx

        for node_subset in node_split:
            pool.apply_async(find_best_node2, args=(di_g, n, node_subset, bc_n, weight_value, dist_global, sigma_global,
                                                    sigma_n_global), callback=store_best_node2)

        pool.close()
        pool.join()  # postpones the execution of next line until all processes in the queue are done
        print("")

        if max_bc_global[0] == -1:  # no bc improvement possible
            print("No new channel would improve bc")
            max_bc_global[0] = random.choice(nodes)  # connect to random node
        if len(max_bc_list_global) > 1:
            # if multiple nodes come into question, choose randomly among them:
            max_bc_global[0] = random.choice(max_bc_list_global)
            print("Multiple nodes ({}) cause maximal bc improvement ({})! => {} was randomly chosen".format(
                max_bc_list_global, max_bc_global[1], max_bc_global[0]))
        if len(nodes_reduced[max_bc_global[0]]) > 1:  # node max_bc[0] represents multiple nodes
            max_bc_global[0] = random.choice(nodes_reduced[max_bc_global[0]])  # choose random node from this star sub-structure
            if max_bc_global[0] not in nodes:  # chosen candidate was not in 'nodes' as it was represented by another node
                nodes.append(max_bc_global[0])  # append to avoid error when 'nodes.remove(max_bc[0])' is executed
            print("Node from star-like sub-structure was chosen!")
            # -> this does not change the BC as all nodes in nodes_reduced[x] are 'equivalent'
        di_g.add_edge(n, max_bc_global[0])
        di_g.add_edge(max_bc_global[0], n)
        di_g[n][max_bc_global[0]][weight] = weight_value
        di_g[max_bc_global[0]][n][weight] = weight_value
        candidates.append(max_bc_global[0])
        nodes.remove(max_bc_global[0])
        # update matrices:
        bc_n2, _ = ap.update_i_bet(di_g, n, n, max_bc_global[0], dist_global, sigma_global, sigma_n_global, bc_n,
                                   weight=weight)
        _, _ = ap.update_i_bet(di_g, n, max_bc_global[0], n, dist_global, sigma_global, sigma_n_global, bc_n2,
                               weight=weight)
        bc_n = max_bc_global[1]
        """if len(nodes_reduced[max_bc[0]]) > 1:  # node max_bc[0] represents multiple nodes
            nodes_reduced = utils.find_stars(di_g)  # reduce 'nodes' list by reducing star sub-structures
            nodes = set(nodes_reduced.keys()) - {n} - set(nx.neighbors(di_g, n))
            nodes = list(nodes.union(set(nodes_reduced[n])))"""
        print("Added channel from", n, "to", max_bc_global[0], "\nNew BC(n) is now: ", bc_n)
        # nx_bc = nx.betweenness_centrality(di_g, normalized=False, weight=weight)[n]  -> just for checking correctness
        # print("NEW BC: ", nx_bc)
    end = time.perf_counter()
    print("Whole procedure took", end - start, "seconds (perf_counter())")

    return candidates
