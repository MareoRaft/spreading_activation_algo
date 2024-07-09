# imports
import sys
import time
import asyncio

import networkx as nx


# version reporting
print(f'python version: {sys.version}')
print(f'networkx version: {nx.__version__}')


def test_is_empty():
	g = nx.Graph()
	g.add_node('a')
  # it's still "empty" because it has no edges
	assert nx.is_empty(g)
test_is_empty()

def test_create_edge():
  g = nx.Graph()
  g.add_edge('b', 'c')
  assert 'b' in g
test_create_edge()

def test_add_attr_to_node():
  g = nx.Graph()
  g.add_node('a')
  a = g.nodes['a']
  a['strength'] = 2.
  assert a['strength'] == 2.
test_add_attr_to_node()

# NOTE: This class is NOT thread safe.
# PriorityQueue uses an internal heap to optimize placing and retrieving items.
from asyncio import PriorityQueue


class TimeQueue (PriorityQueue):

  def __str__(self) -> str:
    """ Returns a string representation of the queue. NOTE that you should not use this in production as iterating through the entire queue and sorting it is an expensive operation. """
    ordered_list = self.as_ordered_list()
    string = 'TimeQueue' + str(ordered_list)
    return string

  def as_ordered_list(self):
    return sorted(self._queue)

  def __bool__(self):
    return not self.empty()

  async def add_node(self, activation_time, output_activation_strength, node_name):
      """ Add a new node to the queue (in time order). It is assumed that the input is a tuple where the first value is the time. """
      await self.put((activation_time, output_activation_strength, node_name))

  def pop_node(self):
      """ Get the next node to be activated. """
      return self.get_nowait()

async def test_as_ordered_list():
  # two items
  tq = TimeQueue()
  await tq.add_node(2, None, 'a')
  await tq.add_node(1, None, 'b')
  ol = tq.as_ordered_list()
  assert ol == [(1, None, 'b'), (2, None, 'a')]
  # many items
  tq = TimeQueue()
  await tq.add_node(3, None, 'a')
  await tq.add_node(1, None, 'b')
  await tq.add_node(2, None, 'c')
  await tq.add_node(4, None, 'd')
  await tq.add_node(0, None, 'e')
  ol = tq.as_ordered_list()
  assert ol == [(0, None, 'e'), (1, None, 'b'), (2, None, 'c'), (3, None, 'a'), (4, None, 'd')]
await test_as_ordered_list()

async def test_tq():
  tq = TimeQueue()
  # test that queue as a boolean is False
  assert bool(tq) == False
  await tq.add_node(2., 1, 'a')
  (time, strength, node) = tq.pop_node()
  assert time == 2.
  assert strength == 1
  assert node == 'a'
await test_tq()



# define constants
activation_decay = 0.8
threshold = 0.05


def get_valid_types_following(node_type, schema):
    """ Find the valid types immediately following a specific type in the schema """
    valid_types = set()
    type_index = schema.index(node_type)
    left_index = type_index - 1
    right_index = type_index + 1
    if left_index >= 0:
        valid_types.add(schema[left_index])
    if right_index < len(schema):
        valid_types.add(schema[right_index])
    return valid_types


def get_node_strength(weight):
  # Node strength is s = 1/2^w.  Node weight is w = -ln_2(s).
  return 1 / 2 ** weight


def get_link_strength(weight):
  # Link strength is s = 1/2^w.  Link weight is w = -ln_2(s).
  return 1 / 2 ** weight


def get_link_transfer_time(weight):
  # Link transfer time is equal to link weight.
  return weight


async def queue_node_activation(tq, activation_time, input_activation_strength, node):
  will_activate = input_activation_strength > threshold 
  # if it will activate then calculate the seconds/steps until activation (a whole number 1 or higher)
  if not will_activate:
    return
  # Activate the node (deferred).
  # -- assign the node it's own activation strength
  output_activation_strength = input_activation_strength * get_node_strength(node['weight'])
  # add the node to the queue
  await tq.add_node(activation_time, output_activation_strength, node['name'])


