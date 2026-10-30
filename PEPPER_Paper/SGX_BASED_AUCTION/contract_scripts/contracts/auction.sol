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
        string[] encryptedBidArray;
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
        0xa8d9645E2927fD08a776A120DBc9096B9Fa8Eeb5;

    address public constant ADMIN = 0x6A1C312D91408Bd62680926E6853C8E2315bC04d;

    bytes32 public pk;

    // Store Auction Information
    mapping(address => Auctioneer) public auctions;
    string[] encryptedBids;
    address[] bidders;

    modifier onlyManager() {
        require(msg.sender == MANAGER_ADDRESS, "You are not manager!");
        _;
    }

    modifier onlyAdmin() {
        require(msg.sender == ADMIN, "You are not manager!");
        _;
    }

    function update_pk(bytes32 _pk) external onlyManager {
        pk = _pk;
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
    //onlyManager
    {
        require(
            auctions[_auctionAddress].isValid == true,
            "Address is not valid!"
        );
        auctions[_auctionAddress].winner = _winner;
    }

    function newBid(address _auctionAddress, string memory _newBid) external {
        auctions[_auctionAddress].encryptedBidArray.push(_newBid);
        bidders.push(msg.sender);
    }

    function returnAuctionDetails(address index)
        external
        view
        returns (uint256)
    {
        return auctions[index].auctionNonce;
    }

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
            _auctionEndTime,
            encryptedBids
        );
    }

    function returnEncryptedBids(address _auctionAddress)
        external
        view
        returns (string[] memory array)
    {
        return auctions[_auctionAddress].encryptedBidArray;
    }

    function returnBidders() external view returns (address[] memory array) {
        return bidders;
    }

    // For testing only, will be removed in the future.
    function resetAuction(address _auctionAddress) external onlyAdmin {
        string[] memory emptyArray;
        address[] memory emptyAddresses;

        auctions[_auctionAddress].encryptedBidArray = emptyArray;
        bidders = emptyAddresses;
        auctions[_auctionAddress].auctionNonce = 0;
    }
}

contract Bidders {
    Auction auction;

    constructor(address _addr) {
        auction = Auction(_addr);
    }

    uint256 public totalBidder;

    // Bidder Information
    struct Bidder {
        string encryptedBid;
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

    modifier validAuction(address _auctionAddress) {
        (, , bool _isValid, , , ) = auction.auctions(_auctionAddress);

        require(
            _auctionAddress != address(0) && _isValid == true,
            "Not Valid Auction!"
        );
        _;
    }

    modifier auctionTime(address _auctionAddress) {
        (, , , , , uint256 _auctionEndTime) = auction.auctions(_auctionAddress);
        require(_auctionEndTime - block.timestamp > 0, "Auction is Over!");
        _;
    }

    modifier auctionEndTime(address _auctionAddress) {
        (, , , , , uint256 _auctionEndTime) = auction.auctions(_auctionAddress);
        require(_auctionEndTime - block.timestamp < 0, "Auction is not over!");
        _;
    }

    // Deposit collateral to prevent malicious act.
    // Entry point to auction.
    // 1 GWEI == 0.01 Ether.
    // 10000000 GWEI
    // 0x6162636400000000000000000000000000000000000000000000000000000000
    function sendBid(address _auctionAddress, string memory _encryptedBid)
        external
        payable
        validAuction(_auctionAddress)
    {
        require(bids[msg.sender].validUser == true, "You aren't registered!");
        require(bids[msg.sender].providedNonce == true, "First provide nonce!");
        bids[msg.sender].encryptedBid = _encryptedBid;
        auction.newBid(_auctionAddress, _encryptedBid);
    }

    function registerBidder(address _auctionAddress, uint256 _nonceVal)
        external
        payable
        validAuction(_auctionAddress)
        requireDeposit
    {
        string memory bid;
        bids[msg.sender] = Bidder(
            bid,
            msg.value,
            true,
            true,
            false,
            _auctionAddress
        );
        totalBidder += 1;

        // Participate in aggregated nonce.
        (, , bool isValid, , , ) = auction.auctions(_auctionAddress);
        require(
            isValid == true &&
                bids[msg.sender].validUser == true &&
                bids[msg.sender].providedNonce == false,
            "You are not valid or you have already!"
        );
        bids[msg.sender].providedNonce = true;
        auction.updateNonce(_auctionAddress, _nonceVal);
    }

    address private SGX_ENCLAVE = 0xAFdE38Bbd62946DcE61BE9c53c797d01d5Ce19F8;

    function signatureVerification(
        address _auctionAddress,
        address winner,
        uint256 id,
        bytes memory signature
    ) external {
        bytes32 messageHash = getMessageHash(winner, id);
        bytes32 ethSignedMessageHash = getEthSignedMessageHash(messageHash);

        require(
            recoverSigner(ethSignedMessageHash, signature) == SGX_ENCLAVE,
            "SGX signature doesn't match!"
        );

        declareWinner(_auctionAddress, winner);
    }

    function getMessageHash(address account, uint256 id)
        public
        pure
        returns (bytes32)
    {
        return keccak256(abi.encodePacked(account, id));
    }

    function getEthSignedMessageHash(bytes32 messageHash)
        public
        pure
        returns (bytes32)
    {
        return
            keccak256(
                abi.encodePacked(
                    "\x19Ethereum Signed Message:\n32",
                    messageHash
                )
            );
    }

    function recoverSigner(
        bytes32 _ethSignedMessageHash,
        bytes memory _signature
    ) public pure returns (address) {
        (bytes32 r, bytes32 s, uint8 v) = splitSignature(_signature);

        return ecrecover(_ethSignedMessageHash, v, r, s);
    }

    function splitSignature(bytes memory signature)
        public
        pure
        returns (
            bytes32 r,
            bytes32 s,
            uint8 v
        )
    {
        require(signature.length == 65, "invalid signature length");

        assembly {
            r := mload(add(signature, 32))
            s := mload(add(signature, 64))
            v := byte(0, mload(add(signature, 96)))
        }
    }

    function declareWinner(address _auctionAddress, address _winner) internal {
        auction.declareWinner(_auctionAddress, _winner);
    }

    function hash(address _auctionAddress)
        external
        view
        auctionEndTime(_auctionAddress)
        returns (bytes32)
    {
        (, uint256 auctionNonce, , , , ) = auction.auctions(_auctionAddress);
        return keccak256(abi.encode(auctionNonce));
    }

    function refundDeposit(address _auctionAddress)
        external
        payable
        auctionTime(_auctionAddress)
    {
        // Check if auction is over
        (, , , address isWinner, , ) = auction.auctions(_auctionAddress);
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
