from brownie import Auction, Bidders, accounts
import time
from web3 import Web3
import random
import os

import subprocess
from subprocess import run
from shlex import split
import subprocess


def main():
    deploy_and_interact()


def deploy_and_interact():

    # Deploy Auction Contract
    auction_contract = Auction.deploy({"from": accounts[0]})
    now = int(time.time())

    # Create auction with start/end times and payment
    tx = auction_contract.auctioneerRegister(
        now, now + 60, {"from": accounts[0], "value": Web3.toWei(1, "ether")}
    )
    tx.wait(1)

    auction_address = accounts[0]
    manager = accounts[1]

    print("The auction created at address: ", auction_contract.address)
    print("Current auction balance is: ", auction_contract.balance())

    # Deploy Bidders contract
    bidders_contract = Bidders.deploy(auction_contract.address, {"from": accounts[0]})

    # Check current nonce
    print(
        "The curent nonce is: ", auction_contract.auctions(auction_contract.address)[1]
    )

    tx = bidders_contract.registerBidder(
        auction_address, {"from": accounts[4], "value": Web3.toWei(0.01, "ether")}
    )
    tx.wait(1)

    tx = bidders_contract.registerBidder(
        auction_address, {"from": accounts[2], "value": Web3.toWei(0.01, "ether")}
    )
    tx.wait(1)

    random_num = random.randint(1, 100)
    tx = bidders_contract.computeNonce(
        auction_address, random_num, {"from": accounts[4]}
    )
    tx.wait(1)

    tx = bidders_contract.computeNonce(
        auction_address, random_num + 5, {"from": accounts[2]}
    )
    tx.wait(1)

    # print(
    #     "The aggregated nonce on contract is: ",
    #     auction_contract.auctions(auction_address)[1],
    # )

    # print("Total nonce our python script computed is: ", total_nonce)

    """
    TEST NEW BID
    """

    tx = bidders_contract.sendBid(
        auction_address,
        "test",
        {"from": accounts[4], "value": Web3.toWei(0.01, "ether")},
    )
    tx.wait(1)

    tx = bidders_contract.sendBid(
        auction_address,
        "test2",
        {"from": accounts[2], "value": Web3.toWei(0.01, "ether")},
    )
    tx.wait(1)

    print(
        "The encrypted bids of auction ",
        accounts[0],
        " is ",
        auction_contract.returnEncryptedBids.call(auction_address),
    )

    print("Updating the bids")

    tx = auction_contract.resetAuction(auction_address, {"from": accounts[0]})
    tx.wait(1)

    print(
        "The encrypted bids of auction ",
        accounts[0],
        " is ",
        auction_contract.returnEncryptedBids.call(auction_address),
    )

