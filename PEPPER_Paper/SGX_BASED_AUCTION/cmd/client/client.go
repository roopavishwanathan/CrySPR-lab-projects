package main

import (
	"bytes"
	"context"
	"crypto"
	"crypto/ecdsa"
	"crypto/sha256"
	"crypto/tls"
	"crypto/x509"
	"encoding/hex"
	"fmt"
	"io/ioutil"
	"math/big"
	rnd "math/rand"
	"net/http"
	"os"
	"strconv"
	"time"

	"crypto/rand"

	ecies "github.com/ecies/go/v2"
	"github.com/edgelesssys/ego/eclient"
	"github.com/emrahsariboz/PEC/pkg/solidity_wrapper"
	"github.com/ethereum/go-ethereum/accounts/abi/bind"
	"github.com/ethereum/go-ethereum/common"
	ethcrypto "github.com/ethereum/go-ethereum/crypto"
)

func randint64() (int64, error) {
	val, err := rand.Int(rand.Reader, big.NewInt(int64(1000000)))
	if err != nil {
		return 0, err
	}
	return val.Int64(), nil
}

func privateKeyToOthers(hexkey string) (*ecdsa.PrivateKey, crypto.PublicKey, *ecdsa.PublicKey) {

	privateKey, err := ethcrypto.HexToECDSA(hexkey)

	if err != nil {
		panic(err)
	}
	publicKey := privateKey.Public()
	publicKeyECDSA, _ := publicKey.(*ecdsa.PublicKey)
	return privateKey, publicKey, publicKeyECDSA
}

func checkIfError(e error) {
	if e != nil {
		panic(e)
	}
}

func httpGet(url string) []byte {

	tlsConfig := &tls.Config{InsecureSkipVerify: true}
	client := http.Client{Transport: &http.Transport{TLSClientConfig: tlsConfig}}
	resp, err := client.Get(url)
	if err != nil {
		panic(err)
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		panic(resp.Status)
	}
	body, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		panic(err)
	}
	return body
}

func httpGetPK(tlsConfig *tls.Config, url string) *ecies.PublicKey {
	fmt.Println("Getting enclave pk...")
	client := http.Client{Transport: &http.Transport{TLSClientConfig: tlsConfig}}

	resp, err := client.Get(url)

	if err != nil {
		panic(err)
	}

	defer resp.Body.Close()

	body, err := ioutil.ReadAll(resp.Body)
	checkIfError(err)

	pk, err := ecies.NewPublicKeyFromBytes(body)
	checkIfError(err)

	return pk
}

