from enum import Enum


class PlayerState(Enum):
    PLAYING = 1
    DONE = 2


class Player:
    def __init__(self, name, account_index):
        self.name = name
        self.account_index = account_index
        self.state = PlayerState.PLAYING
        self.position = 0
        self.in_jail = False
        self.jail_rolls = 0

    def __repr__(self):
        return self.name

    # ------ Getter Methods for blockchain ------
    # Methods in this section view the blockchain, and will not modify it
    def get_balance(self, blockchain):
        return blockchain.get_balance(self)

    def get_properties(self, blockchain):
        return blockchain.get_all_properties(self)

    def add_assets(self, blockchain, board):
        assets = self.get_balance(blockchain)
        for index in self.get_properties(blockchain):
            current_property = board.get_property_at_index(index)
            if blockchain.get_mortgage(index):
                assets += current_property.mortgage
            else:
                assets += current_property.price
                if current_property.type == 'Property':
                    assets += (blockchain.get_houses(index) + blockchain.get_hotel(index)) * current_property.houses
        print('{}\'s total assets are worth: ${}'.format(self, assets))
        return assets

    def describe_all_properties(self, blockchain, board):
        all_properties = self.get_properties(blockchain)
        for index in all_properties:
            property_str = '     Index: {:2} Property: {:<25} Houses: {} Hotel: {} Mortgaged: {}'
            current_property = board.get_property_at_index(index)
            if current_property.type == 'Property':
                print(property_str.format(index, current_property.name, blockchain.get_houses(index), blockchain.get_hotel(index),
                                          blockchain.get_mortgage(index)))
            else:
                print(property_str.format(index, current_property.name, '-', '-', blockchain.get_mortgage(index)))
        return all_properties

    # -------- Transfer methods for blockchain --------------
    # Methods in this section will fire a transaction in the blockchain when called.
    def pay(self, player, amount, blockchain, critical=False, board=None):
        if str(player) == 'Banker':
            success = blockchain.pay_to_bank(self, amount)
        else:
            success = blockchain.transfer_coin(self, player, amount)

        if success:
            print('{} payed {} ${}'.format(self, player, amount))
            return True
        else:
            if not critical:
                print('{} could not pay {} ${}, insufficient funds'.format(self, player, amount))
                return False
            else:
                if self.add_assets(blockchain, board) < amount:
                    print('{} cannot pay and is finished for the game. {} gets all assets.'.format(self, player))
                    self.transfer_all_assets(player, blockchain)
                    self.state = PlayerState.DONE
                else:
                    print('This is a critical transaction that must be payed. Beginning mortgaging process.')
                    self.mortgage_to_target_value(blockchain, board, amount)
                    self.pay(player, amount, blockchain, critical, board)

    def sell_property(self, buyer, sell_property, price, blockchain):
        if blockchain.change_ownership(blockchain.get_account(self), buyer, sell_property.index, price):
            print('{} traded {} to {} for ${}!'.format(self, buyer, sell_property, price))
        else:
            print('Couldn\'t sell {} to {} for ${}.'.format(sell_property, buyer, price))

    def transfer_all_assets(self, player, blockchain):
        self.pay(player, self.get_balance(blockchain), blockchain)  # Give all money
        for index in self.get_properties(blockchain):  # Transfer all properties for free
            blockchain.change_ownership(blockchain.get_account(self), player, index, 0)

    def mortgage_to_target_value(self, blockchain, board, target_amount):
        all_properties = self.describe_all_properties(blockchain, board)
        while self.get_balance(blockchain) < target_amount:
            index_to_edit = int(input('Index to edit: '))
            if index_to_edit in all_properties:
                self.edit_property(blockchain, board, index_to_edit)
                print('Current Balance: ${}'.format(self.get_balance(blockchain)))

    def edit_property(self, blockchain, board, index_to_edit):
        prop_edit = board.get_property_at_index(index_to_edit)
        option = int(
            input('What do you want to do? (1) - Mortgage property (2) - Sell Houses (3) - Sell Hotel' +
                  ' (4) - Unmortgage (5) - Buy Houses and Hotels: '))
        if option == 1:
            houses = blockchain.get_houses(index_to_edit)
            hotel = blockchain.get_hotel(index_to_edit)
            if houses:
                blockchain.sell_houses(self, index_to_edit, houses, prop_edit.houses * houses // 2)
            elif hotel:
                blockchain.sell_hotel(self, index_to_edit, prop_edit.houses // 2)
            if blockchain.mortgage(self, index_to_edit, prop_edit.mortgage):
                print('Successfully mortgaged {}'.format(prop_edit))
        elif option == 2:
            num_houses = int(input('How many houses would you like to sell?: '))
            if num_houses <= blockchain.get_houses(index_to_edit):
                if blockchain.sell_houses(self, index_to_edit, num_houses, prop_edit.houses * num_houses // 2):
                    print('Successfully sold {} houses for {}'.format(num_houses, prop_edit))
            else:
                print('{} has no houses!'.format(prop_edit))
        elif option == 3:
            if blockchain.get_hotel(index_to_edit):
                if blockchain.sell_hotel(self, index_to_edit, prop_edit.houses // 2):
                    print('Successfully sold hotel for {}'.format(prop_edit))
            else:
                print('{} has no hotels!'.format(prop_edit))
        elif option == 4:
            if blockchain.get_mortgage(index_to_edit):
                if blockchain.un_mortgage(self, index_to_edit, prop_edit.mortgage):
                    print('Successfully unmortgaged {} for ${}'.format(prop_edit, prop_edit.mortgage))
                else:
                    print('Could not unmortgage {}.'.format(prop_edit))
            else:
                print('{} is not mortgaged.'.format(prop_edit))
        elif option == 5:
            other_properties = [s for s in board.monopolies[prop_edit.group] if s != prop_edit.index]
            monopoly = True
            for index in other_properties:
                if blockchain.get_property_owner(index) != blockchain.get_account(self):
                    monopoly = False
                    break
            if monopoly:
                self.buy_houses_hotels(blockchain, prop_edit, index_to_edit)
            else:
                print('You need a monopoly on the {} group to buy houses and hotels'.format(prop_edit.group))
        else:
            print('Invalid option.')

    def buy_houses_hotels(self, blockchain, property, index):
        layout = (blockchain.get_houses(index), blockchain.get_hotel(index))
        print('{} has {} houses and {} hotels.'.format(property.name, layout[0], layout[1]))
        print(
            'Houses and hotels cost {}. Current Balance: ${}'.format(property.houses, self.get_balance(blockchain)))
        if layout[0] < 4 and layout[1] == 0:  # Can buy houses only here
            while True:
                amount = int(input('Enter number of houses to buy: '))
                if amount <= 0:
                    break
                elif amount + layout[0] <= 4:
                    if blockchain.buy_houses(self, index, amount, property.houses * amount):
                        print('You bought {} houses for {} for ${}!'.format(amount, property.name, property.houses * amount))
                        break
                    else:
                        print('You can\'t afford that many, try again.')
                else:
                    print('Too many houses, try again.')
        elif layout[0] == 4 and layout[1] == 0:  # Can only buy a hotel
            decision = input('Buy Hotel? Y/N: ')
            if decision == 'Y' or decision == 'y':
                if blockchain.buy_hotel(self, index, property.houses):
                    print('You bought a hotel for {} for ${}!'.format(property.name, property.houses))
                else:
                    print('You can\'t afford a hotel.')
        else:  # Already has a hotel, so they can't buy anything
            print('You already have a hotel at {}!'.format(property.name))


class Bank:
    def __init__(self):
        self.name = 'Banker'
        self.account_index = 0

    def __repr__(self):
        return self.name

    def pay(self, player, amount, blockchain):
        if blockchain.pay_from_bank(player, amount):
            print('{} payed {} ${}'.format(self, player, amount))
            return True
        else:
            print('{} could not pay {} ${}, insufficient funds'.format(self, player, amount))
            return False
