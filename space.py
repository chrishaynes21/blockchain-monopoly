class Space:
    def __init__(self, element, index):
        self.name = element.attrib['name']
        self.type = element.find('type').text
        self.index = index
        if self.type == 'Property':
            self.group = element.find('group').text
            self.price = int(element.find('price').text)
            self.houses = int(element.find('house_price').text)
            self.standard_rent = int(element.find('rent').find('standard').text)
            self.monopoly_rent = self.standard_rent * 2
            self.one_house_rent = int(element.find('rent').find('one_house').text)
            self.two_house_rent = int(element.find('rent').find('two_houses').text)
            self.three_house_rent = int(element.find('rent').find('three_houses').text)
            self.four_house_rent = int(element.find('rent').find('four_houses').text)
            self.hotel_rent = int(element.find('rent').find('hotel').text)
            self.mortgage = int(self.price / 2)
        elif self.type == 'Station':
            self.price = int(element.find('price').text)
            self.standard_rent = int(element.find('rent').find('standard').text)
            self.mortgage = int(self.price / 2)
        elif self.type == 'Utility':
            self.price = int(element.find('price').text)
            self.mortgage = int(self.price / 2)
        elif self.type == 'Draw':
            self.draw_type = element.find('draw_type').text

    def __repr__(self):
        return self.name