func main() {

	// Create connection
	client := solidity_wrapper.CreateConnection()

	// Hardcoded for now. Will be retrieved using HTTPS POST.
	// Auction contract = 0x8cc68aa0F3259A18884F796180a802CC3677e52C
	// Biddders contract  = 0xBA45706F4a1a1dCcc8D3744AEb6E5f6EbC6b5ea8

	// Initialize Contracts
	auction_contract, err := solidity_wrapper.NewAuction(common.HexToAddress("0xb086B0cce9b815d68A8e56e53E3335f096a8cB6F"), client)
	checkIfError(err)

	// Initialize Contracts
	bidders_contract, _ := solidity_wrapper.NewBidders(common.HexToAddress("0x367D856831879E64b5450366AfAd03eb3a875A65"), client)
	auction_identifier := common.HexToAddress("0x6A1C312D91408Bd62680926E6853C8E2315bC04d")

	// Read private key of bidder.
	// dont forget to export private_key!
	val, ok := os.LookupEnv("PRIVATE_KEY")

	if !ok {
		fmt.Println("Cant read private key. Export PRIVATE_KEY.")
	}

	privateKey, _, ethereum_address := privateKeyToOthers(val)
	fromAddress := ethcrypto.PubkeyToAddress(*ethereum_address)

	nonce, _ := client.PendingNonceAt(context.Background(), fromAddress)
	//gasPrice, err := client.SuggestGasPrice(context.Background())
	checkIfError(err)

	chainID, err := client.NetworkID(context.Background())
	checkIfError(err)

	auth, err := bind.NewKeyedTransactorWithChainID(privateKey, chainID)
	checkIfError(err)

	auth.Nonce = big.NewInt(int64(nonce))
	auth.Value = big.NewInt(0)
	auth.GasLimit = uint64(900000)
	auth.GasPrice = big.NewInt(8000000007)

	tx, err := auction_contract.ResetAuction(auth, auction_identifier)
	checkIfError(err)
	fmt.Printf("Clear out previous bids: %s\n", tx.Hash().Hex())
	fmt.Println("Waiting the reset TX to get mined.....")
	time.Sleep(20 * time.Second)

	nonce, _ = client.PendingNonceAt(context.Background(), fromAddress)
	//gasPrice, err := client.SuggestGasPrice(context.Background())
	checkIfError(err)
	auth.Nonce = big.NewInt(int64(nonce))
	auth.Value = big.NewInt(10000000000000000) // in wei
	auth.GasLimit = uint64(300000)
	auth.GasPrice = big.NewInt(8000000007)

	tx, err = bidders_contract.RegisterBidder(auth, auction_identifier)
	checkIfError(err)

	fmt.Printf("Register tx sent: %s\n", tx.Hash().Hex())
	fmt.Println("Waiting the Register TX to get mined.....")
	time.Sleep(20 * time.Second)

	// Reset Auction First for testing!
	nonce, _ = client.PendingNonceAt(context.Background(), fromAddress)
	checkIfError(err)

	auth.Nonce = big.NewInt(int64(nonce))
	auth.Value = big.NewInt(0)
	auth.GasLimit = uint64(900000)
	auth.GasPrice = big.NewInt(8000000007)

	n, err := randint64()
	fmt.Println("Generating random nonce. My random nonce is: ", n)
	tx2, err := bidders_contract.ComputeNonce(auth, auction_identifier, big.NewInt(n))
	checkIfError(err)
	fmt.Printf("Participating in nonce computation...: %s\n", tx2.Hash().Hex())
	fmt.Println("Waiting the nonce transaction to get mined.....")
	time.Sleep(20 * time.Second)

	auction_nonce, err := auction_contract.Auctions(&bind.CallOpts{}, auction_identifier)
	checkIfError(err)
	fmt.Println("The current auction nonce is: ", auction_nonce.AuctionNonce)

	// Trigger manager to start start enclave.
	byte_nonce := []byte(new(big.Int).SetInt64(auction_nonce.AuctionNonce.Int64()).String())

	server_url := "https://20.234.100.177:8045/"

	fmt.Println("Sent request to Manager to init enclave!")

	go httpGet(server_url + "initEnclave")

	fmt.Println("Waiting for the enclave!")
	time.Sleep(10 * time.Second)

	tlsConfig := &tls.Config{InsecureSkipVerify: true}

	enclave_url := "https://20.234.100.177:4000"
	certBytes := httpGet(enclave_url + "/cert")
	reportBytes := httpGet(enclave_url + "/report")

	// Retrive Public Key of Enclave!
	pk := httpGetPK(tlsConfig, enclave_url+"/pk")

	cert, _ := x509.ParseCertificate(certBytes)
	tlsConfig = &tls.Config{RootCAs: x509.NewCertPool(), ServerName: "localhost"}
	tlsConfig.RootCAs.AddCert(cert)

	// Verify Report
	fmt.Println("Verifying the report...")
	report, err := eclient.VerifyRemoteReport(reportBytes)
	if err != nil {
		panic(err)
	}
	fmt.Println("report is verified...")

	// nonce --> Expected nonce
	hash := sha256.Sum256(append(certBytes, byte_nonce...))

	fmt.Println("Verifying the encalve identiy...")
	// if !bytes.Equal(report.SignerID, signer) {
	// 	fmt.Println("Identy doesnt' match!")
	// }
	fmt.Println("The identy matched...")

	fmt.Println("Checking if hash in report matches")
	if !bytes.Equal(report.Data[:len(hash)], hash[:]) {
		fmt.Print("report data does not match the certificate's hash")
	} else {
		fmt.Println("The report data match the certificate's hash")
		fmt.Println("Remote Attestation is Successfull!!!")
	}

	min := 10000000000000
	max := 10000000000000000

	rnd.Seed(time.Now().UnixNano())
	bid := rnd.Intn(max-min) + min

	encryptedBid, _ := ecies.Encrypt(pk, []byte(strconv.Itoa(bid)))

	encodedString := hex.EncodeToString(encryptedBid)

	fmt.Println("ENRYPTED + ENCODED BID", encodedString)

	nonce, _ = client.PendingNonceAt(context.Background(), fromAddress)
	checkIfError(err)

	auth.Nonce = big.NewInt(int64(nonce))
	auth.GasPrice = big.NewInt(8000000007)
	// Send ecrypted bid to smart contract.
	tx3, err := bidders_contract.SendBid(auth, auction_identifier, encodedString)
	fmt.Println("RANDOM BID IN PLAINTEXT IS: ", bid)
	fmt.Printf("Sending encrypted bid...: %s\n", tx3.Hash().Hex())

	checkIfError(err)
	time.Sleep(20 * time.Second)
	// try dectypting it here...
	var bids2 []string
	bids2, err = auction_contract.ReturnEncryptedBids(&bind.CallOpts{}, auction_identifier)
	checkIfError(err)

	fmt.Println(bids2)

	// decodedString, err := hex.DecodeString(bids2[len(bids2)-1])
	// checkIfError(err)

	// _ = decodedString

	// decrypted_bid, err := ecies.Decrypt(pk, decodedString)
	// checkIfError(err)

	// bid_int, err := strconv.Atoi(string(decrypted_bid))
	// checkIfError(err)
	// fmt.Println("DECRYPTED + DECODED BID IS ", bid_int)

	fmt.Println("Asking manager to find winner")

	httpGet("https://20.234.100.177:8045" + "/findWinner")

}
