from ChordRing import ChordRing
import constants as c
import random
from statistics import mean
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
import sys
sys.setrecursionlimit(2000)
verbose = False


import bz2
import pickle
# !pip install pickle5
import pickle5
import _pickle as cPickle
import os
import numpy as np
import pandas as pd
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

import argparse
parser = argparse.ArgumentParser(description="Number of nodes in the ring")
parser.add_argument('--num_nodes', default=int)
parser.add_argument('--split', default=int)
args = parser.parse_args()

def rand_key(l):
  key = l[0]
  l.remove(key)
  return key,l

# def rand_key():
#     return random.randint(0, 2 ** c.ring_size)
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
    print("-----------------Reading Lighting Network -----------------------------")
    g = gc.parse_multi_di_graph('./lngraph_2020_05_01__10_00.json', exclude_disabled=True)  # EXCLUDE DISABLED EDGES!
    print("G has {} nodes and {} edges (={} active channels)".format(g.number_of_nodes(), g.number_of_edges(),
                                                                     g.number_of_edges() / 2))
    #source = choice(list(g.nodes()))
    #target = choice(list(set(g.nodes()) - {source}))
    #print(source)
    #print(target)

    #if nx.has_path(g,source,target):
     #   print([p for p in nx.all_shortest_paths(g, source=source, target=target, weight="capacity", method='dijkstra')])
    #else:
      #  print("Sorry No path")
    #print(nx.degree_centrality(g))
    #print(nx.voterank(g,10))
    #print(nx.maximum_flow_value(g, source, target, capacity='capacity'))


# RMB: added below to avoid many collisions when number of nodes approaches ring size
def rand_address(nodeList):
    allChoices = set([x for x in range(2 ** c.ring_size)])
    return random.choice(list(allChoices - set(nodeList)))


def check_lookups():
    num_keys = 2000
    num_nodes = int(args.num_nodes)
    num_steps_between_new_nodes = 10 * c.max_offset

    num_queries = 100
    steps_between_query = 1

    chord = ChordRing()

    routing_helpers = decompress_pickle('routing_helper'+str(num_nodes))
    key , routing_helpers  = rand_key(routing_helpers)
    print('key - ',key)
    # Initialize Chord ring and add items.
    chord.add_node(key)

    # for i in range(num_keys):
    #     key = rand_key()
    #     chord.add_item((key, key))

    # Slowly build up the Chord ring with nodes.
    for i in range(num_nodes * num_steps_between_new_nodes):
        if i % (num_steps_between_new_nodes) == 0:
            chord.add_node(rand_key(routing_helpers))
        chord.advance_all_one_step(verbose=verbose)

    # Give the Ring more time to properly get values.
    for i in range(c.max_offset * 50):
        chord.advance_all_one_step(verbose=verbose)

    print(chord)
    chord.check_correctness()

    # Query the Ring for items
    for i in range(num_queries * steps_between_query):
        if i % (steps_between_query) == 0:
            item_key = random.sample(chord.item_keys, 1)[0]
            chord.query_item(item_key)
        chord.advance_all_one_step(verbose=verbose)
    for i in range(num_queries * c.ring_size):
        chord.advance_all_one_step(verbose=verbose)


def check_dropouts():
    num_keys = 2000
    num_initial_nodes = 5
    num_steps_between_add_drop = 10 * c.max_offset
    num_add_drops = 100
    add_prob = 0.5
    num_nodes = int(args.num_nodes)

    chord = ChordRing(num_nodes)

    # Initialize and add some Nodes
    chord.add_node(rand_key())
    for i in range(num_keys):
        key = rand_key()
        chord.add_item((key, key))

    for i in range(num_initial_nodes * num_steps_between_add_drop):
        if i % (num_steps_between_add_drop) == 0:
            chord.add_node(rand_key())
        chord.advance_all_one_step(verbose=verbose)
    for i in range(c.max_offset * 50):
        chord.advance_all_one_step(verbose=verbose)

    print('\n' + '-' * 40)
    print('Checking correctness after initial adding of nodes.')
    chord.check_correctness()
    print('-' * 40 + '\n')

    # Randomly add and fail nodes.
    for i in range(num_add_drops * num_steps_between_add_drop):
        if i % (num_steps_between_add_drop) == 0:
            coinflip = random.random()
            if coinflip < add_prob:
                chord.add_node(rand_key())
            else:
                remove_ID = random.choice(list(chord.nodeDict.keys()))
                chord.remove_node_failure(remove_ID)
        chord.advance_all_one_step(verbose=verbose)
    for i in range(c.max_offset * 50):
        chord.advance_all_one_step(verbose=verbose)

    print('\n' + '-' * 40)
    print('Checking correctness after adding and removing of nodes.')
    chord.check_correctness()
    print('-' * 40 + '\n')


