# Blockchain Monopoly
A Python application that leverages blockchain transaction technology to manage currencies and properties. It does this by using Solidity smart contracts and the Ethereum blockchain.

## Required Technologies
- Python 3.6.5
- Web3.py 4.7.2 
- PySolc 3.2.0
- Ganache GUI 1.2.2 
  - One can use the Ganache CLI if the port is updated in blockchain.py

## Running the application
1. Start the Ganache GUI
    - In the settings page add the number of accounts you would like. Since Monopoly has 2-8 players, 9 is the best number because that's an account for 8 players and the banker. This only needs to be done once.
2. Run game_engine.py using the command `python game_engine.py`.
3. Enjoy!

*Front end coming soon!*
