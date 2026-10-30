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

    function returnAuctionDetails(address index)
        external
        view
        returns (uint256);
}

