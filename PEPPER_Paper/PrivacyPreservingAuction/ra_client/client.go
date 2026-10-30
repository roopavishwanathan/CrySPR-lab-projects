package main

import (
	"bytes"
	"math/rand"	
	"strconv"
	"crypto/x509"
	"crypto/sha256"
	"crypto/tls"
	"fmt"
	"io/ioutil"
	"net/http"
	"encoding/json"
	"io"
	ecies "github.com/ecies/go/v2"
	"encoding/hex"
	"flag"
	"time"
	"github.com/edgelesssys/ego/eclient"
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

	// Construct pk/
	pk, err := ecies.NewPublicKeyFromBytes(body)

	checkIfError(err)

	return pk
}

func main() {
	pk_url := "https://localhost:8080/pk"
	bid_dec_url := "https://localhost:8080/findWinner"


	signerArg := flag.String("s", "", "signer ID")

	// get signer command line argument
	signer, err := hex.DecodeString(*signerArg)
	if err != nil {
		panic(err)
	}
	// Example nonce variable
	//nonce := []byte("12345")
	var nonceL = flag.String("nonce", "12345", "Aggregated Nonce Variable")
	
	flag.Parse()

	nonce := []byte(*nonceL)

	// Server address
	server_url := "https://localhost:8080"
	
	
	fmt.Println("waiting enclave!!!")
	time.Sleep(8 * time.Second)

	tlsConfig := &tls.Config{InsecureSkipVerify: true}
	certBytes := httpGet(tlsConfig, server_url+"/cert")
	reportBytes := httpGet(tlsConfig, server_url+"/report")


	cert, _ := x509.ParseCertificate(certBytes)
	tlsConfig = &tls.Config{RootCAs: x509.NewCertPool(), ServerName: "localhost"}
	tlsConfig.RootCAs.AddCert(cert)
	

	// Retrive Public Key of Enclave!
        fmt.Println("Sent a request to retrieve enclave public key")
        pk := httpGetPK(tlsConfig, pk_url)
        fmt.Println("Received the public key of enclave")

	// Verify Report
	fmt.Println("Verifying the report...")
	report, err := eclient.VerifyRemoteReport(reportBytes)
	if err != nil {
		panic(err)
	}
	fmt.Println("report is verified...")
	
	// nonce --> Expected nonce
	hash := sha256.Sum256(append(certBytes, nonce...))
	
		fmt.Println("Verifying the encalve identiy...")
	if !bytes.Equal(report.SignerID, signer) {
		fmt.Println("Identy doesnt' match!")
	}
	fmt.Println("The identy matched...")

	fmt.Println("Checking if hash in report matches")
	if !bytes.Equal(report.Data[:len(hash)], hash[:]) {
		fmt.Print("report data does not match the certificate's hash")
	} else {
		fmt.Println("The report data match the certificate's hash")

	}

	fmt.Println("Remote Attestation is Successfull!!!")
	fmt.Println("Its time to find winner...")

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

	// Encrypt Samples
	//ciphertext, _ := ecies.Encrypt(pk, []byte("100000000000000000"))
	//ciphertext2, _ := ecies.Encrypt(pk, []byte("1000000000000"))
	//ciphertext3, _ := ecies.Encrypt(pk, []byte("30000000000000000"))
	//ciphertext4, _ := ecies.Encrypt(pk, []byte("50000000000000000"))
	//ciphertext5, _ := ecies.Encrypt(pk, []byte("3000000000000000"))
	//ciphertext6, _ := ecies.Encrypt(pk, []byte("100000000000000000"))

	//bs := map[string][]byte{"accountA": ciphertext, "accountB": ciphertext2, "accountC": ciphertext3, "accountD": ciphertext4, "accountE": ciphertext5, "accountF": ciphertext6}
	
	jsonValue, err := json.Marshal(bids_map)

	checkIfError(err)
	fmt.Println("Sent the encrypted bids...")
	client := http.Client{Transport: &http.Transport{TLSClientConfig: tlsConfig}}
	resp, err := client.Post(bid_dec_url, "application/json", bytes.NewBuffer(jsonValue))

	checkIfError(err)
	// Write the winner bid!
	winner, _ := io.ReadAll(resp.Body)
	
	fmt.Println("The winner address is")
	fmt.Println(string(winner))

	// Close
	client.Get("https://localhost:8080/closeApp")
}

func httpGetPK(tlsConfig *tls.Config, url string) *ecies.PublicKey {
	fmt.Println("get pk called")
	client := http.Client{Transport: &http.Transport{TLSClientConfig: tlsConfig}}
	resp, err := client.Get(url)
	if err != nil {
		panic(err)
	}
	defer resp.Body.Close()

	body, err := ioutil.ReadAll(resp.Body)

	if err != nil {
		print("ERror reading body")
	}
	fmt.Println(string(body))
	pk, _ := ecies.NewPublicKeyFromBytes(body)
	fmt.Println(pk)
	fmt.Println("end of body")

	// if resp.StatusCode != http.StatusOK {
	// 	panic(resp.Status)
	// }
	// print("AFTER status")
	// body, err := ioutil.ReadAll(resp.Body)
	// if err != nil {
	// 	panic(err)
	// }

	// Construct pk

	return pk
}


func httpGet(tlsConfig *tls.Config, url string) []byte {
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

