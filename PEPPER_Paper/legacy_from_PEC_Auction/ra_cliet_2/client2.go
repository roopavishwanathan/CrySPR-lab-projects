package main

import (
	"bytes"
	"crypto/tls"
	"fmt"
	"math/rand"
	"net/http"
	"strconv"
	"time"

	"encoding/json"
	"io"

	ecies "github.com/ecies/go/v2"
)

func checkIfError(e error) {
	if e != nil {
		panic(e)
	}
}

func readResponseBody(r io.Reader) []byte {
	b, _ := io.ReadAll(r)
	return b
}

func retrievePk(url string, tlsConfig *tls.Config) *ecies.PublicKey {
	client := http.Client{Transport: &http.Transport{TLSClientConfig: tlsConfig}}

	resp, err := client.Get(url)

	checkIfError(err)

	body := readResponseBody(resp.Body)

	// Construct pk
	pk, err := ecies.NewPublicKeyFromBytes(body)

	checkIfError(err)

	return pk
}

func main() {
	tlsConfig := &tls.Config{InsecureSkipVerify: true}

	pk_url := "http://localhost:8080/pk"
	bid_dec_url := "http://localhost:8080/findWinner"

	// Retrive Public Key of Enclave!
	fmt.Println("Sent a request to retrieve enclave public key")
	pk := retrievePk(pk_url, tlsConfig)
	fmt.Println("Received the public key of enclave")

	// Generate 10 random bids
	var bids [10]int
	rand.Seed(time.Now().UnixNano())

	min := 10000000000000
	max := 10000000000000000

	// 10 dummy account
	accounts := [10]string{"account0", "account1", "account2", "account3", "account4", "account5", "account6", "account7", "account8", "account9"}

	// account to encrypted bid
	bids_map := map[string][]byte{}

	// Gen 10 dummy random bid, encrypt and store in mapping
	for i := 0; i < 10; i++ {
		bids[i] = rand.Intn(max-min) + min
		bids_map[accounts[i]], _ = ecies.Encrypt(pk, []byte(strconv.Itoa(bids[i])))
	}

	//fmt.Println(bids_map)

	// ciphertext, _ := ecies.Encrypt(pk, []byte("100000000000000000"))
	// ciphertext2, _ := ecies.Encrypt(pk, []byte("1000000000000"))
	// ciphertext3, _ := ecies.Encrypt(pk, []byte("30000000000000000"))
	// ciphertext4, _ := ecies.Encrypt(pk, []byte("50000000000000000"))
	// ciphertext5, _ := ecies.Encrypt(pk, []byte("3000000000000000"))
	// ciphertext6, _ := ecies.Encrypt(pk, []byte("100000000000000000"))

	//bs := map[string][]byte{"accountA": ciphertext, "accountB": ciphertext2, "accountC": ciphertext3, "accountD": ciphertext4, "accountE": ciphertext5, "accountF": ciphertext6}
	jsonValue, err := json.Marshal(bids_map)

	checkIfError(err)
	fmt.Println("Sent the encrypted bids...")
	resp, err := http.Post(bid_dec_url, "application/json", bytes.NewBuffer(jsonValue))

	checkIfError(err)
	// Write the winner bid!
	winner, _ := io.ReadAll(resp.Body)

	fmt.Println("The winner address is")
	fmt.Println(string(winner))

}
