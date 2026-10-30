from brownie import Auction, Bidders, accounts, config, interface
import time
from web3 import Web3

from subprocess import run
import subprocess


def main():
    deploy_and_interact()


def deploy_and_interact():

    account = accounts.add(config["wallets"]["from_key"])

    # Deploy Auction Contract
    auction_contract = Auction.deploy({"from": account})

    # Deploy Bidder contract
    bidders_contract = Bidders.deploy(auction_contract.address, {"from": account})

    now = int(time.time())

    # Create auction with start/end times and payment
    tx = auction_contract.auctioneerRegister(
        now, now + 1231231231231231231231231231231231231, {"from": account, "value": Web3.toWei(0.0001, "ether")}
    )
    tx.wait(1)

    auction_address = account


    print("The auction identifier is: ", auction_address)
    print("The auction contract address is: ", auction_contract)
    print("The bidder contract address is: ", bidders_contract)

