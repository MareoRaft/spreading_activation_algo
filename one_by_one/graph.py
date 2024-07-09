# Here we implement the Node and Edge classes (ontop of NetworkX)

class Node:

    # weight (builtin)

    def get_activation_strength(self):
        activation_weakness = 1 / 2 ** self.weight
        activation_strength = 1 - activation_weakness
        return activation_strength


class Edge:

    # weight (builtin)

    def get_activation_factor(self):
        # this is a number between 0 and 1, calculated by the input weight

    def get_transfer_time(self):
        # a higher weight means the transfer happens faster
        transfer_time = 1 / 2 ** self.weight
        return transfer_time


    
