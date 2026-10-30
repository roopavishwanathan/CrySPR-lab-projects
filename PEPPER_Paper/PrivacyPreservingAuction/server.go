package main

import (
	"crypto"
	"os"
	"crypto/rand"
	"crypto/rsa"
	"crypto/sha256"
	"crypto/tls"
	"crypto/x509"
	"crypto/x509/pkix"
	"fmt"
	"encoding/json"
	"strconv"
		"io/ioutil"

	"math/big"
	"net/http"
	"time"
	"flag"
	"log"
	ecies "github.com/ecies/go/v2"
	"github.com/edgelesssys/ego/enclave"
)
var k, _ = ecies.GenerateKey()

func main() {

	// This value will be retrieved by Manager from SC
	// nonce := []byte("12345")
	
	var nonceL = flag.String("nonce", "12345", "Aggregated Nonce Variable")
	flag.Parse()
	nonce := []byte(*nonceL)

	// Generate x509 certificate.
	cert, priv := createCertificate()

	// x = cert || nonce
	appended := append(cert, nonce...)

	// h = H(x)
	hash := sha256.Sum256(appended)

	// Include hash in the extra field in report!
	report, err := enclave.GetRemoteReport(hash[:])

	if err != nil {
		fmt.Println(err)
	}


	//Finding Winner
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
			//fmt.Println("Key: ", z, " => ", "Decrypted: ", val)
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

	// Create HTTPS server.
	http.HandleFunc("/cert", func(w http.ResponseWriter, r *http.Request) {
		fmt.Println("Certificate is requested")
		w.Write(cert)
	})


	// Create HTTPS server.
        http.HandleFunc("/closeApp", func(w http.ResponseWriter, r *http.Request) {
                fmt.Println("")
		fmt.Println("We have a winner, killing the enclave now!")		
                os.Exit(0)
        })


	http.HandleFunc("/report", func(w http.ResponseWriter, r *http.Request) {
		fmt.Println("Report is requested. ")
		w.Write(report)
	})
	http.HandleFunc("/nonce", func(w http.ResponseWriter, r *http.Request) {
		fmt.Println(2+2);
		fmt.Println("Nonce is requested.")
		w.Write(nonce)
	})
	// Retrieveing the pk
                http.HandleFunc("/pk", func(w http.ResponseWriter, r *http.Request) {
                fmt.Println("pk requested")
                log.Println("key pair has been generated")
                log.Println(k.PublicKey)
                var test []byte
                test = k.PublicKey.Bytes(false)

                w.Write(test)
                //log.Println(ecies.NewPublicKeyFromBytes(test))
        })

	tlsCfg := tls.Config{
		Certificates: []tls.Certificate{
			{
				Certificate: [][]byte{cert},
				PrivateKey:  priv,
			},
		},
	}

	server := http.Server{Addr: "0.0.0.0:8080", TLSConfig: &tlsCfg}

	fmt.Println("listening to 0.0.0.0:8080")
	_ = server.ListenAndServeTLS("", "")
	//fmt.Println(err)
}

func createCertificate() ([]byte, crypto.PrivateKey) {
	template := &x509.Certificate{
		SerialNumber: &big.Int{},
		Subject:      pkix.Name{CommonName: "localhost"},
		NotAfter:     time.Now().Add(time.Hour),
		DNSNames:     []string{"localhost"},
	}
	priv, _ := rsa.GenerateKey(rand.Reader, 2048)
	cert, _ := x509.CreateCertificate(rand.Reader, template, template, &priv.PublicKey, priv)
	return cert, priv
}

