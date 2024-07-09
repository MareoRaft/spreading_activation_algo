# Here we house the main Spreading Activation algorithm.
#
# This is the ONE-BY-ONE solution which is simpler and generalized to work with real times, not just whole
# times.  In other words, it will even work for a non-stepwise network.


# imports
import networkx as nx
# from .graph import Node, Edge
from .time_queue import TimeQueue


# define constants
starting_activation_strength = 1.0
activation_decay = 0.8
schema = ['a', 'b', 'c']


def get_valid_types_following(node_type):
    """ Find the valid types immediately following a specific type in the schema """
    valid_types = set()
    type_index = schema.indexof(node_type)
    left_index = type_index - 1
    right_index = type_index + 1
    if left_index >= 0:
        valid_types.add(left_index)
    if right_index < len(schema):
        valid_types.add(right_index)
    return valid_types
    

def algo(graph, start_node, threshold):
    """ The ONE-BY-ONE spreading activation algorithm """
    tq = TimeQueue()
    # Put the start node in the time queue. It will be the first to activate.
    tq.add_node(start_node)
    # current time is 0 (0 seconds)
    time = 0
    # Iteratively apply this algo until you've exhausted all reachable nodes.
    while tq:
        # take the first node out of the time queue (hence, the first event since nodes are ordered)
        current_node = tq.pop_node()
        # intersect its children with valid types to spread to. (note that this could be a preprocessing step if we don't want to dynamically change strategies)
        children = set(current_node.children)
        valid_types = get_valid_types_following(current_node.type)
        # obtain the valid children
        valid_children = {x for x in children if x.type in valid_types}
        # for each valid child, calculate whether it will activate
        for child in children:
            # see if it will activate
            # TODO: add edge weight to calculation
            input_activation_strength = current_node.activation_strength * 0.8 # * current_node.edge_to_child_weight
            will_activate = input_activation_strength > threshold 
            # if it will activate then calculate the seconds/steps until activation (a whole number 1 or higher)
            if not will_activate:
                continue
            # activate the child
            child_activation_strength = child.get_activation_strength(input_activation_strength)
            child.activation_strength = child_activation_strength
            time_until_activation = child.get_time_until_activation()
            # activation time of the node is equal to current seconds plus the seconds until activation
            activation_time = time + time_until_activation
            # place the child into the time queue according to the computed time (for optimization we could have a sequence or custom struct where all children of the same act time are grouped together, it could even just be a set where the inputs are numbers. or a deck so we can pop efficiently)
            tq.add_node(child, activation_time)



def main():
    # setup the graph and whatnot

    # kick off the algo
    algo(graph, types,)

if __name__ == '__main__':
    main()

    
