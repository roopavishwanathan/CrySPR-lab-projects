import constants as c
import random
import bisect
import ast
import time
from Node import ChordNode, between
from collections import OrderedDict
import rsa
import networkx as nx
import graph_creation as gc
from random import choice, seed
from queue import PriorityQueue
import jordan
import numpy as np
import sys
import networkx as nx
import os
sys.setrecursionlimit(2000)

#@title function : load / save pickle_obj

### pickle

import bz2
import pickle
# !pip install pickle5
import pickle5
import _pickle as cPickle
import os
import numpy as np

def save_obj(obj, name):
    with open(name + '.pkl', 'wb') as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)

def load_obj(name):
    with open(name + '.pkl', 'rb') as f:
        return pickle.load(f)

def load_obj_pkl5(name):
    with open(name + '.pkl', 'rb') as f:
        return pickle5.load(f)

def compressed_pickle(data,title):
  with bz2.BZ2File(title + '.pbz2', 'w') as f: 
    cPickle.dump(data, f)

def decompress_pickle(file):
 data = bz2.BZ2File(file+'.pbz2', 'rb')
 data = cPickle.load(data)
 return data



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
        # print("-----------------------------------------------")
        u = q.get()  # get first element in priority queue (smallest weight)
        # print(u)

        u = u[1]
        nodes[u][2] = True  # done with node u
        # print(nodes[u])
        # print("------------------------------------------------")
        if u == source:
            break
        # print("*************************************************")
        # print(u)
        for v in routing_graph.neighbors(u):
            # print(v)
            if nodes[v][2]:
                # print("be here")
                # print(nodes[v])
                continue  # neighbor v was processed already

            # check which v-u channel has sufficient total capacity and requests minimal fees for routing the tx:
            fee, idx = jordan.choose_channel(routing_graph, v, u, nodes[u][1])

            if fee is None:
                continue  # cannot route in v->u direction

            if v == source:
                # print("be source")
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
def send_tx(g,source,target,tx_amt):
    stats={}
    for n in g.nodes():
        stats[n] = [0, 0, 0, 0, 0]

        #sys.stdout.write("\rNOW:" + str(self.env.now))
    #source = choice(list(self.g.nodes()))  # source of transaction -> not necessarily in largest conn. component
    # source = choice(list(self.g_f.nodes()))  # source of transaction
    #if s is not None:
        #source = s
    #target = choice(list(set(self.g.nodes()) - {source}))  # recipient of transaction -> see above
    # target = choice(list(set(self.g_f.nodes()) - {source}))  # recipient of transaction
    res = 'T {:4} --{}--> {:4} : '.format(source, tx_amt, target)

    stats[source][0] += 1  # 'source' attempts to send a tx

    # test if direct channel (with sufficient capacity) exists:
    if g.has_edge(source, target):

        tx_failed = 1
        for j in g[source][target]:
            if not g[source][target][j]['disabled']:
                if g[source][target][j]['capacity'] >= tx_amt:
                    tx_failed = send_a_to_b(g, source, target, tx_amt)
                    if not tx_failed:
                        stats[source][1] += 1
                        res += "S (direct channel)\n"
                        # print(self.tx_amt, "sat were successfully sent from", source, "to", target)
                    break
        if not tx_failed:
            return res

        # a faster option here would be to simply choose the shortest (=cheapest) path in the fee graph, but as
        # outlined in the thesis, this is not always accurate (e.g. first channel on route does not charge fees)

        # do routing on graph 'g':


    path = routing(g, source, target, tx_amt)
    print("Length of path:" + str(path))

    if not path:
        # print("Failure (no sufficiently funded route exists)")
        res += "F (no sufficiently funded route exists)\n"
        return res
    failed, fees = route_tx(g, path, tx_amt)
    
    if failed: ### to fix!!!
        # route exists, but routing failed as exact shares of channel balances are unknown
        res += "F (temporary channel failure)\n"
        # print("Transaction failed (", self.tx_amt, "from", source, "to", target, ")")
    
    else:
        stats[source][1] += 1
        stats[source][2] += abs(fees[source])
        for j in range(1, len(fees)):
            stats[path[j][0]][3] += 1  # this node successfully routed a tx
            stats[path[j][0]][4] += fees[path[j][0]]  # this node earned routing fees
        res += "S (Route: {})\n".format(path)
    # print(self.tx_amt, "sat were successfully sent from", source, "to", target)

    return res

