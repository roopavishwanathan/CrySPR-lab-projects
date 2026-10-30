// SPDX-License-Identifier: MIT

// Author: Emrah
pragma solidity ^0.8.0;

interface IAuction {
    function returnAuctionDetails(address index)
        external
        view
        returns (uint256);
}
