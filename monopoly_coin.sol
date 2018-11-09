pragma solidity ^0.4.25;

contract MonopolyCoin {
    string public name = 'MonopolyCoin';
    string public symbol = 'mc';
    address banker;

    //a key-value pair to store addresses and their account balances
    mapping (address => uint) balances;

    // declaration of an event. Event will not do anything but add a record to the log
    event Transfer(address from, address to, uint256 value);

    constructor() public {
        //set the balances of creator account to be 15400
        balances[msg.sender] = 15400;
        banker = msg.sender;
    }

    function initializeAccounts(address[] addresses) public returns (bool sufficient) {
        // ensure no more than 8 players
        assert(addresses.length < 9);
        for (uint i = 0; i < addresses.length; i++) {
            // initialize the account with 1500 MonopolyCoin
            if (!sendCoinFromBank(addresses[i], 1500)) {
                return false;
            }
        }
        return true;
    }

    function sendCoinFromBank(address receiver, uint amount) public returns(bool sufficient) {
        return transferCoin(banker, receiver, amount);
    }

    function sendCoinToBank(address sender, uint amount) public returns(bool sufficient) {
        return transferCoin(sender, banker, amount);
    }

    function transferCoin(address sender, address receiver, uint amount) public returns(bool sufficient) {
        // validate transfer
        if (balances[sender] < amount) return false;

        // complete coin transfer and call event to record the log
        balances[sender] -= amount;
        balances[receiver] += amount;
        emit Transfer(sender, receiver, amount);

        return true;
    }

    function getBalance(address addr) public view returns(uint) {
        return balances[addr];
    }
}