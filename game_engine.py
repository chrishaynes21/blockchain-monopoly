import random
from board import Board
from draw import Draw
from player import Player, PlayerState, Bank
from blockchain import BlockChain


class Monopoly:
    def __init__(self, num_players):
        self.board = Board()
        self.draw = Draw()
        self.blockchain = BlockChain()
        self.banker = Bank()
        self.num_players = num_players
        self.players = []
        for player_index in range(num_players):
            name = input('Enter Player {}\'s Name: '.format(player_index + 1))
            self.players.append(Player(name, player_index + 1))

        # Initialize the accounts of all players with 1500 Monopoly Coin
        self.blockchain.initialize_accounts(self.players)

        # Initialize all properties. By default the owner of all properties is the bank
        self.blockchain.initialize_properties(self.board.get_all_properties())

    @staticmethod
    def roll_dice():
        return random.randint(1, 6), random.randint(1, 6)

    def play_game(self, automatic=True):
        if automatic:
            while not self.game_over():
                for player in self.players:
                    self.serve_turn(player, 0)
        else:
            game_ended = False
            while not game_ended:
                for player in self.players:
                    cont = input('\nContinue? Y/N: ')
                    if cont == 'Y' or cont == 'y':
                        self.serve_turn(player, 0)
                    else:
                        winner = None
                        highest_assets = 0
                        for player in self.players:
                            if not player.state == PlayerState.DONE:
                                assets = player.add_assets(self.blockchain, self.board)
                                if highest_assets < assets:
                                    winner = player
                                    highest_assets = assets
                        game_ended = True
                        print('Winner is {}. Game Ended. Bye!'.format(winner))

    # ---------- Serving Methods ------------
    def serve_turn(self, player, num_doubles):
        if num_doubles == 0:
            print('\n{} is up! Starting balance: ${}'.format(str(player), player.get_balance(self.blockchain)))

        roll = self.roll_dice()
        print('{} rolled: {}'.format(str(player), roll))
        if num_doubles == 2 and roll[0] == roll[1]:
            self.go_to_jail(player)
        elif player.in_jail:
            self.serve_jail(player, roll)
        else:
            trade = input('Would you like to make a trade? Y/N: ')
            if trade == 'Y' or trade == 'y':
                self.serve_trade(player)
            self.serve_normally(player, roll)
            if roll[0] == roll[1]:
                self.serve_turn(player, num_doubles + 1)

        if num_doubles == 0:
            print('{}\'s turn is over! Ending balance: ${}'.format(str(player), player.get_balance(self.blockchain)))

    def serve_normally(self, player, roll):
        position = (player.position + roll[0] + roll[1]) % 40
        space = self.board.get_property_at_index(position)
        print('{} landed on: {}'.format(str(player), space.name))
        self.move_player_to(player, position)

        if space.type == 'Draw':
            self.serve_draw(player, space)
        elif space.type == 'Special':
            self.serve_special_space(player, space)
        else:
            self.serve_property(player, space)

    def serve_jail(self, player, roll):
        player.jail_rolls += 1
        if roll[0] == roll[1] or player.jail_rolls == 3:
            print('{} got out of Jail!'.format(str(player)))
            player.jail_rolls = 0
            player.in_jail = False
            self.serve_normally(player, roll)
        else:
            print('{} is still in Jail!'.format(str(player)))

    def serve_draw(self, player, space):
        draw = self.draw.draw_card(space.draw_type)
        print('{} drew: {}'.format(str(player), draw.description))

        if draw.type == 'Pay':
            player.pay(self.banker, draw.amount, self.blockchain)
        elif draw.type == 'Pay All':
            for player_ in self.players:
                if player_ != player:
                    player.pay(player_, draw.amount, self.blockchain)
        elif draw.type == 'Receive':
            self.banker.pay(player, draw.amount, self.blockchain)
        elif draw.type == 'Receive All':
            for player_ in self.players:
                if player_ != player:
                    player_.pay(player, draw.amount, self.blockchain)
        elif draw.type == 'Move':
            if draw.name != 'Go to Jail':
                move_space = self.board.get_property_at_index(draw.index)
                print('{} moved to: {}'.format(str(player), str(move_space)))
                self.move_player_to(player, move_space.index)
                if move_space.type != 'Draw' and move_space.type != 'Special':
                    self.serve_property(player, move_space)
            else:
                self.go_to_jail(player)
        elif draw.type == 'Special':
            if draw.name == 'Street Repairs' or draw.name == 'Property Repairs':
                houses = 0
                hotels = 0
                for index in self.blockchain.get_all_properties(player):
                    houses += self.blockchain.get_houses(index)
                    hotels += self.blockchain.get_hotel(index)
                print('{} has {} houses and {} hotels and must.'.format(player, houses, hotels))
                player.pay(self.banker, houses * draw.house_amount + hotels * draw.hotel_amount, self.blockchain)
            elif draw.name == 'Advance to Utility':
                if abs(player.position - 12) >= abs(player.position - 28):
                    index = 28
                else:
                    index = 12
                self.move_player_to(player, index)
                print('{} moved to: {}'.format(player, self.board.get_property_at_index(index).name))
                self.serve_property(player, self.board.get_property_at_index(index), 10)
            elif draw.name == 'Advance to Railroad 1' or draw.name == 'Advance to Railroad 2':
                if player.position == 7:
                    index = 5
                elif player.position == 22:
                    index = 25
                else:
                    index = 35
                self.move_player_to(player, index)
                print('{} moved to: {}'.format(player, self.board.get_property_at_index(index).name))
                self.serve_property(player, self.board.get_property_at_index(index), 10)

    def serve_special_space(self, player, space):
        if space.name == 'Income Tax':
            decision = input('Pay 10% of assets or $200: Y for 10%, N for $200: ')
            if decision == 'Y' or decision == 'y':
                player.pay(self.banker, player.add_assets(self.blockchain, self.board) // 10, self.blockchain)
            else:
                player.pay(self.banker, 200, self.blockchain)
        elif space.name == 'Luxury Tax':
            print('Pay $75 for Luxury Tax')
            player.pay(self.banker, 75, self.blockchain)

    def serve_property(self, player, space, multiplier=1):
        owner_address = self.blockchain.get_property_owner(space.index)
        if owner_address == self.blockchain.get_account(self.banker):
            self.serve_banker(owner_address, player, space)
        elif owner_address == self.blockchain.get_account(player):
            self.serve_owner(owner_address, player, space)
        else:
            self.serve_other_owner(multiplier, owner_address, player, space)

    def serve_banker(self, owner_address, player, space):
        decision = input('{} is unowned! It costs ${}. Want to see a description? Y/N: '.format(space, space.price))
        if decision == 'Y' or decision == 'y':
            self.describe_property(space)
        decision = input(
            'Current Balance: ${}. Would you like to buy it? Y/N: '.format(player.get_balance(self.blockchain)))
        if decision == 'Y' or decision == 'y':
            if self.blockchain.change_ownership(owner_address, player, space.index, space.price):
                print('Congrats! You bought {}!'.format(space))
            else:
                print('Couldn\'t buy {}... :('.format(space))

    def serve_owner(self, owner_address, player, space):
        print('Welcome back Mr.{}!'.format(player))
        if space.type == 'Property':
            if self.blockchain.get_mortgage(space.index):
                decision = input('{} is mortgaged. Un-mortgage for ${}? Current Balance: ${} Y/N: '.format(
                    space, space.mortgage, player.get_balance(self.blockchain)))
                if decision == 'Y' or decision == 'y':
                    if self.blockchain.un_mortgage(player, space.index, space.mortgage):
                        print('{} was un-mortgaged for ${}!'.format(space, space.mortgage))
                    else:
                        print('Couldn\'t un-mortgage {}'.format(space))
            else:
                other_properties = [s for s in self.board.monopolies[space.group] if s != space.index]
                monopoly = True
                for index in other_properties:
                    if self.blockchain.get_property_owner(index) != owner_address:
                        monopoly = False
                        break
                if monopoly:
                    decision = input(
                        'You have a monopoly on the {} group! Buy houses and hotels? Y/N: '.format(space.group))
                    if decision == 'Y' or decision == 'y':
                        for index in self.board.monopolies[space.group]:
                            self.serve_houses_hotels(player, index)

    def serve_other_owner(self, multiplier, owner_address, player, space):
        owner = None
        for player_ in self.players:
            if self.blockchain.get_account(player_) == owner_address:
                owner = player_
                break
        if not self.blockchain.get_mortgage(space.index):
            if space.type == 'Utility':
                other_utility = 28 if space.index == 12 else 12
                if owner_address == self.blockchain.get_property_owner(other_utility) or multiplier == 10:
                    rent = sum(self.roll_dice()) * 10
                else:
                    rent = sum(self.roll_dice()) * 4
            elif space.type == 'Station':
                rent = space.standard_rent
                other_stations = [s for s in [5, 15, 25, 35] if s != space.index]
                for station_index in other_stations:
                    if owner_address == self.blockchain.get_property_owner(station_index):
                        rent += space.standard_rent
            else:
                rent = space.standard_rent
                layout = (self.blockchain.get_houses(space.index), self.blockchain.get_hotel(space.index))
                if layout[0]:
                    if layout[0] == 1:
                        rent = space.one_house_rent
                    elif layout[0] == 2:
                        rent = space.two_house_rent
                    elif layout[0] == 3:
                        rent = space.three_house_rent
                    else:
                        rent = space.four_house_rent
                elif layout[1]:
                    rent = space.hotel_rent
                else:
                    other_properties = [s for s in self.board.monopolies[space.group] if s != space.index]
                    monopoly = True
                    for index in other_properties:
                        if self.blockchain.get_property_owner(index) != owner_address:
                            monopoly = False
                            break
                    if monopoly:
                        rent *= 2
            print('Uh oh. You owe {} ${}.'.format(owner, rent * multiplier))
            player.pay(owner, rent * multiplier, self.blockchain, critical=True, board=self.board)
        else:
            print('You lucky duck, {} is mortgaged. Enjoy your free stay!'.format(space))

    def serve_houses_hotels(self, player, index):
        curr = self.board.get_property_at_index(index)
        layout = (self.blockchain.get_houses(index), self.blockchain.get_hotel(index))
        print('{} has {} houses and {} hotels.'.format(curr.name, layout[0], layout[1]))
        print(
            'Houses and hotels cost {}. Current Balance: ${}'.format(curr.houses, player.get_balance(self.blockchain)))
        if layout[0] < 4 and layout[1] == 0:  # Can buy houses only here
            while True:
                amount = int(input('Enter number of houses to buy: '))
                if amount <= 0:
                    break
                elif amount + layout[0] <= 4:
                    if self.blockchain.buy_houses(player, index, amount, curr.houses * amount):
                        print('You bought {} houses for {} for ${}!'.format(amount, curr.name, curr.houses * amount))
                        break
                    else:
                        print('You can\'t afford that many, try again.')
                else:
                    print('Too many houses, try again.')
        elif layout[0] == 4 and layout[1] == 0:  # Can only buy a hotel
            decision = input('Buy Hotel? Y/N: ')
            if decision == 'Y' or decision == 'y':
                if self.blockchain.buy_hotel(player, index, curr.houses):
                    print('You bought a hotel for {} for ${}!'.format(curr.name, curr.houses))
                else:
                    print('You can\'t afford a hotel.')
        else:  # Already has a hotel, so they can't buy anything
            print('You already have a hotel at {}!'.format(curr.name))

    def serve_trade(self, player):
        all_properties = player.describe_all_properties(self.blockchain, self.board)  # Prints all properties as well
        keep_trading = True
        while keep_trading:
            trade_index = int(input('Index to trade: '))
            if trade_index in all_properties:
                buyer = int(input('Enter player number to trade with: '))
                if buyer - 1 < len(self.players) and buyer > 0:
                    buyer = self.players[buyer - 1]
                    sell_property = self.board.get_property_at_index(trade_index)
                    price = int(input('Enter amount to offer: '))
                    buyer_decision = input('Would {} like to buy {} for ${}? Y/N: '.format(buyer, sell_property, price))
                    if buyer_decision == 'Y' or buyer_decision == 'y':
                        player.sell_property(buyer, sell_property, price, self.blockchain)
                    else:
                        print('{} rejected the offer.'.format(buyer))
                else:
                    print('{} is not a valid player index, try again.'.format(buyer))
            else:
                print('{} is not an index you can trade, try again tiger.'.format(trade_index))
            decision = input('Continue trading? Y/N: ')
            if not decision == 'Y' and not decision == 'y':
                keep_trading = False

    # Describes a property's rent and mortgage
    @staticmethod
    def describe_property(space):
        if space.type == 'Utility':
            print('     If one utility is owned rent is 4 times amount shown on dice.\n' +
                  '     If both utilities are owned rent is 10 times amount shown on dice.')
        elif space.type == 'Station':
            print('     Rent ${}\n'.format(space.standard_rent) +
                  '     If 2 stations are owned ${}\n'.format(space.standard_rent * 2) +
                  '     If 3 stations are owned ${}\n'.format(space.standard_rent * 3) +
                  '     If 4 stations are owned ${}'.format(space.standard_rent * 4))
        else:
            print('     Color Group: {}\n'.format(space.group) +
                  '     Rent ${}\n'.format(space.standard_rent) +
                  '     With 1 House ${}\n'.format(space.one_house_rent) +
                  '     With 2 Houses ${}\n'.format(space.two_house_rent) +
                  '     With 3 Houses ${}\n'.format(space.three_house_rent) +
                  '     With 4 Houses ${}\n'.format(space.four_house_rent) +
                  '     With Hotel ${}'.format(space.hotel_rent))
        print('     Mortgage Value: ${}'.format(space.mortgage))

    # Moves a player to the given index. If at 30, the player goes to jail
    def move_player_to(self, player, index):
        if index < player.position:
            print('{} passed Go!'.format(str(player)))
            self.banker.pay(player, 200, self.blockchain)
        if index == 30:
            self.go_to_jail(player)
        else:
            player.position = index

    @staticmethod
    def go_to_jail(player):
        print('{} went to Jail!'.format(player))
        player.in_jail = True
        player.position = 10

    def game_over(self):
        finished_players = 0
        for player in self.players:
            if player.state == PlayerState.DONE:
                finished_players += 1
        if finished_players - 1 == len(self.players):
            return True
        else:
            return False


if __name__ == '__main__':
    num_of_players = int(input('Enter number of players: '))
    game = Monopoly(num_of_players)
    game.play_game()
