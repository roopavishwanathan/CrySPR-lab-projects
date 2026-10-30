// SPDX-License-Identifier: MIT

// Author: Emrah

pragma solidity ^0.8.0;

interface IAuction {
    struct Auctioneer {
        uint256 paymentOffered;
        uint256 auctionNonce;
        bool isValid;
        address winner;
        uint256 auctionStartTime;
        uint256 auctionEndTime;
    }

    function updateNonce(address _auctionAddress, uint256 _auctionNonce)
        external;

    function declareWinner(address _auctionAdress, address _winner) external;
}

contract Auction is IAuction {
    // Will be used when there is a conflict!
    address public constant CLOUD_ADDRESS =
        0x6A1C312D91408Bd62680926E6853C8E2315bC04d;

    // Manager address
    address public constant MANAGER_ADDRESS =
        0x17F6AD8Ef982297579C203069C1DbfFE4348c372;

    bytes32 public pk;

    modifier onlyManager() {
        require(msg.sender == MANAGER_ADDRESS, "You are not manager!");
        _;
    }

    function update_pk(bytes32 _pk) public onlyManager {
        pk = _pk;
    }

    // Store Auction Information
    mapping(address => Auctioneer) public auctions;

    // Create a new auction
    function auctioneerRegister(
        uint256 _auctionStartTime,
        uint256 _auctionEndTime
    ) external payable {
        require(msg.value > 0, "You did not specify the payment!");
        auctions[msg.sender] = Auctioneer(
            msg.value,
            0,
            true,
            address(0),
            _auctionStartTime,
            _auctionEndTime
        );
    }

    // AddNonceToAuction
    function updateNonce(address _auctionAddress, uint256 _auctionNonce)
        external
        override
    {
        auctions[_auctionAddress].auctionNonce += _auctionNonce;
    }

    function declareWinner(address _auctionAddress, address _winner)
        external
        override
    {
        require(
            auctions[_auctionAddress].isValid == true,
            "Address is not valid!"
        );
        auctions[_auctionAddress].winner = _winner;
    }
}

contract Bidders {
    Auction auction;

    constructor(address _addr) {
        auction = Auction(_addr);
    }

    // Bidder Information
    struct Bidder {
        bytes32 encryptedBid;
        uint256 deposit;
        bool validUser;
        bool registered;
        bool providedNonce;
        address auctionOwnerAddress;
    }

    // Bids
    mapping(address => Bidder) public bids;

    // Used Modifiers
    modifier requireDeposit() {
        require(msg.value == 10000000 gwei, "Deposit amount is not matching!");
        _;
    }

    modifier validAuction(address _auctionAdress) {
        (, , bool test, , , ) = auction.auctions(_auctionAdress);
        require(
            _auctionAdress != address(0) && test == true,
            "Not Valid Auction!"
        );
        _;
    }

    modifier auctionTime(address _auctionAdress) {
        (, , , , , uint256 _auctionEndTime) = auction.auctions(_auctionAdress);
        require(_auctionEndTime - block.timestamp > 0, "Auction is Over!");
        _;
    }

    modifier auctionEndTime(address _auctionAdress) {
        (, , , , , uint256 _auctionEndTime) = auction.auctions(_auctionAdress);
        require(_auctionEndTime - block.timestamp < 0, "Auction is not over!");
        _;
    }

    // Deposit collateral to prevent malicious act.
    // Entry point to auction.
    // 1 GWEI == 0.01 Ether.
    // 10000000 GWEI
    // 0x6162636400000000000000000000000000000000000000000000000000000000
    function sendBid(address _auctionAdress, bytes32 _encryptedBid)
        external
        payable
        validAuction(_auctionAdress)
        requireDeposit
    {
        require(bids[msg.sender].validUser == true, "You aren't registered!");
        require(bids[msg.sender].providedNonce == true, "First provide nonce!");
        bids[msg.sender].encryptedBid = _encryptedBid;
    }

    function registerBidder(address _auctionAddress)
        external
        payable
        validAuction(_auctionAddress)
        requireDeposit
    {
        bytes32 bid;
        bids[msg.sender] = Bidder(
            bid,
            msg.value,
            true,
            true,
            false,
            _auctionAddress
        );
    }

    // Todo: Add access control (only manager).
    function declareWinner(address _auctionAdress, address _winner) external {
        auction.declareWinner(_auctionAdress, _winner);
    }

    // No need for this!
    function computeNonce(address _auctionAdress, uint256 _nonceVal) public {
        //auctionTime(_auctionAdress) {
        (, , bool isValid, , , ) = auction.auctions(_auctionAdress);
        require(
            isValid == true &&
                bids[msg.sender].validUser == true &&
                bids[msg.sender].providedNonce == false,
            "You are not valid or you have done already!"
        );
        auction.updateNonce(_auctionAdress, _nonceVal);
    }

    function hash(address _auctionAdress)
        external
        view
        auctionEndTime(_auctionAdress)
        returns (bytes32)
    {
        (, uint256 auctionNonce, , , , ) = auction.auctions(_auctionAdress);
        return keccak256(abi.encode(auctionNonce));
    }

    function refundDeposit(address _auctionAdress)
        external
        payable
        auctionTime(_auctionAdress)
    {
        // Check if auction is over
        (, , , address isWinner, , ) = auction.auctions(_auctionAdress);
        require(
            msg.sender != isWinner,
            "You are winner, you can't take back the deposit"
        );
        require(
            bids[msg.sender].deposit > 0,
            "You withdrawed your deposit already"
        );
        //Send the deposited bid amount
        bids[msg.sender].deposit = 0;
        payable(msg.sender).transfer(bids[msg.sender].deposit);
    }
}
