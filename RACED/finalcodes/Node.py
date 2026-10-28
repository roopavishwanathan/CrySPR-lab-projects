import constants as c
import math
import random


class ChordNode:
    ''' A single Node on the Chord Ring. Each Node contains the following:
        ID:             Hashed ID of the Node.
        pred_ID:        ID of the Node that preceeds itself.
        finger_table_i: ith entry of the finger table.
        next:           Index that keeps track of next finger table entry to update
        storage:        Dictionary that holds the keys and values of the items it stores.
        succ_list:      Successor list, of size r-1. Contains the subsequent successors AFTER
            the first one, which is already stored in finger_table_0

    Furthermore, each Node contains the following:
        func:          A dictionary that makes function names to actual Node functions themselves.
        joined:        A boolean to keep track of whether the Node has joined the ring yet.
            Only set to True once it's successor has been determined.
        incoming_RPCs: A queue of RPCs that the node needs to process. For more information
            on RPCs, view the README document.
        counter:       countains (operation_count, offset). Used as a proxy for time to determine
            when to fix finger and stabilize. The offset is randomly generated to make sure
            that not all Nodes are trying to fix finger and stabilize at the same itme.

    '''

    def __init__(self, ID):
        self.var = {}  # var contains ALL variables that define the node.
        self.var['ID'] = ID
        self.var['pred_ID'] = None
        for i in range(c.ring_size):
            var_name = 'finger_table_{}'.format(i)
            self.var[var_name] = None
        self.var['next'] = 0
        self.var['storage'] = {}
        self.var['succ_list'] = [None] * (c.successor_list_size - 1)
        self.var['nodebalance']=random.randint(500,10000)
        self.var['FingertableID']=[]
        self.var['NodeChannels']=[]
        self.var['Channelbalance']={}
        # self.var["Pub/Privkeys"]=[]
        self.var["long_term_signing_key"]=[]
        self.var["long_term_verfication_key"]=[]
        
        self.var["temp_verification_key"]=[]
        self.var["temp_signing_key"]=[]

        self.var["public_parameter_long_term"]=[]
        self.var["public_parameter_temp"]=[]

        self.var["Not_FT"]=[]
        self.func = {}
        self.func['find_successor'] = self.find_successor
        self.func['create'] = self.create
        self.func['join'] = self.join
        self.func['request_items'] = self.request_items
        self.func['send_items'] = self.send_items
        self.func['stabilize'] = self.stabilize
        self.func['notify'] = self.notify
        self.func['fix_finger'] = self.fix_finger
        self.func['check_pred'] = self.check_pred

        self.joined = False
        self.incoming_RPCs = []
        self.counter = [0, random.randint(0, c.max_offset)]

    '''
    At each timestep, the Node will process one incoming RPC. The RPC can either
    be a value RPC, which means the Node needs to process the returned value, or 
    it can be a function RPC, which means the Node needs to launch a function.
    If there are no RPCs to process, then the Node does nothing.
    Inputs:
        nodeDict: A dictionary that maps IDs to Nodes.
    '''

    def process_incoming_RPC(self, nodeDict, verbose=False):
        if len(self.incoming_RPCs) == 0:
            return
        # Get the RPC in a queue order.
        RPC_type, RPC = self.incoming_RPCs.pop(0)

        # If the RPC is a value RPC, then we process it. If the variable name is client,
        # then the client is the one who ran the query, so we print it. Otherwise, it is
        # a value to variable specified by var_name that needs to be processed.
        # If the var name is storage, then we add incoming values to our storage. Otherwise,
        # we set the variable to the value.
        if RPC_type == 'value':
            var_name, val = RPC
            if var_name == 'client':
                # RMB: added step_tracker to below
                item_key, successor, steps, step_tracker, success = val
                if success:
                    #print('Successfully found key {} at Node {} in {} steps!'.format(item_key, successor, steps))
                    # RMB: added below; hopefully only real step that is needed!
                    #print('Appending steps to step_tracker')
                    step_tracker.append(steps)
                else:
                    print('Incorrect Node {} located for key {} in {} steps.'.format(successor, item_key, steps))
                    print('!Tracker needs to be added for this case to deal with churrn condition!')
            elif var_name == 'storage':
                if verbose:
                    print('Node {} storing items {}'.format(self.var['ID'], val))
                for item in val:
                    self.var['storage'][item[0]] = item[1]
            # If this is the first update to successor, then we need to annouce that
            # The node has successfully joined, as well as get items from successor.
            elif var_name is 'finger_table_0' and self.var['finger_table_0'] is None:
                # print('Node {} Successfully joined on counter {}'.format(self.var['ID'], self.counter[0]))
                self.joined = True
                self.var[var_name] = val
                self.request_items(nodeDict)
            # Otherwise, we can just assign the variable to the value.
            else:
                self.var[var_name] = val
                if verbose:
                    print('Node {} putting value {} in variable {}'.format(self.var['ID'], val, var_name))
        # If the RPC is a function RPC, then we have the Node call the function with the
        # passed in arguments.
        elif RPC_type == 'function':
            func_name, kwargs = RPC
            if verbose:
                print('Node {} running function {}'.format(self.var['ID'], func_name))
            self.func[func_name](**kwargs)

    '''
    Helper function where, using the first indeix of the finger and the successor list, finds the 
    first successor that is alive. Note that if none are alive, the program will throw an 
    IndexOOB exeception and crash. That, in a way, is desired behavior.
    Inputs:
        nodeDict: A dictionary that maps IDs to Nodes.
    '''

    def find_first_alive_succ(self, nodeDict):
        if self.var['finger_table_0'] in nodeDict.keys():
            succ = self.var['finger_table_0']
        else:
            found_alive_succ = False
            succ_ind = 0
            while not found_alive_succ:
                if succ_ind == c.successor_list_size - 1:  #####
                    print('Node {} is throwing OOB Exception with Succesor List: {}'.format(self.var['ID'], self.var[
                        'succ_list']))  #####
                succ = self.var['succ_list'][succ_ind]
                if succ in nodeDict.keys():
                    found_alive_succ = True
                succ_ind += 1
        return succ

    '''
    The bread and butter of Chord. The basic logic is covered within the paper. 
    Note that because we keep track of the ID that made the original find_successor 
    request, we always return the found successor directly to that Node. 
    Inputs: 
        dest_ID:  The ID of the original Node that queried for the key. This is so
            if the successor is found, we can return the value immediately to 
            that Node.
        var_name: The name of the variable that is associated with the key we are 
            trying to find the successor for. For example, it could be 'client', which
            means the client is the one that requested the successor. It could be 
            'finger_table_i', which means the successor's ID would be put into 
            that entry of the finger table.
        key:      The key that we are trying to find the successor for.
        nodeDict: A dictionary that maps IDs to Nodes.
    Actions:
        Sends a value_RPC back to node of dest_ID if successor is found.
        Sends a function_RPC to the closest preceding node to call find_successor otherwise. 
    '''

    # RMB: added optinal argument for step_tracker here
    def find_successor(self, dest_ID, var_name, key, nodeDict, steps=None, step_tracker=None):
        if steps is not None:
            steps += 1
        # Find the first non-dead successor
        ft_0 = self.find_first_alive_succ(nodeDict)
        # If we find the successor, we send a value RPC to the Node that made the initial
        # query.
        if between(self.var['ID'], ft_0, key):
            if var_name == 'client':  # RMB: if query, should have steps and step_tracker arguments
                if key in nodeDict[ft_0].var['storage'].keys():
                    success = True
                else:
                    success = False
                # RMB: added step_tracker as input here
                value_RPC = (var_name, (key, ft_0, steps, step_tracker, success))
            else:
                value_RPC = (var_name, ft_0)
            # We also make sure the initial query node exists.
            if dest_ID in nodeDict.keys():
                nodeDict[dest_ID].incoming_RPCs.append(('value', value_RPC))
            return
        # Otherwise, we find the closest preceding node through the finger table
        for i in range(c.ring_size - 1, -1, -1):
            ft_i = self.var['finger_table_{}'.format(i)]
            # The second conditional is case of node departure or failure.
            if ft_i is not None and ft_i in nodeDict.keys() and between_exclusive(self.var['ID'], key, ft_i):
                # RMB: added step_tracker to below
                kwargs = {'dest_ID': dest_ID, 'var_name': var_name, 'key': key, 'nodeDict': nodeDict,
                          'steps': steps, 'step_tracker': step_tracker}
                function_RPC = ('find_successor', kwargs)
                nodeDict[ft_i].incoming_RPCs.append(('function', function_RPC))
                return

    '''
    Only gets run by the first node in the Chord Ring, as defined in paper. 
    Because pred_ID = None during initialization, we only need to Node successor ID to its own.
    '''

    def create(self):
        self.var['finger_table_0'] = self.var['ID']

    '''
    This gets run by newborn Nodes, as defined in the paper. It makes a random Node call
    find_successor. 
    Inputs:
        join_ID:  random ID of a node that will start the find_successor request.
        nodeDict: A dictionary that maps IDs to Nodes
    Actions:
        Sends a function RPC to the random Node to call find_successor for it.
    '''

    def join(self, join_ID, nodeDict):
        start_node = nodeDict[join_ID]
        # The node who needs the successor information is the current node.
        # The variable that the successor corresponds to is finger_table_0.
        # The key we are querying successor for is the Node's own key.
        kwargs = {'dest_ID': self.var['ID'],
                  'var_name': 'finger_table_0',
                  'key': self.var['ID'],
                  'nodeDict': nodeDict}
        function_RPC = ('find_successor', kwargs)
        nodeDict[join_ID].incoming_RPCs.append(('function', function_RPC))

    '''
    We want to make sure we have the correct items in our storage. This gets run when 
    the successor gets updated.
    Inputs:
        nodeDict: A dictionary that maps IDs to Nodes
    Actions: 
        Send function RPC to successor, asking them to send items.
    '''

    def request_items(self, nodeDict):
        succ_node = nodeDict[self.var['finger_table_0']]
        # If the node is it's own successor (possible if it is the only node in the Chord ring),
        # there's no point in requesting items.
        if succ_node.var['ID'] == self.var['ID']:
            return
        # Otherwise, the Node ask the successor to send items to it.
        kwargs = {'dest_ID': self.var['ID'], 'nodeDict': nodeDict}
        function_RPC = ('send_items', kwargs)
        succ_node.incoming_RPCs.append(('function', function_RPC))

    '''
    Sends relevant items to the node that claims is your predecessor. 
    Inputs:
        dest_ID:  ID of the Node to send the items to.
        nodeDict: A dictionary that maps IDs to Nodes
    Actions:
        Send value RPC to the Node that made the query, with all items
    '''

    def send_items(self, dest_ID, nodeDict):
        send_list = []
        # The items to send are the ones that aren't between the predecessor and the Node itself.
        for k, v in self.var['storage'].items():
            if not between(dest_ID, self.var['ID'], k):
                send_list.append((k, v))
        for item in send_list:
            self.var['storage'].pop(item[0])
        # Send the value RPC
        value_RPC = ('storage', send_list)
        # There is a miniscule chance that the Node we're sending to has died. This avoids that.
        if dest_ID not in nodeDict.keys():
            return
        nodeDict[dest_ID].incoming_RPCs.append(('value', value_RPC))

    ''' 
    If the node is gracefully failing, it can send all of the storage contents to 
    it's successor.
    Inputs:
        nodeDict: A dictionary that maps IDs to Nodes
    Actions:
        Sends value RPC to successor, with all items
    '''

    def send_successor_items(self, nodeDict):
        succ_ID = self.find_first_alive_succ(nodeDict)
        succ_node = nodeDict[succ_ID]
        send_list = []
        for k, v in self.var['storage'].items():
            send_list.append((k, v))
        value_RPC = ('storage', send_list)
        succ_node.incoming_RPCs.append(('value', value_RPC))

    '''
    Verify who the successor is, and notify the successor. The basic logic is defined in the paper.
    Inputs:
        nodeDict: A dictionary that maps IDs to Nodes
    Actions:
        Send function RPC to notify successor.
    '''

    def stabilize(self, nodeDict):
        # Finds the first successor that is still alive
        succ_ID = self.find_first_alive_succ(nodeDict)
        # Let's set this node to our successor tentatively, since as far as we know, it is the successor.
        self.var['finger_table_0'] = succ_ID
        succ_node = nodeDict[succ_ID]
        # This next line is cheating a bit. Instead of sending an RPC to query for the predecessor,
        # we're grabbing it directly. This is because it's a massive pain to get the above to
        # work with our framework, and this operation is constant and inexpensive anyways.
        succ_pred_ID = succ_node.var['pred_ID']
        # If there is another node between this Node and the successor, we need to update the
        # successor. There is also a chance that this 'in between node is dead. We need to
        # account for all of this
        if succ_pred_ID is not None and succ_pred_ID in nodeDict.keys() and between(self.var['ID'], succ_ID,
                                                                                    succ_pred_ID):
            self.var['finger_table_0'] = succ_pred_ID
        # Then, we update our successor list. At this point, we are sure that our successor is alive.
        # The successor list contains our successor's successor, as well as it's successor list (except for
        # the last value).
        succ_node = nodeDict[self.var['finger_table_0']]
        self.var['succ_list'] = [succ_node.var['finger_table_0']] + succ_node.var['succ_list'][:-1]
        # Regardless of whether the successor updates, the Node send a function RPC to the successor
        # to say that current node is predecessor.
        kwargs = {'pot_pred_ID': self.var['ID']}
        function_RPC = ('notify', kwargs)
        succ_node.incoming_RPCs.append(('function', function_RPC))

    '''
    Updates predecessor. The logic is described in the paper.
    Inputs:
        pot_pred_ID: potential predecessor ID.
    Actions:
        Updates pred_ID if applicable.
    '''

    def notify(self, pot_pred_ID):
        if self.var['pred_ID'] is None or between(self.var['pred_ID'], self.var['ID'], pot_pred_ID):
            self.var['pred_ID'] = pot_pred_ID
            # This can only happen if the node is the first node in the Chord ring.
            # Which means the notify is coming from the 2nd node in the ring, which means the
            # predecessor for this Node is also the successor.
            if self.var['finger_table_0'] == self.var['ID']:
                self.var['finger_table_0'] = self.var['pred_ID']
                self.joined = True

    '''
    Fixes one finger on the finger table. The logic is described in the paper.
    Inputs:
        nodeDict: A dictionary that maps IDs to Nodes
    Actions:
        Has itself start a find_predecessor lookup for the relevant finger.
    '''

    def fix_finger(self, nodeDict):
        i = self.var['next']
        key = (self.var['ID'] + 2 ** i) % 2 ** c.ring_size
        self.var['next'] = (self.var['next'] + 1) % c.ring_size
        self.find_successor(self.var['ID'], 'finger_table_{}'.format(i), key, nodeDict)

    '''
    Checks if the predecessor node still exists. If not, set the ID to None.
    Inputs:
        nodeDict: A dictionary that maps IDs to Nodes
    '''

    def check_pred(self, nodeDict):
        try:
            nodeDict[self.var['pred_ID']]
        except:
            self.var['pred_ID'] = None


def between(ID1, ID2, key):
    if ID1 == ID2:
        return True
    wrap = ID1 > ID2
    if not wrap:
        return True if key > ID1 and key <= ID2 else False
    else:
        return True if key > ID1 or key <= ID2 else False


def between_exclusive(ID1, ID2, key):
    if ID1 == ID2:
        return True
    wrap = ID1 > ID2
    if not wrap:
        return True if key > ID1 and key < ID2 else False
    else:
        return True if key > ID1 or key < ID2 else False
