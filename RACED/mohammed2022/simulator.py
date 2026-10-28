"""
    Network Simulator
"""

import sys
from random import choice, sample
import time
from queue import PriorityQueue
import utils


def routing(routing_graph, source, target, amount):
    """
        Input:  graph, source/target/amount of the transaction
        Output: list containing route from source to target together with the amount to be transferred (incl. fees)

        ~> finds best route in 'g' to route 'amount' sat from 'source' to 'target:
            - use Dijkstra algorithm to find best route (-> search from target to source)
                - exclude channels w/o sufficient total capacity
                    -> exact shares are (simulated to be) unknown and the tx might therefore still fail due to
                       insufficient capacities in one direction
                - for each node 'n' store [successor, amount, done]
                    + nodes[n][0]: current successor of 'n' on the payment route
                    + nodes[n][1]: #sat 'n' has to receive s.t. 'target' gets 'amount' sat
                    + nodes[n][2]: True if "shortest" route to 'n' has already been found
                    + nodes[n][3]: index of edge (-> multi-edges!) from n to nodes[n][0] to use for routing
            - calculate and return route (empty list if no route exists)
    """

    nodes = dict(routing_graph.nodes())
    for n in nodes:
        nodes[n] = [-1, -1, False, -1]  # [successor, amount, done, channel idx]
    nodes[target][1] = amount

    q = PriorityQueue()
    q.put((0, target))

    while not q.empty():
        u = q.get()  # get first element in priority queue (smallest weight)
        u = u[1]
        nodes[u][2] = True  # done with node u
        if u == source:
            break
        for v in routing_graph.neighbors(u):
            if nodes[v][2]:
                continue  # neighbor v was processed already

            # check which v-u channel has sufficient total capacity and requests minimal fees for routing the tx:
            fee, idx = utils.choose_channel(routing_graph, v, u, nodes[u][1])

            if fee is None:
                continue  # cannot route in v->u direction

            if v == source:
                nodes[v][0] = u
                nodes[v][1] = nodes[u][1]
                nodes[v][3] = idx
                q.put((0, v))  # source found => should be processed next as 'source' does not charge fees (obviously)
                break

            w = nodes[u][1] + fee  # calculate weight
            if (nodes[v][1] == -1) or (nodes[v][1] > (nodes[u][1] + fee)):  # update if new or cheaper route was found
                nodes[v][1] = nodes[u][1] + fee
                nodes[v][0] = u
                nodes[v][3] = idx
                q.put((w, v))

    if nodes[source][0] == -1:
        # print("No route from", source, "to", target, "(with sufficient funds) exists!")
        return []

    # calculate and return route and amount:
    route = [(source, nodes[source][1], nodes[source][3])]
    n = source
    while n != target:
        n = nodes[n][0]  # exchange 'n' by its successor
        route.append((n, nodes[n][1], nodes[n][3]))
    return route


def send_a_to_b(g, a, b, amount):
    """
        Input:  (Multi-)DiGraph 'g', source 'a', target 'b' and amount of transaction
        Output: 0 on success, 1 on failure (due to insufficient capacity)

        ~> sends 'amount' Satoshi from 'a' to 'b'
            - choose edge with highest capacity
            - (assume every a-b edge has corresponding b-a edge)
    """
    if not g.has_edge(a, b):
        print("ERROR! This channel does not exist!")
        return 1
    max_cap = (-1, -1)  # (capacity, index)
    if g.is_multigraph():
        for i in g[a][b]:
            if (g[a][b][i]['capacity'] > max_cap[0]) and not g[a][b][i]['disabled']:  # and not g[b][a][i]['disabled']:
                max_cap = (g[a][b][i]['capacity'], i)
            # if (g[a][b][i]['capacity'] + g[b][a][i]['capacity']) > max_cap[0]:
            #    max_cap = (g[a][b][i]['capacity'] + g[b][a][i]['capacity'], i)
        if g[a][b][max_cap[1]]['capacity'] < amount:
            return 1  # channel does not provide sufficient funds
        g[a][b][max_cap[1]]['capacity'] -= amount
        g[b][a][max_cap[1]]['capacity'] += amount
    else:
        if g[a][b]['capacity'] < amount:
            return 1  # channel does not provide sufficient funds
        g[a][b]['capacity'] -= amount
        g[b][a]['capacity'] += amount

    return 0