def check_dropout_graceful():
    num_keys = 2000
    num_initial_nodes = 5
    num_steps_between_add_drop = 10 * c.max_offset
    num_add_drops = 100
    add_prob = 0.5

    num_queries = 100
    steps_between_query = 1

    chord = ChordRing()

    # Initialize and add some Nodes
    chord.add_node(rand_key())
    for i in range(num_keys):
        key = rand_key()
        chord.add_item((key, key))

    for i in range(num_initial_nodes * num_steps_between_add_drop):
        if i % (num_steps_between_add_drop) == 0:
            chord.add_node(rand_key())
        chord.advance_all_one_step(verbose=verbose)
    for i in range(c.max_offset * 50):
        chord.advance_all_one_step(verbose=verbose)

    print('\n' + '-' * 40)
    print('Checking correctness after initial adding of nodes.')
    chord.check_correctness()
    print('-' * 40 + '\n')

    # Randomly add and GRACEFULLY fail some Nodes.
    for i in range(num_add_drops * num_steps_between_add_drop):
        if i % (num_steps_between_add_drop) == 0:
            coinflip = random.random()
            if coinflip < add_prob:
                chord.add_node(rand_key())
            else:
                remove_ID = random.choice(list(chord.nodeDict.keys()))
                chord.remove_node_graceful(remove_ID)
        chord.advance_all_one_step(verbose=verbose)
    for i in range(c.max_offset * 50):
        chord.advance_all_one_step(verbose=verbose)

    print('\n' + '-' * 40)
    print('Checking correctness after adding and removing of nodes.')
    chord.check_correctness()
    print('-' * 40 + '\n')
    print(chord)

    # Query the Ring for items
    # for i in range(num_queries * steps_between_query):
    #     if i % (steps_between_query) == 0:
    #         item_key = random.sample(chord.item_keys, 1)[0]
    #         chord.query_item(item_key)
    #     chord.advance_all_one_step(verbose=verbose)
    # for i in range(num_queries * c.ring_size):
    #     chord.advance_all_one_step(verbose=verbose)


def small_test():
    num_keys = 100
    num_nodes = 15
    num_steps_between_new_nodes = 20 * c.max_offset

    chord = ChordRing()
    chord.add_node(rand_key())
    for i in range(num_keys):
        key = rand_key()
        chord.add_item((key, key))

    for i in range(num_nodes * num_steps_between_new_nodes):
        if i % (num_steps_between_new_nodes) == 0:
            chord.add_node(rand_key())
        chord.advance_all_one_step()
    for i in range(c.max_offset * 100):
        chord.advance_all_one_step()
    chord.stop_periodic = True
    print('No longer adding')
    for i in range(c.max_offset * 200):
        chord.advance_all_one_step()
    print(chord)
    chord.check_correctness()


# RMB: added this function to test average number of steps following query
def return_query_steps():
    start_time = time.time()
    # set parameters; will fix num queries and iterate through different numbers of nodes and keys
    num_keys = 1000000
    num_nodes = int(args.num_nodes)
    split = int(args.split)

    tx_data = decompress_pickle('SenderReceiver_1_3_mil')
    tx_data_splits =  np.array_split(tx_data,216) # no of splits to run in parallel
    SenderandDestination = tx_data_splits[split] 

    print('Printing first 5 sender receiver pair(testing): ',SenderandDestination[0:5])
    print('\n\n')
    print('**** num nodes ****',num_nodes)
    print('**** split ****',split)
    print('\n\n')

    num_steps_between_new_nodes = 20 * c.max_offset

    num_queries = 1000
    steps_between_query = 1
    # initialize ring
    chord = ChordRing(num_nodes,split)
    
    routing_helpers = decompress_pickle('routing_helper'+str(num_nodes))
    key , routing_helpers  = rand_key(routing_helpers)
    
    chord.add_node(key)
    # for i in range(num_keys):
    #     key = rand_key()
    #     chord.add_item((key, key))

    # add nodes
    for i in range(num_nodes * num_steps_between_new_nodes):
        if i % (num_steps_between_new_nodes) == 0:
            try:
              key , routing_helpers  = rand_key(routing_helpers)
                # chord.add_node(rand_address(chord.nodeList))
              chord.add_node(key)
            except Exception as e:
                print('no more names to allocate (more nodes than chord size?): {}'.format(e))
        chord.advance_all_one_step()
    for i in range(c.max_offset * 100):
        chord.advance_all_one_step()
    chord.stop_periodic = True
    print('No longer adding')
    print("@#--- %s Time for adding node ---" % (time.time() - start_time))

    # stabliize and check correctness
    for i in range(c.max_offset * 200):
        chord.advance_all_one_step()
    print(chord)
    chord.check_correctness()

    # query
    # for i in range(num_queries * steps_between_query):
    #     if i % (steps_between_query) == 0:
    #         routing_helpers = decompress_pickle('routing_helper'+str(num_nodes))
    #         item_key , routing_helpers  = rand_key(routing_helpers)
    
    #         # item_key = random.sample(chord.item_keys, 1)[0]
    #         chord.query_item(item_key)
    #     chord.advance_all_one_step(verbose=verbose)

    # to make sure all have cleared (max transit should be one time round)
    # for i in range(num_queries * c.ring_size):
    #     chord.advance_all_one_step(verbose=verbose)

    # print('\n Average number of steps was {} for {} nodes with {} keys total!'.format(mean(chord.step_tracker),
                                                                                     # num_nodes, num_keys))


if __name__ == "__main__":
    # check_dropout_graceful()
    #creategraph()
    print("-----------------------Chord Setup--------------------------------------")
    return_query_steps()
