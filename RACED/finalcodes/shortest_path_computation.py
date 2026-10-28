#@title function : load / save pickle_obj

### pickle

import bz2
import pickle
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



SenderReceiver_max = decompress_pickle('SenderReceiver_500000')

sender_60 = decompress_pickle('sender_60')
# receiver_60 = decompress_pickle('receiver_60')
req_routing_helper = decompress_pickle('req_routing_helper')

failed_nodes_sender_helper = []
for s in sender_60:
  for r in req_routing_helper:
    try:
      shortest_paths_sender_helper[s][r] = len(nx.shortest_path(g,source=s,target=r))
    except:
      shortest_paths_sender_helper[s][r] = 0
      # failed_nodes_sender_helper.append((s,r))