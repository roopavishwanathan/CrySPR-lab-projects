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
        #print(nodes[n])
    nodes[target][1] = amount
    #print("iam here")
    #print(nodes[target])

    q = PriorityQueue()
    q.put((0, target))
    #print(q.get())

    while not q.empty():
        print("-----------------------------------------------")
        u = q.get()  # get first element in priority queue (smallest weight)
        print(u)

        u = u[1]
        nodes[u][2] = True  # done with node u
        print(nodes[u])
        print("------------------------------------------------")
        if u == source:
            break
        print("*************************************************")
        print(u)
        for v in routing_graph.neighbors(u):
            print(v)
            if nodes[v][2]:
                print("be here")
                print(nodes[v])
                continue  # neighbor v was processed already

            # check which v-u channel has sufficient total capacity and requests minimal fees for routing the tx:
            fee, idx = utils.choose_channel(routing_graph, v, u, nodes[u][1])

            if fee is None:
                continue  # cannot route in v->u direction

            if v == source:
                print("be source")
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


def send_tx(self, s=None):

    #sys.stdout.write("\rNOW:" + str(self.env.now))
    source = choice(list(self.g.nodes()))  # source of transaction -> not necessarily in largest conn. component
    # source = choice(list(self.g_f.nodes()))  # source of transaction
    if s is not None:
        source = s
    target = choice(list(set(self.g.nodes()) - {source}))  # recipient of transaction -> see above
    # target = choice(list(set(self.g_f.nodes()) - {source}))  # recipient of transaction
    res = 'T {:4} --{}--> {:4} : '.format(source, self.tx_amt, target)

    self.stats[source][0] += 1  # 'source' attempts to send a tx

    # test if direct channel (with sufficient capacity) exists:
    if self.g.has_edge(source, target):
        tx_failed = 1
        for j in self.g[source][target]:
            if not self.g[source][target][j]['disabled']:
                if self.g[source][target][j]['capacity'] >= tx_amt:
                    tx_failed = send_a_to_b(g, source, target, tx_amt)
                    if not tx_failed:
                        self.stats[source][1] += 1
                        res += "S (direct channel)\n"
                        # print(self.tx_amt, "sat were successfully sent from", source, "to", target)
                    break
        if not tx_failed:
            return res

        # a faster option here would be to simply choose the shortest (=cheapest) path in the fee graph, but as
        # outlined in the thesis, this is not always accurate (e.g. first channel on route does not charge fees)

        # do routing on graph 'g':


    path = routing(g, source, target, tx_amt)

    if not path:
        # print("Failure (no sufficiently funded route exists)")
        res += "F (no sufficiently funded route exists)\n"
        return res
    failed, fees = route_tx(g, path, self.tx_amt)
    if failed:
        # route exists, but routing failed as exact shares of channel balances are unknown
        res += "F (temporary channel failure)\n"
        # print("Transaction failed (", self.tx_amt, "from", source, "to", target, ")")
    else:
        self.stats[source][1] += 1
        self.stats[source][2] += abs(fees[source])
        for j in range(1, len(fees)):
            self.stats[path[j][0]][3] += 1  # this node successfully routed a tx
            self.stats[path[j][0]][4] += fees[path[j][0]]  # this node earned routing fees
        res += "S (Route: {})\n".format(path)
    # print(self.tx_amt, "sat were successfully sent from", source, "to", target)

    return res


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
    print (routing(g, source, target, 100))
creategraph()