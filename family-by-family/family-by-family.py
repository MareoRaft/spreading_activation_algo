# imports
import sys
import time
from collections import deque
import math

import networkx as nx



# define constants
ACTIVATION_DECAY = 0.8
THRESHOLD = 0.05



class TimeQueue (deque):

  def add_node(self, i, output_activation_strength, node_name):
      """ Add a new node to the queue (in time order). It is assumed that the input is a tuple where the first value is the time. """
      # Grab the family to be activated at that time, creating one if there is none.
      while i >= len(self):
        new_empty_family = []
        self.append(new_empty_family)
      family = self[i]
      # Add the new node to the family.
      x = (output_activation_strength, node_name)
      family.append(x)

  def pop_family(self):
      """ Get the next family to be activated. """
      return self.popleft()



def get_valid_types_following(node_type, schema):
    """ Find the valid types immediately following a specific type in the schema. Just a helper function. """
    valid_types = set()
    type_index = schema.index(node_type)
    left_index = type_index - 1
    right_index = type_index + 1
    if left_index >= 0:
        valid_types.add(schema[left_index])
    if right_index < len(schema):
        valid_types.add(schema[right_index])
    return valid_types



# These functions calculate node and link strengths based on a weight.
# * The weight should be a nonnegative real number. You can think of the weight as the transfer time of a link or the distance or
#   "length" of a link. So a short link is stronger and faster. A link of weight 0 causes the activation to transfer instantaneously
#   and doesn't diminish activation strength at all.
# * These functions can be customized to fit the situation/behavior that we wish to model.
def get_node_strength(weight):
  # Node strength is s = 1/2^w.  Node weight is w = -ln_2(s).
  return 1 / 2 ** weight

def get_link_strength(weight):
  # Link strength is s = 1/2^w.  Link weight is w = -ln_2(s).
  return 1 / 2 ** weight

def get_link_transfer_time(weight):
  # Link transfer time is equal to ceil of link weight. Must be an integer.
  transfer_time = math.ceil(weight)
  if transfer_time <= 0:
    raise ValueError('Link weight must be positive in stepwise algo (use a positive weight).')
  return transfer_time



def queue_node_activation(tq, steps_until_activation, input_activation_strength, node):
  """ See if the node will activate and if so put it into the queue. """
  will_activate = input_activation_strength > THRESHOLD
  if not will_activate:
    return
  # Activate the node (deferred).
  # -- assign the node it's own activation strength
  output_activation_strength = input_activation_strength * get_node_strength(node['weight'])
  # -- add the node to the queue
  # print(f'adding node {node["name"]} with activation strength {output_activation_strength}')
  tq.add_node(i=(steps_until_activation - 1), output_activation_strength=output_activation_strength, node_name=node['name'])

# Input parameters are the graph (nodes, edges, node weights, edge weights, node types, and schema)
def algo(graph, start_state, schema):
    """ The STEPWISE FAMILY spreading activation algorithm.
    This algorithm calculates one family of nodes at a time, and is potentially faster because we can parallelize the nodes that get activated at the same time.
    """
    activation_history = [] # for output purposes, so we can see how the algorithm went down.
    tq = TimeQueue()
    # Put the starting nodes in the time queue. They will be the first to activate.
    for (start_node, start_input_activation_strength) in start_state:
      queue_node_activation(tq, steps_until_activation=1, input_activation_strength=start_input_activation_strength, node=start_node)
    # Current time is 0. This does not track real-life time but rather the time that our algorithm simulates as activation spreads.
    current_time = 0
    # Iteratively apply this algo until you've exhausted all reachable nodes.
    while tq:
      print(f'tq: {tq}')
      # take the first node out of the time queue (hence, the first activation event since nodes are ordered by time)
      family = tq.pop_family()
      activation_history.append((current_time, family)) # for logging purposes
      # update the current time
      current_time += 1
      for (current_node_activation_strength, current_node_name) in family:
        current_node = graph.nodes[current_node_name]
        # intersect its children with valid types to spread to. (note that this could be a preprocessing step if we don't want to dynamically change strategies)
        valid_types = get_valid_types_following(current_node['type'], schema)
        children = [graph.nodes[x] for x in graph.successors(current_node_name)]
        valid_children = [x for x in children if x['type'] in valid_types]
        # for each valid child, calculate whether it will activate
        for child in valid_children:
          # Conditionally activate the node. (queue_node_activation will only activate the node if strength above threshold)
          link = graph.edges[current_node_name, child['name']]
          time_until_activation = get_link_transfer_time(link['weight'])
          # calculate activation strength reaching the child node through the link
          input_activation_strength = current_node_activation_strength * get_link_strength(link['weight']) * ACTIVATION_DECAY
          # place the child into the time queue according to the computed time (for optimization we could have a sequence or custom struct where all children of the same act time are grouped together (but that would limit us to a stepwise situation), it could even just be a set where the inputs are numbers. or a deck so we can pop efficiently)
          queue_node_activation(tq, time_until_activation, input_activation_strength, child)
    return activation_history


def test_singleton():
  # setup the graph and whatnot
  g = nx.DiGraph()
  # setup a schema
  schema = ['value_prop']
  # add a node for each types in the schema
  for node_type in schema:
    name = node_type
    g.add_node(name, **{'name': name, 'weight': 0})
    g.nodes[name]['type'] = node_type
  print(f'\n{g}')
  # set the starting state, that is, specify the starting nodes and their starting activation inputs
  start_state = [(g.nodes['value_prop'], 1)]
  # kick off the algo
  out = algo(g, start_state, schema)
  print(out)
test_singleton()

def test_two_node_graph():
  # setup
  g = nx.DiGraph()
  schema = ['b', 'c']
  # add a node for each types in the schema
  for node_type in schema:
    name = node_type
    g.add_node(name, **{'name': name, 'weight': 0})
    g.nodes[name]['type'] = node_type
  g.add_edges_from([('b', 'c', {'weight': 0.2})])
  print(f'\n{g}')
  start_state = [(g.nodes['b'], 1)]
  # kick off the algo
  out = algo(g, start_state, schema)
  print(out)
test_two_node_graph()

def test_three_node_graph():
  # setup
  g = nx.DiGraph()
  schema = ['a', 'b', 'c']
  # add a node for each types in the schema
  for node_type in schema:
    name = node_type
    g.add_node(name, **{'name': name, 'weight': 0})
    g.nodes[name]['type'] = node_type
  g.add_edges_from([('b', 'c', {'weight': 1}), ('b', 'a', {'weight': 1})]) # because link (b,c) has weight 0, the transfer is instantaneous and so c will activate at the same time as b (at time 0).
  print(f'\n{g}')
  start_state = [(g.nodes['b'], 1)]
  # kick off the algo
  out = algo(g, start_state, schema)
  print(out)
test_three_node_graph()

def test_outward():
  # setup
  g = nx.DiGraph()
  schema = ['a', 'b', 'c', 'd', 'e']
  # add a node for each types in the schema
  for node_type in schema:
    name = node_type
    g.add_node(name, **{'name': name, 'weight': 0})
    g.nodes[name]['type'] = node_type
  # a <-- b <-- c --> d --> e
  g.add_edges_from([('b', 'a', {'weight': 1}), ('c', 'b', {'weight': 1}), ('c', 'd', {'weight': 1}), ('d', 'e', {'weight': 2})])
  print(f'\n{g}')
  start_state = [(g.nodes['c'], 1)]
  # kick off the algo
  out = algo(g, start_state, schema)
  print(out)
test_outward()


