# NOTE: This class is NOT thread safe.
# PriorityQueue uses an internal heap to optimize placing and retrieving items.
from asyncio import PriorityQueue


class TimeQueue (PriorityQueue):
    def add_node(self, new_node, activation_time):
        """ Add a new node to the queue (in time order).
            new_node: the node to be added
            activation_time: the time that the node will get activated
        """
        self.put((activation_time, new_node))

    def pop_node(self):
        """ Get the next node to be activated. """
        (activation_time, node) = self.get_nowait()
        return (activation_time, node)