def creategraph(nodelist,txamount):
    """
        Input:  'strategy' that is to be evaluated for k from 'k_start' to k=15

        ~> starts autopilot and simulator for given strategy and saves results
    """
    # folder:
    #file = './simulation_results/' + str(strategy)

    # open file and create multigraph model of the Lightning Network:
    # g = gc.parse_multi_di_graph('./lngraph_2020_05_01__10_00.json', exclude_disabled=False)
    # baseline_transactions(g)
    print("-----------------Reading Lighting Network -----------------------------")
    print(nodelist)
    g = decompress_pickle('Testing_graph')
    # g = gc.parse_multi_di_graph('./lngraph_2020_05_01__10_00.json', exclude_disabled=True)  # EXCLUDE DISABLED EDGES!
    print("G has {} nodes and {} edges (={} active channels)".format(g.number_of_nodes(), g.number_of_edges(),
                                                                     g.number_of_edges() / 2))
    source = choice(list(g.nodes()))
    target = choice(list(set(nodelist) - {source}))
    print("Iam herereeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee")
    print(source)
    print(target)
    print(send_tx(g,source,target,txamount))
    print("iamkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkk")
    #if nx.has_path(g,source,target):
     #   print([p for p in nx.all_shortest_paths(g, source=source, target=target, weight="capacity", method='dijkstra')])
    #else:
      #  print("Sorry No path")
    #print(nx.degree_centrality(g))
    #print(nx.voterank(g,10))
    #print(nx.maximum_flow_value(g, source, target, capacity='capacity'))

 
