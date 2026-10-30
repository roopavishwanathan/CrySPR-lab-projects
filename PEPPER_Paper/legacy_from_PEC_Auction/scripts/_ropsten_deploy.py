from brownie import Auction, Bidders, accounts, config, interface
import time
from web3 import Web3

from subprocess import run
import subprocess


def main():
    deploy_and_interact()
    # nonce = getNonce()
    # initEnclave(nonce)


def initEnclave(nonce):

    go_command = "./client -nonce "
    go_command += str(nonce)

    go_command += " -s `ego signerid public.pem`"

    go_command_client = " & ego run server -nonce "
    go_command_client += str(nonce)

    go_command += go_command_client

    result = subprocess.run(
        go_command, text=True, encoding="ISO-8859-1", capture_output=True, shell=True
    )

    print(result)


def getNonce():
    # Get the current nonce

    auction_contract = "0x8cc68aa0F3259A18884F796180a802CC3677e52C"
    bidder_contract = "0xBA45706F4a1a1dCcc8D3744AEb6E5f6EbC6b5ea8"
    auction_identifier = "0x6A1C312D91408Bd62680926E6853C8E2315bC04d"
    nonce = interface.IAuction(auction_contract).returnAuctionDetails(
        auction_identifier
    )
    print(
        "the current nonce is: ",
        nonce,
    )
    return nonce


def deploy_and_interact():

    account = accounts.add(config["wallets"]["from_key"])

    auction_contract = Auction.deploy({"from": account})

    # Deploy Bidders contract
    bidders_contract = Bidders.deploy(auction_contract.address, {"from": account})

    now = int(time.time())

    # Create auction with start/end times and payment
    tx = auction_contract.auctioneerRegister(
        now, now + 240000, {"from": account, "value": Web3.toWei(0.0001, "ether")}
    )
    tx.wait(1)

    auction_address = account

    # # wait 120 seconds.
    # time.sleep(120)

    # Call enclave with nonce so that it can generate remote report!

    print("The auction identifier is: ", auction_address)
    print("The auction contract address is: ", auction_contract)
    print("The bidder contract address is: ", bidders_contract)

    # Get all encrypt bids and feed to enclave.

    # Get the  winner
