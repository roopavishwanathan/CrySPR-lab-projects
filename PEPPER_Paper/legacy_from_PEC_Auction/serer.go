package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"io/ioutil"
	"log"
	"net/http"
	"reflect"
	"strconv"

	ecies "github.com/ecies/go/v2"
)

var k, _ = ecies.GenerateKey()

func main() {

	var nonce = flag.String("nonce", "12345", "Aggregated Nonce Variable")

	http.HandleFunc("/bids", func(w http.ResponseWriter, r *http.Request) {
	})

	http.HandleFunc("/pk", func(w http.ResponseWriter, r *http.Request) {
		log.Println("key pair has been generated")
		log.Println(k.PublicKey)
		var test []byte
		test = k.PublicKey.Bytes(false)

		w.Write(test)
	})

	http.HandleFunc("/findWinner", func(w http.ResponseWriter, r *http.Request) {
		var response map[string][]byte

		body, _ := ioutil.ReadAll(r.Body)

		err := json.Unmarshal(body, &response)

		if err != nil {
			panic(err)
		}

		// fmt.Println("The length of mapping is ", len(response))
		// bidsType := make([]string, len(response))
		// bids := make([]interface{}, len(bidsType))

		fmt.Println("Received the encrypted bids...")
		fmt.Println("Finding the minimum bid...")
		min := 100000000000000000

		var winner_bid string
		for z, l := range response {
			plaintext, _ := ecies.Decrypt(k, l)
			val, _ := strconv.Atoi(string(plaintext))

			if val < min {
				min = val
				winner_bid = z
			}
			fmt.Println("Key: ", z, " => ", "Decrypted: ", val)
		}

		fmt.Println("The minimum bid is: ", min)

		// bidsInterface := make([]interface{}, len(bids))

		// for i, s := range bids {

		// }

		w.Write([]byte(winner_bid))
		//fmt.Println("Received following: ", response[1])
		//plaintext, _ := ecies.Decrypt(k, response[1])
		//log.Printf("ciphertext decrypted: %s\n", string(plaintext))

	})

	flag.Parse()

	strPointerValue := *nonce
	lhs := []byte(strPointerValue)
	rhs := []byte("12345")

	if reflect.DeepEqual(lhs, rhs) {
		fmt.Println("MATCH")
	}

	server := http.Server{Addr: "0.0.0.0:8080"}

	fmt.Println("Enclave is listening at port 8080...")
	err := server.ListenAndServe()

	if err != nil {
		panic(err)
	}
}

// func verifyReport(reportbytes, signerId []byte) error {
// 	// Example nonce variable
// 	nonce := []byte("12345")

// 	signerArg := flag.String("s", "", "signer ID")
// 	flag.Parse()

// 	// get signer command line argument
// 	signer, err := hex.DecodeString(*signerArg)
// 	if err != nil {
// 		panic(err)
// 	}
// 	fmt.Println("Verifying the encalve identiy...")
// 	if !bytes.Equal(report.SignerID, signer) {
// 		return errors.New("invalid signer")
// 	}
// 	fmt.Println("The identy matched...")

// 	fmt.Println("Verifying the report")
// 	// Verify Report
// 	report, err := eclient.VerifyRemoteReport(reportBytes)
// 	if err != nil {
// 		panic(err)
// 	}

// 	fmt.Println("The report is matched...")

// 	// nonce --> Expected nonce
// 	hash := sha256.Sum256(append(certBytes, nonce...))

// 	fmt.Println("Checking if hash in report matches")

// 	if !bytes.Equal(report.Data[:len(hash)], hash[:]) {
// 		fmt.Print("report data does not match the certificate's hash")
// 	} else {
// 		fmt.Println("The report data match the certificate's hash")
// 	}

// 	fmt.Println("Remote attestation is succesful...")
//}
