import random
from xml.etree import ElementTree


class Draw:
    def __init__(self):
        self.community_chest = []
        self.chance = []
        self.community_index = 0
        self.chance_index = 0
        tree = ElementTree.parse('draw.xml')
        cards = tree.getroot()
        for next_card in cards:
            card = Card(next_card)
            if card.draw_type == 'community_chest':
                self.community_chest.append(card)
            if card.draw_type == 'chance':
                self.chance.append(card)
        random.shuffle(self.community_chest)
        random.shuffle(self.chance)

    def draw_card(self, draw_type):
        if draw_type == 'Community Chest':
            index = self.community_index
            self.community_index = (self.community_index + 1) % len(self.community_chest)
            return self.community_chest[index]
        elif draw_type == 'Chance':
            index = self.chance_index
            self.chance_index = (self.chance_index + 1) % len(self.chance)
            return self.chance[index]
        else:
            print('Error: Illegal draw type.')


class Card:
    def __init__(self, element):
        self.draw_type = element.tag
        self.name = element.attrib['name']
        self.type = element.find('type').text
        self.description = element.find('description').text
        if self.type == 'Pay' or self.type == 'Pay All' or self.type == 'Receive' or self.type == 'Receive All':
            self.amount = int(element.find('amount').text)
        elif self.type == 'Move':
            self.index = int(element.find('index').text)
        elif self.type == 'Special':
            if self.name == 'Street Repairs' or self.name == 'Property Repairs':
                self.house_amount = int(element.find('amount').find('house').text)
                self.hotel_amount = int(element.find('amount').find('hotel').text)
            elif self.name == 'Advance to Utility' or self.name == 'Advance to Railroad 1' or self.name == 'Advance to ' \
                                                                                                         'Railroad 2':
                self.location = element.find('location').text
                self.multiplier = int(element.find('multiplier').text)

    def __repr__(self):
        return self.name


if __name__ == '__main__':
    draw = Draw()
    print(draw.community_chest)
    print(draw.chance)
    print(draw.draw_card('Community Chest').description)
    print(draw.draw_card('Chance').description)
