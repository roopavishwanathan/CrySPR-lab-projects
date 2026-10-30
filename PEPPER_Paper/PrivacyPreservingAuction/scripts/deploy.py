from brownie import Auction, Bidders, accounts
import time
from web3 import Web3
import random
from subprocess import run
import subprocess

from shlex import split

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
    manager = accounts[14]

    print("The auction created at address: ", auction_contract.address)
    print("Current auction balance is: ", auction_contract.balance())

    # Deploy Bidders contract
    bidders_contract = Bidders.deploy(auction_contract.address, {"from": accounts[0]})

    # Check current nonce
    print(
        "The curent nonce is: ", auction_contract.auctions(auction_contract.address)[1]
    )

    # Register 10 bidders
    for i in range(1, 11):
        tx = bidders_contract.registerBidder(
            auction_address, {"from": accounts[i], "value": Web3.toWei(0.01, "ether")}
        )
        tx.wait(1)

    # Create 10 nonce varibles for aggregated nonce!
    total_nonce = 0
    for i in range(1, 11):
        random_num = random.randint(1, 100)
        tx = bidders_contract.computeNonce(
            auction_address, random_num, {"from": accounts[i]}
        )
        tx.wait(1)
        total_nonce += random_num

    print(
        "The aggregated nonce on contract is: ",
        auction_contract.auctions(auction_address)[1],
    )

    print("Total nonce our python script computed is: ", total_nonce)


    #go_command = "ego run server -nonce "
    #go_command += str(total_nonce)

    #go_command_client = " & ./client -nonce "
    #go_command_client += str(total_nonce)

    #go_command_client += " -s `ego signerid public.pem`"
    
    #go_command += go_command_client

    #print(go_command)
    go_command2 = "./client -nonce "
    go_command2 += str(total_nonce)

    go_command2 += " -s `ego signerid public.pem`"

    go_command_client = " & ego run server -nonce "
    go_command_client += str(total_nonce)

    go_command2 += go_command_client

    result = subprocess.run(
        go_command2, text=True,encoding="ISO-8859-1", capture_output=True, shell=True).stdout

    
    print(result)

    result = result.split("\n")
     
    winner_address = accounts[int(result[-4].split("t")[1])]

    print("The winner address is: ", winner_address)

    print("Updating the auction contract...")

    tx = auction_contract.declareWinner(
        auction_address, winner_address, {"from": manager}
    )

    tx.wait(1)
     
    #subprocess.run(go_command)
    #subprocess.run(go_command_client)
    # bytes