def route_tx(g, route, amount):
    """
        Input:  (Multi-)DiGraph, route and amount of transaction
        Output: 0 and the fees for each node of the route on success
                1 and an empty set on failure (due to insufficient capacity)

        ~> sends tx along the given route and stores which node earned which fees
            - the source has a negative fee value as it has to pay the fees
    """
    # check if routing is possible:
    for j in range(len(route) - 1):
        if g.is_multigraph():
            if g[route[j][0]][route[j+1][0]][route[j][2]]['disabled']:
                print("channel is disabled!!!")
                return 1, {}  # tx failed
            if g[route[j][0]][route[j+1][0]][route[j][2]]['capacity'] < route[j+1][1]:
                return 1, {}  # tx failed
        else:
            if g[route[j][0]][route[j+1][0]]['capacity'] < route[j+1][1]:
                return 1, {}  # tx failed

    # do routing:
    i = 0
    fees = {}  # store fees nodes earn/ have to pay (if tx succeeds)
    while i != len(route) - 1:
        if g.is_multigraph():
            g[route[i][0]][route[i+1][0]][route[i][2]]['capacity'] -= route[i+1][1]
            g[route[i+1][0]][route[i][0]][route[i][2]]['capacity'] += route[i+1][1]
        else:
            g[route[i][0]][route[i+1][0]]['capacity'] -= route[i+1][1]
            g[route[i+1][0]][route[i][0]]['capacity'] += route[i+1][1]

        fees[route[i][0]] = route[i][1] - route[i+1][1]
        i += 1
    fees[route[0][0]] = amount - route[0][1]  # fees source has to pay

    return 0, fees  # return fees


def simulate_transactions(g, tx_amt, tx_num, src=None, file=None):
    """
        Input:  graph, transaction amount, number of transactions, fixed source(?), write results to file(?)
        Output: statistics for each node: [tx_attempts, tx_sent, fees_paid, tx_routed, fees_earned]

        ~> simulates 'tx_num' transactions, each of amount 'tx_amt' and records statistics
            - chooses 'source' and 'target' uniformly at random
                - if fixed source 'src' is given, only 'target' is chosen uniformly at random
            - if possible, a direct channel between 'source' and 'target' is chosen (-> no fees)
            - otherwise, the routing process is started (if existent, cheapest route is chosen)
            - statistics are updated accordingly
    """

    t0 = time.process_time()
    results = "Simulating " + str(tx_num) + " transactions of " + str(tx_amt) + " Satoshi each...\n\n"
    nodes = list(g.nodes())
    stats = {}  # statistics for each node about transactions
    for n in g.nodes():
        stats[n] = [0, 0, 0, 0, 0]  # [tx_attempts, tx_sent, fees_paid, tx_routed, fees_earned]

    # execute 'tx_num' consecutive transactions:
    source = src
    if src is not None:  # source of tx is given -> use it for every tx to determine success rate
        nodes.remove(src)
    for i in range(tx_num):
        sys.stdout.write("\rtx: " + str(i))
        if src is None:  # no source is given -> select 'source' and 'target' at random
            s_t = sample(nodes, 2)
            source = s_t[0]
            target = s_t[1]
        else:
            target = choice(nodes)

        results += str(i) + "\t\t" + '{:4}'.format(str(source)) + " --> " + '{:4}'.format(str(target)) + " :\t"

        stats[source][0] += 1

        # test if direct channel (with sufficient capacity) exists:
        if g.has_edge(source, target):
            tx_failed = 1
            for j in g[source][target]:  # loop through all channels between 'source' and 'target'
                if not g[source][target][j]['disabled']:
                    if g[source][target][j]['capacity'] >= tx_amt:  # ('source' knows its shares of the channel)
                        tx_failed = send_a_to_b(g, source, target, tx_amt)
                        if not tx_failed:
                            stats[source][1] += 1
                            results += "Success (direct channel)\n"
                            # print(tx_amt, "sat were successfully sent from", source, "to", target)
                        break
            if not tx_failed:
                continue  # ... with next transaction

        # a faster option here would be to simply choose the shortest (=cheapest) path in the fee graph, but as outlined
        # in the thesis, this is not always accurate (e.g. first channel on route does not charge fees)

        # do routing on graph 'g':
        path = routing(g, source, target, tx_amt)

        if not path:
            results += "Failure (no sufficiently funded route exists)\n"
            continue
        failed, fees = route_tx(g, path, tx_amt)
        if failed:
            # route exists, but routing failed as exact shares of channel balances are unknown
            results += "Failure\n"
            # print("Transaction failed (", tx_amt, "from", source, "to", target, ")")
            continue
        else:
            stats[source][1] += 1
            stats[source][2] += abs(fees[source])
            for j in range(1, len(fees)):
                stats[path[j][0]][3] += 1  # this node successfully routed a tx
                stats[path[j][0]][4] += fees[path[j][0]]  # this node earned routing fees
            results += "Success\t Route: {}\n".format(path)
            # print(tx_amt, "sat were successfully sent from", source, "to", target)
    t1 = time.process_time()
    sys.stdout.write("\r")
    print(tx_num, " transactions took:", int(t1-t0), "seconds")
    # print(results)
    results += "\n---------------STATISTICS [tx_attempts, tx_sent, fees_paid, tx_routed, fees_earned]---------------\n"
    results += "(statistics of nodes are not listed if they equal [0,0,0,0,0])\n"
    for n in g.nodes():
        if stats[n] != [0, 0, 0, 0, 0]:
            results += '{:5}'.format(str(n)) + str(stats[n]) + "\n"
    results += "\n"

    if file is not None:
        with open(file, "a", encoding='utf8') as f:  # write to file
            print("writing results to file: ", file)
            f.write(results)

    return stats
