from space import Space
from collections import defaultdict
import xml.etree.ElementTree as ElementTree


class Board:
    def __init__(self):
        self.spaces = {}  # Dictionary to hold all spaces and information
        self.board = []  # Holds the order of the board, the data is the name of the space
        self.monopolies = defaultdict(list)  # Holds the indices of the property monopolies, the color group is the key
        tree = ElementTree.parse('spaces.xml')
        spaces = tree.getroot()
        for index in range(0, len(spaces)):
            new_space = Space(spaces[index], index)
            self.spaces[new_space.name] = new_space
            self.board.append(new_space.name)
            if new_space.type == 'Property':
                self.monopolies[new_space.group].append(new_space.index)

    def get_property_at_index(self, index):
        return self.spaces[self.board[index]]

    def get_all_properties(self):
        properties = []
        for space_index in range(0, len(self.board)):
            property_type = self.get_property_at_index(space_index).type
            if property_type != 'Draw' and property_type != 'Special':
                properties.append(space_index)
        return properties


if __name__ == '__main__':
    m = Board()
    print(len(m.board))
    for space_ in m.board:
        space = m.spaces[space_]
        if space.type != 'Property':
            print('{}: {}'.format(space.index, space))
        else:
            print('{}: {} - {}'.format(space.index, space, m.monopolies[space.group]))

    print(m.get_all_properties())