# Input parameters are the graph (nodes, edges, node weights, edge weights, node types, and schema)
async def algo(graph, start_state, schema):
    """ The ONE-BY-ONE spreading activation algorithm.
    This algorithm is simpler, slower, and more general.  It does not require a stepwise system, and hence could model a real time scenario.
    """
    activation_history = []
    tq = TimeQueue()
    # Put the starting nodes in the time queue. It will be the first to activate.
    for (start_node, start_input_activation_strength) in start_state:
      await queue_node_activation(tq, activation_time=0, input_activation_strength=start_input_activation_strength, node=start_node)
    # current time is 0 (0 seconds)
    current_time = 0
    # start timer
    start_time = time.time()
    # Iteratively apply this algo until you've exhausted all reachable nodes.
    while tq:
      print(f'tq: {tq}')
      # take the first node out of the time queue (hence, the first event since nodes are ordered)
      (current_node_activation_time, current_node_activation_strength, current_node_name) = tq.pop_node()
      current_node = graph.nodes[current_node_name]
      activation_history.append((current_node_activation_time, current_node_activation_strength, current_node['name']))
      # update the current time
      current_time = current_node_activation_time
      # intersect its children with valid types to spread to. (note that this could be a preprocessing step if we don't want to dynamically change strategies)
      valid_types = get_valid_types_following(current_node['type'], schema)
      children = [graph.nodes[x] for x in graph.successors(current_node['name'])]
      valid_children = [x for x in children if x['type'] in valid_types]
      # for each valid child, calculate whether it will activate
      for child in valid_children:
        # Conditionally activate the node. (queue_node_activation will only activate the node if strength above threshold)
        link = graph.edges[current_node['name'], child['name']]
        time_until_activation = get_link_transfer_time(link['weight'])
        # activation time of the node is equal to current seconds plus the seconds until activation
        activation_time = current_time + time_until_activation
        # TODO: add edge weight to calculation
        input_activation_strength = current_node_activation_strength * get_link_strength(link['weight']) * activation_decay
        # place the child into the time queue according to the computed time (for optimization we could have a sequence or custom struct where all children of the same act time are grouped together, it could even just be a set where the inputs are numbers. or a deck so we can pop efficiently)
        await queue_node_activation(tq, activation_time, input_activation_strength, child)
    end_time = time.time()
    elapsed_time = end_time - start_time
    return {'elapsed_time': elapsed_time, 'activation_history': activation_history}


async def test_basic():
  # setup the graph and whatnot
  g = nx.DiGraph()
  # setup a schema
  schema = ['value_prop']
  # add a node for each types in the schema
  for node_type in schema:
    name = node_type
    g.add_node(name, **{'name': name, 'weight': 0})
    g.nodes[name]['type'] = node_type
  # set the starting state, that is, specify the starting nodes and their starting activation inputs
  start_state = [(g.nodes['value_prop'], 1)]
  # kick off the algo
  out = await algo(g, start_state, schema)
  print(out)
# await test_basic()

async def test_two():
  # setup
  g = nx.DiGraph()
  schema = ['b', 'c']
  # add a node for each types in the schema
  for node_type in schema:
    name = node_type
    g.add_node(name, **{'name': name, 'weight': 0})
    g.nodes[name]['type'] = node_type
  g.add_edges_from([('b', 'c', {'weight': 0})])
  print(f'\n{g}')
  start_state = [(g.nodes['b'], 1)]
  # kick off the algo
  out = await algo(g, start_state, schema)
  print(out)
# await test_two()

async def test_three():
  # setup
  g = nx.DiGraph()
  schema = ['a', 'b', 'c']
  # add a node for each types in the schema
  for node_type in schema:
    name = node_type
    g.add_node(name, **{'name': name, 'weight': 0})
    g.nodes[name]['type'] = node_type
  g.add_edges_from([('b', 'c', {'weight': 0}), ('b', 'a', {'weight': 1})])
  print(f'\n{g}')
  start_state = [(g.nodes['b'], 1)]
  # kick off the algo
  out = await algo(g, start_state, schema)
  print(out)
# await test_three()

async def test_outward():
  # setup
  g = nx.DiGraph()
  schema = ['a', 'b', 'c', 'd', 'e']
  # add a node for each types in the schema
  for node_type in schema:
    name = node_type
    g.add_node(name, **{'name': name, 'weight': 0})
    g.nodes[name]['type'] = node_type
  g.add_edges_from([('b', 'a', {'weight': 1}), ('c', 'b', {'weight': 1}), ('c', 'd', {'weight': 1}), ('d', 'e', {'weight': 2})])
  print(f'\n{g}')
  start_state = [(g.nodes['c'], 1)]
  # kick off the algo
  out = await algo(g, start_state, schema)
  print(out)
await test_outward()