class ChordRing:
    '''
    The overarching system that keeps track of the nodes. It contains the following:
    nodeDict: Dictionary that maps IDs to Nodes
    nodeList: List of Nodes in numerical order of their IDs.
    curr_node_ind: Index that keeps track of which node is next to process RPC.
    num_node: Keeps track of how many nodes are in the Chord Ring.
    step_tracker: list with number of steps per query. passed with initial query RPC (see ring query_item method)
    '''

    def __init__(self,num_node,split):
        self.nodeDict = OrderedDict()
        self.nodeList = []
        self.num_node = 0
        self.arg_num_node = num_node
        self.arg_split = split
        self.item_keys = set()
        # RMB: initialize step tracker structure
        self.step_tracker = []

    '''
    Adds a node into the Ring, if there isn't already a node with the same values. 
    If the Node to be added is the first one, it will send the 'create' RPC to it.
    Otherwise, it will send the 'join' RPC.
    '''

    def add_node(self, ID):

        print('Adding node: {}'.format(ID))
        if ID in self.nodeDict.keys():
            print('Node already exists on the Chord ring. Exiting operation.')
            return

        # Initialize node, and add method of joining the chord ring.
        node = ChordNode(ID)
        if len(self.nodeDict) == 0:
            kwargs = {}
            function_RPC = ('create', kwargs)
            node.incoming_RPCs.append(('function', function_RPC))
        else:
            join_ID = random.choice(list(self.nodeDict.keys()))
            kwargs = {'join_ID': join_ID, 'nodeDict': self.nodeDict}
            function_RPC = ('join', kwargs)
            node.incoming_RPCs.append(('function', function_RPC))
        # Update the Chord Ring.
        self.nodeDict[ID] = node
        bisect.insort(self.nodeList, ID)
        self.num_node += 1

    '''
    Remove a node from the Ring. Because we are assuming spontaneous failure,
    all that happens is that the Node is no longer kept track of by the Chord Ring.
    '''

    def remove_node_failure(self, ID):
        print('Removing node by failure: {}'.format(ID))
        self.nodeDict.pop(ID)
        self.nodeList.remove(ID)
        self.num_node -= 1

    '''
    Remove a node from the Ring. Same as above, but this time we fail gracefully.
    This means that the contents of that are stored in the Node are first 
    transfered to the successor.
    '''

    def remove_node_graceful(self, ID):
        print('Removing node gracefully: {}'.format(ID))
        self.nodeDict[ID].send_successor_items(self.nodeDict)
        self.nodeDict.pop(ID)
        self.nodeList.remove(ID)
        self.num_node -= 1

    '''
    Has every node in the Chord Ring take one step.
    '''

    def advance_all_one_step(self, verbose=False):
        for i in range(self.num_node):
            node_ID = list(self.nodeDict.keys())[i]
            node = self.nodeDict[node_ID]

            node.counter[0] += 1
            self.check_periodic_ops(node)
            node.process_incoming_RPC(self.nodeDict, verbose)

    '''
    There are three operations that each Node should periodically run. 
    This function checks if it's time to run it, and if so, send the RPC to do so.
    '''

    def check_periodic_ops(self, node):
        if (node.counter[0] + node.counter[1]) % c.stabilize_period == 0 and node.joined:
            kwargs = {'nodeDict': self.nodeDict}
            function_RPC = ('stabilize', kwargs)
            node.incoming_RPCs.append(('function', function_RPC))
        if (node.counter[0] + node.counter[1]) % c.fix_finger_period == 0 and node.joined:
            kwargs = {'nodeDict': self.nodeDict}
            function_RPC = ('fix_finger', kwargs)
            node.incoming_RPCs.append(('function', function_RPC))
        if (node.counter[0] + node.counter[1]) % c.check_pred_period == 0 and node.joined:
            kwargs = {'nodeDict': self.nodeDict}
            function_RPC = ('check_pred', kwargs)
            node.incoming_RPCs.append(('function', function_RPC))

    '''
    Add item to the Chord ring. Note that I am cheating by just directly adding
    it in, rather than finding the successor and having the successor add the item.
    '''

    def add_item(self, item):
        k, v = item
        self.item_keys.add(k)
        for i, curr_ID in enumerate(self.nodeList):
            prev_ID = self.nodeList[(i - 1) % len(self.nodeList)]
            if between(prev_ID, curr_ID, k):
                self.nodeDict[curr_ID].var['storage'][k] = v

    # RMB: added step tracker to kwargs below
    def query_item(self, item_key):
        #sssprint('Querying for {}'.format(item_key))
        query_ID = random.choice(list(self.nodeDict.keys()))
        query_node = self.nodeDict[query_ID]
        kwargs = {'dest_ID': query_ID, 'var_name': 'client', 'key': item_key,
                  'nodeDict': self.nodeDict, 'steps': 0, 'step_tracker': self.step_tracker}
        function_RPC = ('find_successor', kwargs)
        query_node.incoming_RPCs.append(('function', function_RPC))

    '''
    Checks to see if the current state of the Chord Ring is "correct".
    '''

    def check_correctness(self):
        key_list = list()
        overall_fail_test = False
        for node_ind, curr_ID in enumerate(self.nodeList):
            to_print = '\n'
            fail_test = False
            to_print += 'Problems with Node {}\n'.format(curr_ID) + '-' * 30
            curr_node = self.nodeDict[curr_ID]

            # Check predecessor is correct
            e_pred_ID = self.nodeList[(node_ind - 1) % len(self.nodeList)]
            a_pred_ID = curr_node.var['pred_ID']
            if not e_pred_ID == a_pred_ID:
                fail_test = True
                to_print += '\nNode {} has wrong predecessor. Expected: {}\tActual: {}'.format(curr_ID, e_pred_ID,
                                                                                               a_pred_ID)

            # Check if values in storage are correct
            item_keys = list(curr_node.var['storage'].keys())
            for item_key in item_keys:
                j = (bisect.bisect_left(self.nodeList, item_key)) % len(self.nodeList)
                e_ID = self.nodeList[j]
                if not e_ID == curr_ID:
                    fail_test = True
                    to_print += '\nNode {} incorrectly possesses item with key {}. Expected Node: {}'.format(curr_ID,
                                                                                                             item_key,
                                                                                                             e_ID)

            # Check if finger table values are correct
            for ind in range(c.ring_size):
                key = (curr_ID + 2 ** ind) % 2 ** c.ring_size
                ft_i = curr_node.var['finger_table_{}'.format(ind)]
                j = (bisect.bisect_left(self.nodeList, key)) % len(self.nodeList)
                e_ft_i = self.nodeList[j]
                if not ft_i == e_ft_i:
                    fail_test = True
                    to_print += '\nNode {} Has wrong finger table {} value. Expected: {}\tActual: {}'.format(curr_ID,
                                                                                                             ind,
                                                                                                             e_ft_i,
                                                                                                             ft_i)

            # Check if successor list is correct
            # The + 2 when indexing is because succ_list starts two the right with our implementation.
            for ind, succ in enumerate(curr_node.var['succ_list']):
                e_succ = self.nodeList[(node_ind + ind + 2) % len(self.nodeList)]
                if not e_succ == succ:
                    fail_test = True
                    to_print += '\nNode {} has wrong successor list value at index {}. Expected: {}\tActual: {}'.format(
                        curr_ID, ind, e_succ, succ)

            if fail_test:
                overall_fail_test = True
                print(to_print)
        if not overall_fail_test:
            print('No errors in Chord Ring')

    '''
    To String function
    '''
    def GenerateZKP(self,balanceValue):
        p = 71
        g = 13
        x = balanceValue
        r = 8

        print('p=', p)
        print('g=', g)
        print('x=', x)
        print('r=', r)
        print('========')

        y = g ** x % p

        print('Y=', y)

        C = g ** r % p
        print('C=', C)

        print('========')
        val1 = g ** ((x + r) % (p - 1)) % p
        print('g^(x+r)%(p-1) mod p=', val1)

        val2 = C * y % p
        print('C.y mod P=', val2)

        if (val1 == val2):
            print('Well done ... have you proven that you know x')
        else:
            print('Not proven')
    def payment(self,paths,amount):
        if len(paths)==0:
            print("The payment transaction is complete")
        else:
            channelid = []
            x = paths.pop(0)
            channelid.append(x)
            node = self.nodeDict[x]
            first = paths[0]
            channelid.append(first)
            Remainingamount = node.var['Channelbalance'][str(channelid)]-amount
    def checkingavilable(self,path,amount,checking,p1):
        while checking==True:
            if len(path)==1:
                break
            else:
                channelid=[]
                x=path.pop(0)
                channelid.append(x)
                node=self.nodeDict[x]
                first=path[0]
                channelid.append(first)
                maximumvalue=random.randint(10,node.var['Channelbalance'][str(channelid)])
                if amount<maximumvalue:
                    x=True
                    self.checkingavilable(path,amount,x,p1)
                else:
                  x=False
                  self.checkingavilable(path, amount, x,p1)
        if checking==False:
            print("The is path is not avalible")
        else:
            print("this path is available")
            #print(p1)

    def closest_value(self,input_list, input_value):

        arr = np.asarray(input_list)

        i = (np.abs(arr - input_value)).argmin()

        return arr[i]


    def closest(self,lst, K):
        return lst[min(range(len(lst)), key=lambda i: abs(lst[i] - K))]
    def tocheckReciver(self,opsit,paths,rec):
        x=False
        for i in range(len(opsit)):
            if rec==opsit[i]:
                paths.append(rec)
                x=True
        return x,paths
    def helper(self,paths,dicto,fio,recv,counter,amount1,p):
      with open("rand_tx_o_insideChord_"+str(p+1)+".txt","a+") as f:
        # insideChord_str = ''
        # insideChord_str.append('@@@ Inside helper...')
        #pathsl=[]
        #pathsl.append(paths)
        conter=counter
        fo,paths=self.tocheckReciver(fio,paths,recv)
        if fo==False or conter>0:
            nearst = self.closest_value(fio, recv)
            #nearst = self.closest(fio, recv)
            node = self.nodeDict[nearst]
            if dicto[nearst] == False:
                dicto[nearst] = True
                paths.append(nearst)
                ins = sorted(node.var['FingertableID'])
                self.helper(paths, dicto, ins, recv,counter,amount1,p)
            #else:
                #conter=conter+1
                #ins = sorted(node.var['FingertableID'])
                #self.helper(paths, dicto, ins, recv, conter,amount1)
        else:
            if len(paths) <= np.log2(self.arg_num_node):
              f.write(str(paths))
              f.write("The length inside the Chord ring :" +str(len(paths))+'\n')
              # print(paths)
              # print("The length inside the Chord ring :" +str(len(paths)))

        '''if conter==0:
            checking = True
            print("hello")
            print(paths)
            x = paths
            self.checkingavilable(paths, amount1, checking, x)

        else:
            print("there is no path")'''

        """
        for i in range(len(fio)):
            print("iam in helper")
            print(fio[i])
            print("iam out")
            if fio[i]==recv:
                dicto[fio[i]]=True
                paths.append(recv)
                break
            nearst=self.closest(fio,recv)
            node = self.nodeDict[nearst]
            if dicto[nearst]==False:
                dicto[nearst]=True
                print("iam in second part")
                print(dicto)
                print("looooooooool")
                paths.append(nearst)
                ins=sorted(node.var['FingertableID'])
                self.helper(paths,dicto,ins,recv)
            else:
                #print("there is no path")
                break

                #ph=fio.remove(nearst)
                #self.helper(paths,dicto,ph,recv)
        print(paths)
        """
    def findpaththree(self,sender,revciver,amount,p):
        pathschord=[]
        conunter=0
        print("the Sender :"+ str(sender))
        print("The Reciver :" + str(revciver))
        dicvalue = {}
        path=[]
        for i in range(len(self.nodeList)):
            dicvalue[self.nodeList[i]]=False
        #ID = self.nodeList[sender]
        #print(dicvalue)
        node = self.nodeDict[sender]
        dicvalue[sender] = True
        #print(dicvalue)
        fig=sorted(node.var['FingertableID'])
        print("The Finger table of Nearest Routing helper : "+ str(sorted(node.var['FingertableID'])))
        #print(fig)
        path.append(sender)
        #print(path)
        rec=revciver
        self.helper(path,dicvalue,fig,rec,conunter,amount,p)






    def findPathtwo(self,graph,sender,revciver,amount):
        print("The Sender :" + str(sender))
        print("The Reciver :" + str(revciver))
        '''print("Generating Graph For chord based on Networkx library")
        graph = nx.strongly_connected_components()
        print("The Sender :" + str(sender))
        print("The Reciver :" + str(revciver))
        for i in range(len(self.nodeList)):
            ID = self.nodeList[i]
            node = self.nodeDict[ID]
            x = node.var['FingertableID']
            # print(x)
            # print("---------------------------------------")
            graph.add_node(self.nodeList[i])
            for j in range(len(x)):
                # print(x[j])
                graph.add_edge(self.nodeList[i], x[j])
        print("The Nodes of Chord graph")
        print(graph.nodes)
        print("The edges of Chord graph")
        print(graph.edges)'''
        #print([p for p in nx.all_simple_paths(graph, source=sender, target=revciver, cutoff=None)])
        node = self.nodeDict[sender]
        you=node.var['FingertableID']
        for p in nx.all_simple_paths(graph, source=sender, target=revciver, cutoff=None):
            x=p
            if len(x)<=6 and x[1] in you :
                print(x)
                break
            else:
                print("There is no path avalabile")
                break

    def Find_path_2(self,SenderRountingID,ReciverRoutingID,Amount):
        #print("Find the path between the Sender and other RoutingHelper not in his Fingertable")
        if SenderRountingID==ReciverRoutingID:
            print("Hey we Found the path")
        else:
            node = self.nodeDict[SenderRountingID]

            print("The Sender ID :"+ str(SenderRountingID))
            print("The Sender Finger Table :"+ str(node.var['FingertableID']))
            print("The Node not in Sender Finger Table : "+ str(node.var["Not_FT"]))
            print("The Sender channels :"+ str(node.var['NodeChannels']))
            print("The Sender channels balances :"+ str(node.var['Channelbalance']))
            print("The amont need to be send it  : " + str(Amount))
            print("-************************-")
            count=0
            accespt=0
            print()
            for key in node.var['Channelbalance']:
                count = count + 1
                if Amount < node.var['Channelbalance'][key]:
                    accespt=accespt+1
                    print("The Amount can be handled by this channels"+ key)
                    #node.var['Channelbalance'][key]=abs(Amount-node.var['Channelbalance'][key])
                    print( "The remaining balance : "+ str(node.var['Channelbalance'][key]))
                    print(count)
                    if accespt>0:
                        self.Sendtransaction(node.var['FingertableID'][count-1],ReciverRoutingID, Amount)
                else:
                    print("The Payment can not go through the this channel"+key)
                    break
    def Sendtransaction(self,SenderRountingID,ReciverRoutingID,Amount):
        if SenderRountingID==ReciverRoutingID:
            print("Hey we Found the path")
        else:
            node = self.nodeDict[SenderRountingID]
            print("-************************-")
            print(SenderRountingID)
            #print(node.var['FingertableID'])
            #print(node.var['NodeChannels'])
            #print(node.var['Channelbalance'])
            print("transaction amount : " + str(Amount))
            print("-************************-")
            count=0
            accespt=0
            print()
            for key in node.var['Channelbalance']:
                count = count + 1
                if Amount < node.var['Channelbalance'][key]:
                    accespt=accespt+1
                    print("The Amount can be handled by this channels"+ key)
                    node.var['Channelbalance'][key]=abs(Amount-node.var['Channelbalance'][key])
                    print( "The remaining balance : "+ str(node.var['Channelbalance'][key]))
                    print(count)
                    if accespt>0:
                        self.Sendtransaction(node.var['FingertableID'][count-1],ReciverRoutingID, Amount)
                else:
                    print("The Payment can not go through the this channel"+key)
                    break

    #def findPath(self,SenderRountingID,DestinationRoutingID,nodelist):
    def Find_path_1(self,Amount,NeraestRountingHelper_ID,nodelist,p):
        print("------------Find Path-1---------------------------------------")
        print("The ID's of the Nearst Routing Helper (Sender inside of chord) : " +str(NeraestRountingHelper_ID))
        print(" The Amount Payment to send :  "+str(Amount))
        path=[]
        path.append(NeraestRountingHelper_ID)

        Direct_channel_path=[]
        node=self.nodeDict[NeraestRountingHelper_ID]
        FingerTable_NeraestRountingHelper=node.var['FingertableID']
        for i in range (len(node.var['NodeChannels'])):
            #print("stupied Rounting Helper"+str(NeraestRountingHelper_ID))
            value=node.var['Channelbalance'].get(str(node.var['NodeChannels'][i]))
            #print(value)

            if Amount < value:
                Direct_channel_path.append(node.var['NodeChannels'][i])

            #if Amount<node.var['Channelbalance'].get(str(channelID[i])):
             #   Direct_channel_path.append(channelID[i])
        print(Direct_channel_path)
        if len(Direct_channel_path)>0:
            print("Available Paths from the nerast Routing helper to his Nodes in his Finger table : ")
            print(Direct_channel_path)
            not_FT = list(set(self.nodeList) - set(node.var['FingertableID']))
            node.var["Not_FT"] = not_FT
            not_FT=list(set(not_FT)-set(path))
            node.var["Not_FT"] = not_FT
            print("The nodes are not in the Nearest Routing helper : ")
            print(not_FT)
            print("----------------Path Find-1 Done-------------------------------------------")
            print("-------here we go ----find path 2----using our algorithim--")
            for i in range(len(not_FT)):
                self.findpaththree(NeraestRountingHelper_ID, not_FT[i],Amount,p)
            print("-----------------Done--------------------------------------------")

            print("-------here we go ----find path 2----based Networks library--")
            graph = nx.DiGraph()
            
            #print("The Sender :" + str(sender))
            #print("The Reciver :" + str(revciver))
            for i in range(len(self.nodeList)):
                ID = self.nodeList[i]
                node = self.nodeDict[ID]
                x = node.var['FingertableID']
                # print(x)
                # print("---------------------------------------")
                graph.add_node(self.nodeList[i])
                for j in range(len(x)):
                    # print(x[j])
                    graph.add_edge(self.nodeList[i], x[j])
            print("The Nodes of Chord graph")
            print(graph.nodes)
            print("The edges of Chord graph")
            print(graph.edges)
            #for i in range(len(not_FT)):
                #self.findPathtwo(graph,NeraestRountingHelper_ID, not_FT[i],Amount)
            print("-----------------Done--------------------------------------------")
            print ("-------here we go ----find path 2------")
            #for i in range(len(not_FT)):
                #self.Find_path_2(NeraestRountingHelper_ID, not_FT[i],Amount)
            #print("-----------------done--------------------------------------------")

        else:
            print("Sender Should Find Another Routing Helper")
      



    def DirectChannels(self,SenderRountingID,DestinationRoutingID):
        counter=0
        node = self.nodeDict[SenderRountingID]
        listnode=node.var['FingertableID']
        print("iam here")
        print(listnode)
        print("-------------------Find Path-------------------------------------")
        for i in range(len(listnode)):
            if int(DestinationRoutingID)==int(listnode[i]):
                counter=counter+1
                print("There is a direct payment Between Sender and Reciver")

    TimeKeygeneration = []
    # def Keygeneration (self,ID):

    #     start_time = time.time()
    #     timesummation=0
    #     node = self.nodeDict[ID]
    #     (Node_pub, Node_priv) = rsa.newkeys(512)
    #     node.var['Pub/Privkeys'].append(Node_pub)
    #     node.var['Pub/Privkeys'].append(Node_priv)
    #     print("the public key and Privit key of "+ str(ID))
    #     print("public key")
    #     print(Node_pub)
    #     print("private key")
    #     print(Node_priv)
    #     #timesummation=timesummation+(time.time() - start_time)
    #     self.TimeKeygeneration.append(time.time() - start_time)
    #     #print("--- %s seconds ---" % (time.time() - start_time))
    #     print(self.TimeKeygeneration)

    def __str__(self):


        to_print = ""
        #print("Mohammed")
        print("The nodes ID's : ")
        print(self.nodeList)
        #creategraph(self.nodeList,3)
        #max_comp = max(nx.strongly_connected_components(g), key=len)
        # g = decompress_pickle('Testing_graph')
        # g = gc.parse_multi_di_graph('./lngraph_2020_05_01__10_00.json', exclude_disabled=True)  # EXCLUDE DISABLED EDGES!
        # print("G has {} nodes and {} edges (={} active channels)".format(g.number_of_nodes(), g.number_of_edges(),
                                                                    #  g.number_of_edges() / 2))
        # compressed_pickle(g,'Testing_graph')
        
        g = decompress_pickle('Testing_graph')
        ## SCC
        # max_comp = max(nx.strongly_connected_components(g), key=len)                                                              
        # print('#@@!',max_comp)
        # compressed_pickle(max_comp,'max_component_graph')
        # max_component_graph = decompress_pickle('max_component_graph')
        # print(max_component_graph)
        # print(type(max_component_graph))
      

        print("-------------Generating Keys---------------------------")

        # for ID in self.nodeList:
        #     self.Keygeneration(ID)

        # print(self.TimeKeygeneration)
        # timesummation=0
        # for i in range(len(self.TimeKeygeneration)):
        #     timesummation=timesummation+self.TimeKeygeneration[i]
        # print("The time required to generate keys"+ str(timesummation))
        # print("---------------Generating Keys Done--------------------------")
        print("-----------Channel Creating and Genrtaing balance------------")
        for ID in self.nodeList:
            dict_channl={}
            Channel_ID = []
            node_jo = []

            #self.Keygeneration(ID)
            node = self.nodeDict[ID]
            to_print += 'Node {}\n'.format(ID) + '-' * 40 + '\n'
            # for RPC_message in node.incoming_RPCs:
            #    to_print += self.RPC_to_string(RPC_message)
            # to_print += 'RPC Queue: {}\n'.format(node.incoming_RPCs)
            #print("node balance : "+ str(ID))
            #print(node.var['nodebalance'])
            #print("thank you")
            to_print += 'Successor List: {}\n'.format([node.var['finger_table_0']] + node.var['succ_list'])
            to_print += 'Predecessor: {}\n'.format(node.var['pred_ID'])
            for i in range(c.ring_size):

                var_name = 'finger_table_{}'.format(i)
                node_jo.append(node.var[var_name])
                node.var['FingertableID'].append(node.var[var_name])

                # print(node_jo)
            # print(set(node_jo))
            #print("iamhere")
            node.var['FingertableID']=list(set(node.var['FingertableID']))
            #print(node.var['FingertableID'])
            #print("iamhere")
            node_jo = list(set(node_jo))


            for i in range(len(node_jo)):
                channel = []

                channel.append(ID)
                channel.append(node_jo[i])
                Channel_ID.append(channel)
                node.var['NodeChannels'].append(channel)

            # print(node_jo)
            print(" Channels created by node with Routing helper " + str(ID))
            print(Channel_ID)
            print(node.var['FingertableID'])
            for i in range(len(node_jo)):
                #dict_channl[str(Channel_ID[i])]=random.randint(20000,1000000)
                node.var['Channelbalance'][str(Channel_ID[i])]= 10 * 65033000  #random.randint(5000,15000)
            print(" Channels balance of Routing helper " + str(ID))
            #print(dict_channl)
            print(node.var['Channelbalance'])

        print("----------channel Creating and balance Generating is Done---------------------")
        print("Finding Route and Payment from Sender to Nearset Routing helper in Chord Ring ")

        tx_data = decompress_pickle('SenderReceiver_1_3_mil')
        shortest_paths_sender_helper = decompress_pickle('shortest_paths_sender_helper'+str(self.arg_num_node))
        shortest_paths_helper_receiver = decompress_pickle('shortest_paths_helper_receiver'+str(self.arg_num_node))
        tx_data_splits =  np.array_split(tx_data,216) # no of splits to run in parallel
        SenderandDestination = tx_data_splits[self.arg_split] 
        
        for p in range(len(SenderandDestination)):
        
          Sender=SenderandDestination[p][0]
          reciver=SenderandDestination[p][1]
          
          
          home_dir = '/home/grad20/kkolachala/RACED_final'
          
          # home_dir = '/content/drive/MyDrive/RACED/finalcodes/'

          os.makedirs(home_dir+'/rand_tx_output/'+str(self.arg_num_node)+"/",exist_ok=True)
          os.chdir(home_dir+'/rand_tx_output/'+str(self.arg_num_node)+"/")
          with open("rand_tx_o_split_"+str(self.arg_split)+"_tx_"+str(p)+".txt","w") as f:
            
            f.write("@sender"+str(Sender)+" @receiver"+str(reciver))
            f.write("Sender : " +str(Sender)+"\n") # print("Sender : " +str(Sender))
            f.write("Reciver :"+ str(reciver)+"\n") # print("Reciver :"+ str(reciver))
            f.write("Lists Nodes : "+ str(self.nodeList)+"\n") # print("Lists Nodes : "+ str(self.nodeList))
            
            shortest_path_sender_helper_chord = shortest_paths_sender_helper[Sender]
            ll = sorted(shortest_path_sender_helper_chord.items(),key=lambda item: item[1])
            for l in ll:
              if l[1]!=0:
                break

            shortest_sender_to_helper_nodeID = l[0]
            pathscheckingforward = l[1]

            shortest_path_helper_receiver_chord = shortest_paths_helper_receiver[reciver]
            ll = sorted(shortest_path_helper_receiver_chord.items(),key=lambda item: item[1])
            for l in ll:
              if l[1]!=0:
                break

            shortest_destination_to_helper_nodeID = l[0]
            pathscheckingbackward = l[1]

            # pathsfromsendertoreciver=[]
            # for i in range (len(self.nodeList)):

            #   if nx.has_path(g, Sender, self.nodeList[i]):
            #     pathscheckingforward.append(self.nodeList[i])
            
            # shortest_path_sender_chord_len = len(self.nodeList)
            
            # for i in range (len(pathscheckingforward)):
            #   route = routing(g,Sender,pathscheckingforward[i],1)
            #   route_len = len(route)
              
            #   if shortest_path_sender_chord_len > route_len:
            #     shortest_path_sender_chord_len = route_len
            #     shortest_path_sender_chord = route
            #     shortest_sender_to_helper_nodeID = pathscheckingforward[i]

            #   # pathsfromsendertoreciver.append(len(routing(g,Sender,pathscheckingforward[i],1))))
            # # shortest_path_sender_chord = min(pathsfromsendertoreciver)
            # print('~@@@~',shortest_path_sender_chord_len)
            # # self.nodeList.remove(shortest_sender_to_helper_nodeID)
            # all_nodes = self.nodeList.copy()
            # all_nodes.remove(shortest_sender_to_helper_nodeID)
            
            # for i in range (len(all_nodes)):
            #   if nx.has_path(g, reciver, all_nodes[i]):
            #       pathscheckingbackward.append(all_nodes[i])

            # shortest_path_sender_chord_len = len(self.nodeList)

            # for i in range (len(pathscheckingbackward)):
            #   route = routing(g,Sender,pathscheckingbackward[i],1)
            #   route_len = len(route)
              
            #   if shortest_path_sender_chord_len > route_len:
            #    shortest_path_sender_chord_len = route_len
            #    shortest_path_sender_chord = route
            #    shortest_destination_to_helper_nodeID = pathscheckingbackward[i]

              # pathsfromsendertoreciver.append(len(routing(g,Sender,pathscheckingforward[i],1))))
            # shortest_path_sender_chord = min(pathsfromsendertoreciver)
    
            # a_set = set(pathscheckingforward)
            # b_set = set(pathscheckingbackward)
            if pathscheckingforward>0 and pathscheckingbackward>0: #and len(a_set.intersection(b_set)) >=2:
              # list1_as_set = set(pathscheckingforward)
              # intersection = list1_as_set.intersection(pathscheckingbackward)
              # intersection_as_list = list(intersection)
              # destination_inside=random.sample(intersection_as_list,2) ## should be shortest path
              
              destination1=shortest_sender_to_helper_nodeID
              destination2=shortest_destination_to_helper_nodeID
              f.write("Finding Route and Payment from Sender to Nearset Routing helper in Chord Ring "+"\n") # print("Finding Route and Payment from Sender to Nearset Routing helper in Chord Ring ")
              rnd_tx_amt = random.randint(1,65033000)
              start_time = time.time()
              send_trans = str(send_tx(g, Sender, destination1, rnd_tx_amt))
              f.write(send_trans+"\n") # print(send_tx(g, Sender, destination1, rnd_tx_amt))
              try:
                 s = send_trans.split("S (")[1].split(": ")[1][:-2]
                 tx_path_len= len(ast.literal_eval(s))
                #  f.write("Path length - "+str(tx_path_len)+"\n")
              except: 
                f.write("~Insufficient balance!!\n")
              
              f.write(str(time.time() - start_time) + " --- Sender to near rh in seconds ---\n") # print("--- %s Sender to near rh in seconds ---" % (time.time() - start_time))

              f.write("the length of path from sender to nearest Routing helper \n")# print("the length of path from sender to nearest Routing helper")
              f.write("----------------------------------------------------------------------------- \n")
             # print("-----------------------------------------------------------------------------")
              start_time = time.time()
              #print("hellllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllo")
              find_path_1 = self.Find_path_1(rnd_tx_amt,destination1,node_jo,p)
              # f.write("inside chord ring - "+str(find_path_1)+"\n")
              f.write(str(time.time() - start_time) +" --- Time inside the Chord ring ---\n")
      
              #print("llllllllllllllllllllllllllllllllllllllllllllllllllllllllloooooooooooooooooooooooooooooooooooooooooooooooo")
              f.write("Finding Route and Payment from Destination RoutingHelper in chord Ring to Destination \n")
              start_time = time.time()
              f.write(str(send_tx(g, destination2, reciver, rnd_tx_amt))+"\n")
              f.write(str(time.time() - start_time)+" --- End Rh to receiver --- \n")
              f.write("the length of path from Destination inside routing hellper to Destination \n")
              f.write("------------------------------------------------------------------------------------- \n")
            else:
              f.write("There is no path\n")
            os.chdir(home_dir)
        return to_print

    ##Printing happens here.

    def RPC_to_string(self, RPC_message):
        RPC_type, RPC = RPC_message
        if RPC_type == 'value':
            return ''
        else:
            func_name, kwargs = RPC
            to_print = '{}: '.format(func_name)
            for k in kwargs.keys():
                if k == 'nodeDict': continue
                to_print += '{}-{} '.format(k, kwargs[k])
            to_print += '\n'
            return to_print
