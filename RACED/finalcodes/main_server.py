from ChordRing import ChordRing
import constants as c
import random
from statistics import mean
import argparse
import os
import csv

verbose = False

parser = argparse.ArgumentParser()
parser.add_argument("-k", type=int)
parser.add_argument("-n", type=int)
parser.add_argument("-i", type=int)
args = parser.parse_args()
print(args)
num_keys = args.k
num_nodes = args.n
iter = args.i
output_path = "result_dump"


def rand_key():
    return random.randint(0, 2 ** c.ring_size)


# RMB: added below to avoid many collisions when number of nodes approaches ring size
def rand_address(nodeList):
    allChoices = set([x for x in range(2 ** c.ring_size)])
    return random.choice(list(allChoices - set(nodeList)))


def check_lookups():
    num_keys = 2000
    num_nodes = 50
    num_steps_between_new_nodes = 10 * c.max_offset

    num_queries = 100
    steps_between_query = 1

    chord = ChordRing()

    # Initialize Chord ring and add items.
    chord.add_node(rand_key())
    for i in range(num_keys):
        key = rand_key()
        chord.add_item((key, key))

    # Slowly build up the Chord ring with nodes.
    for i in range(num_nodes * num_steps_between_new_nodes):
        if i % (num_steps_between_new_nodes) == 0:
            chord.add_node(rand_key())
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
    num_initial_nodes = 50
    num_steps_between_add_drop = 10 * c.max_offset
    num_add_drops = 100
    add_prob = 0.5

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
    num_initial_nodes = 50
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
    for i in range(num_queries * steps_between_query):
        if i % (steps_between_query) == 0:
            item_key = random.sample(chord.item_keys, 1)[0]
            chord.query_item(item_key)
        chord.advance_all_one_step(verbose=verbose)
    for i in range(num_queries * c.ring_size):
        chord.advance_all_one_step(verbose=verbose)


def small_test():
    num_keys = 100
    num_nodes = 10
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
def return_query_steps(num_keys, num_nodes):
    # set parameters; fix num queries; num_keys and num_nodes given through sys.argv
    # num_keys = 1000000
    # num_nodes = 1000
    num_steps_between_new_nodes = 20 * c.max_offset

    num_queries = 1000
    steps_between_query = 1
    # initialize ring
    chord = ChordRing()
    chord.add_node(rand_key())
    for i in range(num_keys):
        key = rand_key()
        chord.add_item((key, key))

    # add nodes
    for i in range(num_nodes * num_steps_between_new_nodes):
        if i % (num_steps_between_new_nodes) == 0:
            try:
                chord.add_node(rand_address(chord.nodeList))
            except Exception as e:
                print('no more names to allocate (more nodes than chord size?): {}'.format(e))
        chord.advance_all_one_step()
    for i in range(c.max_offset * 100):
        chord.advance_all_one_step()
    chord.stop_periodic = True
    print('No longer adding')

    # stabliize and check correctness
    for i in range(c.max_offset * 200):
        chord.advance_all_one_step()
    print(chord)
    chord.check_correctness()

    # query
    for i in range(num_queries * steps_between_query):
        if i % (steps_between_query) == 0:
            item_key = random.sample(chord.item_keys, 1)[0]
            chord.query_item(item_key)
        chord.advance_all_one_step(verbose=verbose)

    # to make sure all have cleared (max transit should be one time round)
    for i in range(num_queries * c.ring_size):
        chord.advance_all_one_step(verbose=verbose)
    average_steps = mean(chord.step_tracker)
    print('\n Average number of steps was {} for {} nodes with {} keys total!'.format(average_steps,
                                                                                      num_nodes, num_keys))
    return average_steps


# helper function to write to csv file
def output_steps(num_keys, num_nodes, output_path):
    trial_steps = [num_keys, num_nodes, return_query_steps(num_keys, num_nodes)]

    # we are saving here
    path_string = '{}/count_steps_keys_{}_nodes_{}_iter_{}'.format(output_path, num_keys, num_nodes, iter)

    # remove any old version
    if os.path.exists(path_string):
        os.remove(path_string)

    # dump to csv
    with open(path_string, 'w') as myfile:
        wr = csv.writer(myfile)
        wr.writerow(['num_keys', 'num_nodes', 'num_steps'])
        wr.writerow(trial_steps)


if __name__ == "__main__":
    # input variables fed in through parser
    output_steps(num_keys, num_nodes, output_path)
