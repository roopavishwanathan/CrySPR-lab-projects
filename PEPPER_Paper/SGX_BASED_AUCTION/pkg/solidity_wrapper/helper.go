package solidity_wrapper

import (
	"crypto"
	"crypto/ecdsa"

	"github.com/ethereum/go-ethereum/common"
	ethcrypto "github.com/ethereum/go-ethereum/crypto"
	"github.com/ethereum/go-ethereum/ethclient"
)

func CreateConnection() *ethclient.Client {

	url := "https://sepolia.infura.io/v3/27b563ecfb3c41f9b2288f3860d9c31a"
	client, err := ethclient.Dial(url)
	if err != nil {
		panic(err)
	}
	return client
}

func ReturnAuctionDetails() (common.Address, *Auction, *Bidder) {

	auction_identifier := common.HexToAddress("0x6A1C312D91408Bd62680926E6853C8E2315bC04d")

	// Initialize Contracts
	auction_contract, err := NewAuction(common.HexToAddress("0xE4e225ec70c023868f3EcBa167f004c8Bc61bC87"), CreateConnection())

	if err != nil {
		panic(err)
	}

	// Initialize Contracts
	bidders_contract, _ := NewBidder(common.HexToAddress("0x43bc293434dfF77f0E955EA46D1CC248E960F873"), CreateConnection())

	// Read private key of bidder.
	return auction_identifier, auction_contract, bidders_contract
}

func PrivateKeyToOthers(hexkey string) (*ecdsa.PrivateKey, crypto.PublicKey, *ecdsa.PublicKey) {

	privateKey, err := ethcrypto.HexToECDSA(hexkey)

	if err != nil {
		panic(err)
	}
	publicKey := privateKey.Public()
	publicKeyECDSA, _ := publicKey.(*ecdsa.PublicKey)
	return privateKey, publicKey, publicKeyECDSA
}
