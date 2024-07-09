# Here we house the main Spreading Activation algorithm.

# imports
import networkx as nx
from . import graph as g

# define constants
starting_activation_strength = 1.0
activation_decay = 0.8
schema = ['a', 'b', 'c']


class TimeQueue (deque):
    def add_node(new_node):
        """ Add a new node to the queue (in time order). """
        # get the index for the new node
        index = new_node.steps_until_activation
        # get the family of nodes to be activated along with the new node
        node_family = self[index]
        # insert the new node with its family
        node_family.add(new_node)

    def pop_node(self):
        """ Get the next node to be activated. """
        next_family = self[0]
        # if the family is empty, discard it entirely
        while not next_family:
            self.popleft()
            next_family = self[0]
        # take any node from the family (they all activate at the same time so it doesn't matter which you take)
        next_node = next_family.pop()
        return next_node


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
    """ The spreading activation algorithm """
    tq = TimeQueue()
    # start at the start node
    # put the start node in the time queue
    tq.add_node(start_node)
    # time is 0 (0 seconds or 0 steps)
    # iteratively apply this algo...
    while True:
        # take the first node out of the time queue (hence, the first event since nodes are ordered)
        current_node = tq.pop_node()
        # intersect its children with valid types to spread to. (note that this could be a preprocessing step if we don't want to dynamically change strategies)
        children = set(current_node.children)
        valid_types = get_valid_types_following(current_node.type)
        # obtain the valid children
        valid_children = children.intersect(valid_types)
        # for each valid child, calculate whether it will activate
        for child in children:
            # see if it will activate
            input_activation_strength = current_node.activation_strength * 0.8
            will_activate = child.get_activation_strength(input_activation_strength) > threshold 
            # if it will activate then calculate the seconds/steps until activation (a whole number 1 or higher)
            if not will_activate:
                continue
            steps_until_activation = child.get_steps_until_activation()
            # activation time of the node is equal to current seconds plus the seconds until activation
            # place the child into the time queue according to the computed time (for optimization we could have a sequence or custom struct where all children of the same act time are grouped together, it could even just be a set where the inputs are numbers. or a deck so we can pop efficiently)
            child.steps_until_activation = steps_until_activation # or just pass it in
            tq.add_node(child)
            # add 1 second/step to current time
            current_time += 1

    

def main():
    # setup the graph and whatnot

    # kick off the algo
    algo(graph, types,)

if __name__ == '__main__':
    main()

    
