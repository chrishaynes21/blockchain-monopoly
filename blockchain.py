from solc import compile_files
from web3 import Web3


class BlockChain:
    # ------- Constructor -------
    def __init__(self):
        # Create the connection and compile all contracts.
        # Ganache GUI runs at 127.0.0.1 at port 7545
        self.w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:7545'))
        compiled_contract = compile_files(['monopoly_coin.sol', 'property_management.sol'])
        coin_contract_interface = compiled_contract['monopoly_coin.sol:MonopolyCoin']
        property_contract_interface = compiled_contract['property_management.sol:PropertyManagement']

        # Set the default owner of a contract, which is the Banker at index 0
        # NOTE: The Banker is also the owner of the contract since this account is used to deploy the contract
        self.w3.eth.defaultAccount = self.w3.eth.accounts[0]

        # Instantiate the contracts, getting the hash and receipt for the deployment of the contracts
        MonopolyCoin = self.w3.eth.contract(
            abi=coin_contract_interface['abi'],
            bytecode=coin_contract_interface['bin'])
        coin_tx_hash = MonopolyCoin.constructor().transact()
        coin_tx_receipt = self.w3.eth.waitForTransactionReceipt(coin_tx_hash)

        PropertyManagement = self.w3.eth.contract(
            abi=property_contract_interface['abi'],
            bytecode=property_contract_interface['bin'])
        property_tx_hash = PropertyManagement.constructor(coin_tx_receipt.contractAddress).transact()
        property_tx_receipt = self.w3.eth.waitForTransactionReceipt(property_tx_hash)

        # Now create an instance of the contracts with the banker as the sender
        self.monopolyCoin = self.w3.eth.contract(
            address=coin_tx_receipt.contractAddress,
            abi=coin_contract_interface['abi']
        )

        self.propertyManagement = self.w3.eth.contract(
            address=property_tx_receipt.contractAddress,
            abi=property_contract_interface['abi']
        )

    # General function to get a players account
    def get_account(self, player):
        return self.w3.eth.accounts[player.account_index]

    # ------ Monopoly Coin Functions --------
    def initialize_accounts(self, players):
        account_addresses = []
        for player in players:
            account_addresses.append(self.get_account(player))

        self.monopolyCoin.functions.initializeAccounts(account_addresses).transact()

    def pay_from_bank(self, player, amount):
        if not self.w3.eth.getBalance(self.w3.eth.accounts[0]) < amount:
            self.monopolyCoin.functions.sendCoinFromBank(self.get_account(player), amount).transact()
            return True
        return False

    def pay_to_bank(self, player, amount):
        if not self.get_balance(player) < amount:
            player_account = self.get_account(player)
            self.monopolyCoin.functions.sendCoinToBank(player_account, amount).transact({
                'from': player_account
            })
            return True
        return False

    def transfer_coin(self, sender, receiver, amount):
        if not self.get_balance(sender) < amount:
            sender_account = self.get_account(sender)
            receiver_account = self.get_account(receiver)
            self.monopolyCoin.functions.transferCoin(sender_account, receiver_account, amount).transact({
                'from': sender_account
            })
            return True
        return False

    def get_balance(self, player):
        player_account = self.get_account(player)
        return self.monopolyCoin.functions.getBalance(player_account).call()

    # ------- Property Management Functions -------
    def initialize_properties(self, properties_indices):
        self.propertyManagement.functions.initializeProperties(properties_indices).transact()

    def get_property_owner(self, index):
        return self.propertyManagement.functions.getPropertyOwner(index).call()

    def get_all_properties(self, player):
        player_address = self.get_account(player)
        return self.propertyManagement.functions.getAllProperties(player_address).call()

    def get_houses(self, index):
        return self.propertyManagement.functions.getPropertyHouses(index).call()

    def get_hotel(self, index):
        return self.propertyManagement.functions.getPropertyHotel(index).call()

    def get_mortgage(self, index):
        return self.propertyManagement.functions.getPropertyMortgage(index).call()

    # NOTE: s_address corresponds to the seller address
    def change_ownership(self, s_address, buyer, index, price):
        b_address = self.get_account(buyer)
        return self.propertyManagement.functions.changeOwnership(s_address, b_address, index, price).transact({
            'from': b_address
        })

    def buy_houses(self, player, index, amount, price):
        player_address = self.get_account(player)
        if self.get_balance(player) > price and self.get_houses(index) + amount < 4 and self.get_hotel(index) == 0:
            return self.propertyManagement.function.buyHouses(player_address, index, amount, price).transact({
                'from': player_address
            })
        else:
            return False

    def buy_hotel(self, player, index, price):
        player_address = self.get_account(player)
        if self.get_balance(player) > price and self.get_houses(index) == 4 and self.get_hotel(index) == 0:
            return self.propertyManagement.function.buyHotel(player_address, index, price).transact({
                'from': player_address
            })
        else:
            return False

    def un_mortgage(self, player, index, price):
        player_address = self.get_account(player)
        if self.get_balance(player) > price and self.get_mortgage(index):
            return self.propertyManagement.function.unMortgage(player_address, index, price).transact({
                'from': player_address
            })
        else:
            return False

    def sell_houses(self, player, index, amount, price):
        player_address = self.get_account(player)
        if self.get_balance(self.w3.eth.accounts[0]) > price and self.get_houses(index) + amount <= 0 and self.get_hotel(index) == 0:
            return self.propertyManagement.function.sellHouses(player_address, index, amount, price).transact({
                'from': player_address
            })
        else:
            return False

    def sell_hotel(self, player, index, price):
        player_address = self.get_account(player)
        if self.get_balance(self.w3.eth.accounts[0]) > price and self.get_hotel(index) == 1:
            return self.propertyManagement.function.sellHotel(player_address, index, price).transact({
                'from': player_address
            })
        else:
            return False

    def mortgage(self, player, index, price):
        player_address = self.get_account(player)
        if self.get_balance(self.w3.eth.accounts[0]) > price and self.get_houses(index) \
                and self.get_hotel(index) == 0 and not self.get_mortgage(index):
            return self.propertyManagement.function.mortgage(player_address, index, price).transact({
                'from': player_address
            })
        else:
            return False


if __name__ == '__main__':
    # Create some test objects
    from player import Player, Bank
    from board import Board
    bank = Bank()
    player_1 = Player('Ryan', 1)
    player_2 = Player('Jason', 2)
    board = Board()

    blockchain = BlockChain()
    blockchain.initialize_accounts([player_1, player_2])
    blockchain.transfer_coin(player_1, player_2, 150)
    blockchain.initialize_properties(board.get_all_properties())
    print(blockchain.get_property_owner(39))
