# Privacy Preserving Auction
Proof of concept implementation of PEC Auction Framework. Implemented using Solidity, Go and Python. 

#### Dependencies
- EGo
- Brownie and Ganache-CLI

#### How to Run?
```ego-go build server.go```

```ego sign server```

```Compile client.go```

```brownie run scripts/deploy.py --network ganache-zero```
#### Network Details
```brownie networks add development ganache-zero cmd=ganache-cli host=http://0.0.0.0 accounts=15 mnemonic=brownie port=8545```

