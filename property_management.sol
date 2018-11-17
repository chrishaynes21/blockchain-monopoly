pragma solidity ^0.4.25;
import './monopoly_coin.sol';

contract PropertyManagement {
    // A struct to hold all data related to a property
    struct Property {
        uint8 numHouses;
        uint8 hotel;
        bool mortgaged;
    }


    // Holds the banker's address for fast access
    address banker;

    // Points to the MonopolyCoin contract to process transactions
    MonopolyCoin m;

    // Events that can occur in the contract
    event PurchaseProperty(address seller, address buyer, uint8 index);
    event PurchaseHouses(address owner, uint8 amount, uint8 index);
    event SellHouses(address owner, uint8 amount, uint8 index);
    event PurchaseHotel(address owner, uint8 index);
    event SellHotel(address owner, uint8 index);
    event Mortgage(address owner, uint8 index);
    event UnMortgage(address owner, uint8 index);

    // Map all indices to the property and owners to property indices. Storing
    // the address with the property index for accessing the array for O(1) lookup
    mapping(uint8 => Property) properties;
    address[40] owners;

    // Sets the banker's address
    constructor(address coin_contract) public {
        banker = msg.sender;
        m = MonopolyCoin(coin_contract);
    }

    // Takes a list of properties that can be owned
    function initializeProperties(uint8[] indices) public {
        for (uint8 i = 0; i < indices.length; i++) {
            properties[indices[i]] = Property(0, 0,false);
            owners[indices[i]] = banker;
        }
    }

    // Function to see who owns a Property
    function getPropertyOwner(uint8 index) public view returns (address owner) {
        return owners[index];
    }

    // Helper function for getAllProperties
    function countAllProperties(address owner) internal view returns (uint8 propertyCount) {
        propertyCount = 0;
        for (uint8 i = 0; i < 40; i++) {
            if (getPropertyOwner(i) == owner) {
                propertyCount++;
            }
        }
        return propertyCount;
    }

    // A function to get all properties an owner has. 0 Gas required, but slightly
    // expensive computationally
    function getAllProperties(address owner) public view returns (uint8[] ownerProperties) {
        uint8[] memory ownedProperties = new uint8[](countAllProperties(owner));
        uint8 counter = 0;
        for (uint8 i = 0; i < 40; i++) {
            if (getPropertyOwner(i) == owner) {
                ownedProperties[counter] = i;
                counter++;
            }
        }
        return ownedProperties;
    }

    // Function to get the number of houses on a property
    function getPropertyHouses(uint8 index) public view returns (uint8 houses) {
        return properties[index].numHouses;
    }

    // Function to get the number of numHotels on a property
    function getPropertyHotel(uint8 index) public view returns (uint8 hotels) {
        return properties[index].hotel;
    }

    // Function to get if a property is mortgaged
    function getPropertyMortgage(uint8 index) public view returns (bool mortgaged) {
        return properties[index].mortgaged;
    }

    // Transfer ownership of a Property and funds to buy it
    function changeOwnership(address seller, address buyer, uint8 index, uint256 price)
    public returns (bool success) {
        if (getPropertyOwner(index) == buyer) {
            return false;
        }
        if (m.transferCoin(buyer, seller, price)) {
            owners[index] = buyer;
            emit PurchaseProperty(seller, buyer, index);
            return true;
        } else {
            return false;
        }
    }

    // Function to buy houses for a property
    function buyHouses(address owner, uint8 index, uint8 amount ,uint256 price) public returns (bool success) {
        if (getPropertyOwner(index) != owner) {
            return false;
        }
        if (m.transferCoin(owner, banker, price)) {
            properties[index].numHouses += amount;
            emit PurchaseHouses(owner, amount, index);
            return true;
        } else {
            return false;
        }
    }

    // Function to buy a hotel for a property
    function buyHotel(address owner, uint8 index, uint256 price) public returns (bool success) {
        if (getPropertyOwner(index) != owner) {
            return false;
        }

        if (m.transferCoin(owner, banker, price)) {
            properties[index].numHouses = 0;
            properties[index].hotel++;
            emit PurchaseHotel(owner, index);
            return true;
        } else {
            return true;
        }
    }

    // Function to un-mortgage a property
    function unMortgage(address owner, uint8 index, uint256 price) public returns (bool success) {
        if (getPropertyOwner(index) != owner) {
            return false;
        }
        if (m.transferCoin(owner, banker, price)) {
            properties[index].mortgaged = false;
            emit UnMortgage(owner, index);
            return true;
        } else {
            return false;
        }
    }

    // Function to sell houses for a property
    function sellHouses(address owner, uint8 index, uint8 amount ,uint256 price) public returns (bool success) {
        if (getPropertyOwner(index) != owner) {
            return false;
        }
        if (m.transferCoin(banker, owner, price)) {
            properties[index].numHouses -= amount;
            emit SellHouses(owner, amount, index);
            return true;
        } else {
            return false;
        }
    }

    // Function to sell a hotel for a property
    function sellHotel(address owner, uint8 index, uint256 price) public returns (bool success) {
        if (getPropertyOwner(index) != owner) {
            return false;
        }
        if (m.transferCoin(banker, owner, price)) {
            properties[index].numHouses = 4;
            properties[index].hotel = 0;
            emit SellHotel(owner, index);
            return true;
        } else {
            return false;
        }
    }

    // Function to mortgage a property
    function mortgage(address owner, uint8 index, uint256 price) public returns (bool success) {
        if (getPropertyOwner(index) != owner) {
            return false;
        }
        if (m.transferCoin(banker, owner, price)) {
            properties[index].mortgaged = true;
            emit Mortgage(owner, index);
            return true;
        } else {
            return false;
        }
    }
}