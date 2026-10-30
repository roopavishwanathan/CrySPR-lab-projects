// Code generated - DO NOT EDIT.
// This file is a generated binding and any manual changes will be lost.

package solidity_wrapper

import (
	"errors"
	"math/big"
	"strings"

	ethereum "github.com/ethereum/go-ethereum"
	"github.com/ethereum/go-ethereum/accounts/abi"
	"github.com/ethereum/go-ethereum/accounts/abi/bind"
	"github.com/ethereum/go-ethereum/common"
	"github.com/ethereum/go-ethereum/core/types"
	"github.com/ethereum/go-ethereum/event"
)

// Reference imports to suppress errors if they are not otherwise used.
var (
	_ = errors.New
	_ = big.NewInt
	_ = strings.NewReader
	_ = ethereum.NotFound
	_ = bind.Bind
	_ = common.Big1
	_ = types.BloomLookup
	_ = event.NewSubscription
)

// BidderMetaData contains all meta data concerning the Bidder contract.
var BidderMetaData = &bind.MetaData{
	ABI: "[{\"inputs\":[{\"internalType\":\"address\",\"name\":\"_addr\",\"type\":\"address\"}],\"stateMutability\":\"nonpayable\",\"type\":\"constructor\"},{\"inputs\":[{\"internalType\":\"address\",\"name\":\"\",\"type\":\"address\"}],\"name\":\"bids\",\"outputs\":[{\"internalType\":\"string\",\"name\":\"encryptedBid\",\"type\":\"string\"},{\"internalType\":\"uint256\",\"name\":\"deposit\",\"type\":\"uint256\"},{\"internalType\":\"bool\",\"name\":\"validUser\",\"type\":\"bool\"},{\"internalType\":\"bool\",\"name\":\"registered\",\"type\":\"bool\"},{\"internalType\":\"bool\",\"name\":\"providedNonce\",\"type\":\"bool\"},{\"internalType\":\"address\",\"name\":\"auctionOwnerAddress\",\"type\":\"address\"}],\"stateMutability\":\"view\",\"type\":\"function\"},{\"inputs\":[{\"internalType\":\"bytes32\",\"name\":\"messageHash\",\"type\":\"bytes32\"}],\"name\":\"getEthSignedMessageHash\",\"outputs\":[{\"internalType\":\"bytes32\",\"name\":\"\",\"type\":\"bytes32\"}],\"stateMutability\":\"pure\",\"type\":\"function\"},{\"inputs\":[{\"internalType\":\"address\",\"name\":\"account\",\"type\":\"address\"},{\"internalType\":\"uint256\",\"name\":\"id\",\"type\":\"uint256\"}],\"name\":\"getMessageHash\",\"outputs\":[{\"internalType\":\"bytes32\",\"name\":\"\",\"type\":\"bytes32\"}],\"stateMutability\":\"pure\",\"type\":\"function\"},{\"inputs\":[{\"internalType\":\"address\",\"name\":\"_auctionAddress\",\"type\":\"address\"}],\"name\":\"hash\",\"outputs\":[{\"internalType\":\"bytes32\",\"name\":\"\",\"type\":\"bytes32\"}],\"stateMutability\":\"view\",\"type\":\"function\"},{\"inputs\":[{\"internalType\":\"bytes32\",\"name\":\"_ethSignedMessageHash\",\"type\":\"bytes32\"},{\"internalType\":\"bytes\",\"name\":\"_signature\",\"type\":\"bytes\"}],\"name\":\"recoverSigner\",\"outputs\":[{\"internalType\":\"address\",\"name\":\"\",\"type\":\"address\"}],\"stateMutability\":\"pure\",\"type\":\"function\"},{\"inputs\":[{\"internalType\":\"address\",\"name\":\"_auctionAddress\",\"type\":\"address\"}],\"name\":\"refundDeposit\",\"outputs\":[],\"stateMutability\":\"payable\",\"type\":\"function\"},{\"inputs\":[{\"internalType\":\"address\",\"name\":\"_auctionAddress\",\"type\":\"address\"},{\"internalType\":\"uint256\",\"name\":\"_nonceVal\",\"type\":\"uint256\"}],\"name\":\"registerBidder\",\"outputs\":[],\"stateMutability\":\"payable\",\"type\":\"function\"},{\"inputs\":[{\"internalType\":\"address\",\"name\":\"_auctionAddress\",\"type\":\"address\"},{\"internalType\":\"string\",\"name\":\"_encryptedBid\",\"type\":\"string\"}],\"name\":\"sendBid\",\"outputs\":[],\"stateMutability\":\"payable\",\"type\":\"function\"},{\"inputs\":[{\"internalType\":\"address\",\"name\":\"_auctionAddress\",\"type\":\"address\"},{\"internalType\":\"address\",\"name\":\"winner\",\"type\":\"address\"},{\"internalType\":\"uint256\",\"name\":\"id\",\"type\":\"uint256\"},{\"internalType\":\"bytes\",\"name\":\"signature\",\"type\":\"bytes\"}],\"name\":\"signatureVerification\",\"outputs\":[],\"stateMutability\":\"nonpayable\",\"type\":\"function\"},{\"inputs\":[{\"internalType\":\"bytes\",\"name\":\"signature\",\"type\":\"bytes\"}],\"name\":\"splitSignature\",\"outputs\":[{\"internalType\":\"bytes32\",\"name\":\"r\",\"type\":\"bytes32\"},{\"internalType\":\"bytes32\",\"name\":\"s\",\"type\":\"bytes32\"},{\"internalType\":\"uint8\",\"name\":\"v\",\"type\":\"uint8\"}],\"stateMutability\":\"pure\",\"type\":\"function\"},{\"inputs\":[],\"name\":\"totalBidder\",\"outputs\":[{\"internalType\":\"uint256\",\"name\":\"\",\"type\":\"uint256\"}],\"stateMutability\":\"view\",\"type\":\"function\"}]",
}

// BidderABI is the input ABI used to generate the binding from.
// Deprecated: Use BidderMetaData.ABI instead.
var BidderABI = BidderMetaData.ABI

// Bidder is an auto generated Go binding around an Ethereum contract.
type Bidder struct {
	BidderCaller     // Read-only binding to the contract
	BidderTransactor // Write-only binding to the contract
	BidderFilterer   // Log filterer for contract events
}

// BidderCaller is an auto generated read-only Go binding around an Ethereum contract.
type BidderCaller struct {
	contract *bind.BoundContract // Generic contract wrapper for the low level calls
}

// BidderTransactor is an auto generated write-only Go binding around an Ethereum contract.
type BidderTransactor struct {
	contract *bind.BoundContract // Generic contract wrapper for the low level calls
}

// BidderFilterer is an auto generated log filtering Go binding around an Ethereum contract events.
type BidderFilterer struct {
	contract *bind.BoundContract // Generic contract wrapper for the low level calls
}

// BidderSession is an auto generated Go binding around an Ethereum contract,
// with pre-set call and transact options.
type BidderSession struct {
	Contract     *Bidder           // Generic contract binding to set the session for
	CallOpts     bind.CallOpts     // Call options to use throughout this session
	TransactOpts bind.TransactOpts // Transaction auth options to use throughout this session
}

// BidderCallerSession is an auto generated read-only Go binding around an Ethereum contract,
// with pre-set call options.
type BidderCallerSession struct {
	Contract *BidderCaller // Generic contract caller binding to set the session for
	CallOpts bind.CallOpts // Call options to use throughout this session
}

// BidderTransactorSession is an auto generated write-only Go binding around an Ethereum contract,
// with pre-set transact options.
type BidderTransactorSession struct {
	Contract     *BidderTransactor // Generic contract transactor binding to set the session for
	TransactOpts bind.TransactOpts // Transaction auth options to use throughout this session
}

// BidderRaw is an auto generated low-level Go binding around an Ethereum contract.
type BidderRaw struct {
	Contract *Bidder // Generic contract binding to access the raw methods on
}

// BidderCallerRaw is an auto generated low-level read-only Go binding around an Ethereum contract.
type BidderCallerRaw struct {
	Contract *BidderCaller // Generic read-only contract binding to access the raw methods on
}

// BidderTransactorRaw is an auto generated low-level write-only Go binding around an Ethereum contract.
type BidderTransactorRaw struct {
	Contract *BidderTransactor // Generic write-only contract binding to access the raw methods on
}

// NewBidder creates a new instance of Bidder, bound to a specific deployed contract.
func NewBidder(address common.Address, backend bind.ContractBackend) (*Bidder, error) {
	contract, err := bindBidder(address, backend, backend, backend)
	if err != nil {
		return nil, err
	}
	return &Bidder{BidderCaller: BidderCaller{contract: contract}, BidderTransactor: BidderTransactor{contract: contract}, BidderFilterer: BidderFilterer{contract: contract}}, nil
}

// NewBidderCaller creates a new read-only instance of Bidder, bound to a specific deployed contract.
func NewBidderCaller(address common.Address, caller bind.ContractCaller) (*BidderCaller, error) {
	contract, err := bindBidder(address, caller, nil, nil)
	if err != nil {
		return nil, err
	}
	return &BidderCaller{contract: contract}, nil
}

// NewBidderTransactor creates a new write-only instance of Bidder, bound to a specific deployed contract.
func NewBidderTransactor(address common.Address, transactor bind.ContractTransactor) (*BidderTransactor, error) {
	contract, err := bindBidder(address, nil, transactor, nil)
	if err != nil {
		return nil, err
	}
	return &BidderTransactor{contract: contract}, nil
}

// NewBidderFilterer creates a new log filterer instance of Bidder, bound to a specific deployed contract.
func NewBidderFilterer(address common.Address, filterer bind.ContractFilterer) (*BidderFilterer, error) {
	contract, err := bindBidder(address, nil, nil, filterer)
	if err != nil {
		return nil, err
	}
	return &BidderFilterer{contract: contract}, nil
}

// bindBidder binds a generic wrapper to an already deployed contract.
func bindBidder(address common.Address, caller bind.ContractCaller, transactor bind.ContractTransactor, filterer bind.ContractFilterer) (*bind.BoundContract, error) {
	parsed, err := abi.JSON(strings.NewReader(BidderABI))
	if err != nil {
		return nil, err
	}
	return bind.NewBoundContract(address, parsed, caller, transactor, filterer), nil
}

// Call invokes the (constant) contract method with params as input values and
// sets the output to result. The result type might be a single field for simple
// returns, a slice of interfaces for anonymous returns and a struct for named
// returns.
func (_Bidder *BidderRaw) Call(opts *bind.CallOpts, result *[]interface{}, method string, params ...interface{}) error {
	return _Bidder.Contract.BidderCaller.contract.Call(opts, result, method, params...)
}

// Transfer initiates a plain transaction to move funds to the contract, calling
// its default method if one is available.
func (_Bidder *BidderRaw) Transfer(opts *bind.TransactOpts) (*types.Transaction, error) {
	return _Bidder.Contract.BidderTransactor.contract.Transfer(opts)
}

// Transact invokes the (paid) contract method with params as input values.
func (_Bidder *BidderRaw) Transact(opts *bind.TransactOpts, method string, params ...interface{}) (*types.Transaction, error) {
	return _Bidder.Contract.BidderTransactor.contract.Transact(opts, method, params...)
}

// Call invokes the (constant) contract method with params as input values and
// sets the output to result. The result type might be a single field for simple
// returns, a slice of interfaces for anonymous returns and a struct for named
// returns.
func (_Bidder *BidderCallerRaw) Call(opts *bind.CallOpts, result *[]interface{}, method string, params ...interface{}) error {
	return _Bidder.Contract.contract.Call(opts, result, method, params...)
}

// Transfer initiates a plain transaction to move funds to the contract, calling
// its default method if one is available.
func (_Bidder *BidderTransactorRaw) Transfer(opts *bind.TransactOpts) (*types.Transaction, error) {
	return _Bidder.Contract.contract.Transfer(opts)
}

// Transact invokes the (paid) contract method with params as input values.
func (_Bidder *BidderTransactorRaw) Transact(opts *bind.TransactOpts, method string, params ...interface{}) (*types.Transaction, error) {
	return _Bidder.Contract.contract.Transact(opts, method, params...)
}

// Bids is a free data retrieval call binding the contract method 0x62ea82db.
//
// Solidity: function bids(address ) view returns(string encryptedBid, uint256 deposit, bool validUser, bool registered, bool providedNonce, address auctionOwnerAddress)
func (_Bidder *BidderCaller) Bids(opts *bind.CallOpts, arg0 common.Address) (struct {
	EncryptedBid        string
	Deposit             *big.Int
	ValidUser           bool
	Registered          bool
	ProvidedNonce       bool
	AuctionOwnerAddress common.Address
}, error) {
	var out []interface{}
	err := _Bidder.contract.Call(opts, &out, "bids", arg0)

	outstruct := new(struct {
		EncryptedBid        string
		Deposit             *big.Int
		ValidUser           bool
		Registered          bool
		ProvidedNonce       bool
		AuctionOwnerAddress common.Address
	})
	if err != nil {
		return *outstruct, err
	}

	outstruct.EncryptedBid = *abi.ConvertType(out[0], new(string)).(*string)
	outstruct.Deposit = *abi.ConvertType(out[1], new(*big.Int)).(**big.Int)
	outstruct.ValidUser = *abi.ConvertType(out[2], new(bool)).(*bool)
	outstruct.Registered = *abi.ConvertType(out[3], new(bool)).(*bool)
	outstruct.ProvidedNonce = *abi.ConvertType(out[4], new(bool)).(*bool)
	outstruct.AuctionOwnerAddress = *abi.ConvertType(out[5], new(common.Address)).(*common.Address)

	return *outstruct, err

}

// Bids is a free data retrieval call binding the contract method 0x62ea82db.
//
// Solidity: function bids(address ) view returns(string encryptedBid, uint256 deposit, bool validUser, bool registered, bool providedNonce, address auctionOwnerAddress)
func (_Bidder *BidderSession) Bids(arg0 common.Address) (struct {
	EncryptedBid        string
	Deposit             *big.Int
	ValidUser           bool
	Registered          bool
	ProvidedNonce       bool
	AuctionOwnerAddress common.Address
}, error) {
	return _Bidder.Contract.Bids(&_Bidder.CallOpts, arg0)
}

// Bids is a free data retrieval call binding the contract method 0x62ea82db.
//
// Solidity: function bids(address ) view returns(string encryptedBid, uint256 deposit, bool validUser, bool registered, bool providedNonce, address auctionOwnerAddress)
func (_Bidder *BidderCallerSession) Bids(arg0 common.Address) (struct {
	EncryptedBid        string
	Deposit             *big.Int
	ValidUser           bool
	Registered          bool
	ProvidedNonce       bool
	AuctionOwnerAddress common.Address
}, error) {
	return _Bidder.Contract.Bids(&_Bidder.CallOpts, arg0)
}

// GetEthSignedMessageHash is a free data retrieval call binding the contract method 0xfa540801.
//
// Solidity: function getEthSignedMessageHash(bytes32 messageHash) pure returns(bytes32)
func (_Bidder *BidderCaller) GetEthSignedMessageHash(opts *bind.CallOpts, messageHash [32]byte) ([32]byte, error) {
	var out []interface{}
	err := _Bidder.contract.Call(opts, &out, "getEthSignedMessageHash", messageHash)

	if err != nil {
		return *new([32]byte), err
	}

	out0 := *abi.ConvertType(out[0], new([32]byte)).(*[32]byte)

	return out0, err

}

// GetEthSignedMessageHash is a free data retrieval call binding the contract method 0xfa540801.
//
// Solidity: function getEthSignedMessageHash(bytes32 messageHash) pure returns(bytes32)
func (_Bidder *BidderSession) GetEthSignedMessageHash(messageHash [32]byte) ([32]byte, error) {
	return _Bidder.Contract.GetEthSignedMessageHash(&_Bidder.CallOpts, messageHash)
}

// GetEthSignedMessageHash is a free data retrieval call binding the contract method 0xfa540801.
//
// Solidity: function getEthSignedMessageHash(bytes32 messageHash) pure returns(bytes32)
func (_Bidder *BidderCallerSession) GetEthSignedMessageHash(messageHash [32]byte) ([32]byte, error) {
	return _Bidder.Contract.GetEthSignedMessageHash(&_Bidder.CallOpts, messageHash)
}

// GetMessageHash is a free data retrieval call binding the contract method 0x512c91df.
//
// Solidity: function getMessageHash(address account, uint256 id) pure returns(bytes32)
func (_Bidder *BidderCaller) GetMessageHash(opts *bind.CallOpts, account common.Address, id *big.Int) ([32]byte, error) {
	var out []interface{}
	err := _Bidder.contract.Call(opts, &out, "getMessageHash", account, id)

	if err != nil {
		return *new([32]byte), err
	}

	out0 := *abi.ConvertType(out[0], new([32]byte)).(*[32]byte)

	return out0, err

}

// GetMessageHash is a free data retrieval call binding the contract method 0x512c91df.
//
// Solidity: function getMessageHash(address account, uint256 id) pure returns(bytes32)
func (_Bidder *BidderSession) GetMessageHash(account common.Address, id *big.Int) ([32]byte, error) {
	return _Bidder.Contract.GetMessageHash(&_Bidder.CallOpts, account, id)
}

// GetMessageHash is a free data retrieval call binding the contract method 0x512c91df.
//
// Solidity: function getMessageHash(address account, uint256 id) pure returns(bytes32)
func (_Bidder *BidderCallerSession) GetMessageHash(account common.Address, id *big.Int) ([32]byte, error) {
	return _Bidder.Contract.GetMessageHash(&_Bidder.CallOpts, account, id)
}

// Hash is a free data retrieval call binding the contract method 0x7e809973.
//
// Solidity: function hash(address _auctionAddress) view returns(bytes32)
func (_Bidder *BidderCaller) Hash(opts *bind.CallOpts, _auctionAddress common.Address) ([32]byte, error) {
	var out []interface{}
	err := _Bidder.contract.Call(opts, &out, "hash", _auctionAddress)

	if err != nil {
		return *new([32]byte), err
	}

	out0 := *abi.ConvertType(out[0], new([32]byte)).(*[32]byte)

	return out0, err

}

// Hash is a free data retrieval call binding the contract method 0x7e809973.
//
// Solidity: function hash(address _auctionAddress) view returns(bytes32)
func (_Bidder *BidderSession) Hash(_auctionAddress common.Address) ([32]byte, error) {
	return _Bidder.Contract.Hash(&_Bidder.CallOpts, _auctionAddress)
}

// Hash is a free data retrieval call binding the contract method 0x7e809973.
//
// Solidity: function hash(address _auctionAddress) view returns(bytes32)
func (_Bidder *BidderCallerSession) Hash(_auctionAddress common.Address) ([32]byte, error) {
	return _Bidder.Contract.Hash(&_Bidder.CallOpts, _auctionAddress)
}

// RecoverSigner is a free data retrieval call binding the contract method 0x97aba7f9.
//
// Solidity: function recoverSigner(bytes32 _ethSignedMessageHash, bytes _signature) pure returns(address)
func (_Bidder *BidderCaller) RecoverSigner(opts *bind.CallOpts, _ethSignedMessageHash [32]byte, _signature []byte) (common.Address, error) {
	var out []interface{}
	err := _Bidder.contract.Call(opts, &out, "recoverSigner", _ethSignedMessageHash, _signature)

	if err != nil {
		return *new(common.Address), err
	}

	out0 := *abi.ConvertType(out[0], new(common.Address)).(*common.Address)

	return out0, err

}

// RecoverSigner is a free data retrieval call binding the contract method 0x97aba7f9.
//
// Solidity: function recoverSigner(bytes32 _ethSignedMessageHash, bytes _signature) pure returns(address)
func (_Bidder *BidderSession) RecoverSigner(_ethSignedMessageHash [32]byte, _signature []byte) (common.Address, error) {
	return _Bidder.Contract.RecoverSigner(&_Bidder.CallOpts, _ethSignedMessageHash, _signature)
}

// RecoverSigner is a free data retrieval call binding the contract method 0x97aba7f9.
//
// Solidity: function recoverSigner(bytes32 _ethSignedMessageHash, bytes _signature) pure returns(address)
func (_Bidder *BidderCallerSession) RecoverSigner(_ethSignedMessageHash [32]byte, _signature []byte) (common.Address, error) {
	return _Bidder.Contract.RecoverSigner(&_Bidder.CallOpts, _ethSignedMessageHash, _signature)
}

// SplitSignature is a free data retrieval call binding the contract method 0xa7bb5803.
//
// Solidity: function splitSignature(bytes signature) pure returns(bytes32 r, bytes32 s, uint8 v)
func (_Bidder *BidderCaller) SplitSignature(opts *bind.CallOpts, signature []byte) (struct {
	R [32]byte
	S [32]byte
	V uint8
}, error) {
	var out []interface{}
	err := _Bidder.contract.Call(opts, &out, "splitSignature", signature)

	outstruct := new(struct {
		R [32]byte
		S [32]byte
		V uint8
	})
	if err != nil {
		return *outstruct, err
	}

	outstruct.R = *abi.ConvertType(out[0], new([32]byte)).(*[32]byte)
	outstruct.S = *abi.ConvertType(out[1], new([32]byte)).(*[32]byte)
	outstruct.V = *abi.ConvertType(out[2], new(uint8)).(*uint8)

	return *outstruct, err

}

// SplitSignature is a free data retrieval call binding the contract method 0xa7bb5803.
//
// Solidity: function splitSignature(bytes signature) pure returns(bytes32 r, bytes32 s, uint8 v)
func (_Bidder *BidderSession) SplitSignature(signature []byte) (struct {
	R [32]byte
	S [32]byte
	V uint8
}, error) {
	return _Bidder.Contract.SplitSignature(&_Bidder.CallOpts, signature)
}

// SplitSignature is a free data retrieval call binding the contract method 0xa7bb5803.
//
// Solidity: function splitSignature(bytes signature) pure returns(bytes32 r, bytes32 s, uint8 v)
func (_Bidder *BidderCallerSession) SplitSignature(signature []byte) (struct {
	R [32]byte
	S [32]byte
	V uint8
}, error) {
	return _Bidder.Contract.SplitSignature(&_Bidder.CallOpts, signature)
}

// TotalBidder is a free data retrieval call binding the contract method 0x77439937.
//
// Solidity: function totalBidder() view returns(uint256)
func (_Bidder *BidderCaller) TotalBidder(opts *bind.CallOpts) (*big.Int, error) {
	var out []interface{}
	err := _Bidder.contract.Call(opts, &out, "totalBidder")

	if err != nil {
		return *new(*big.Int), err
	}

	out0 := *abi.ConvertType(out[0], new(*big.Int)).(**big.Int)

	return out0, err

}

// TotalBidder is a free data retrieval call binding the contract method 0x77439937.
//
// Solidity: function totalBidder() view returns(uint256)
func (_Bidder *BidderSession) TotalBidder() (*big.Int, error) {
	return _Bidder.Contract.TotalBidder(&_Bidder.CallOpts)
}

// TotalBidder is a free data retrieval call binding the contract method 0x77439937.
//
// Solidity: function totalBidder() view returns(uint256)
func (_Bidder *BidderCallerSession) TotalBidder() (*big.Int, error) {
	return _Bidder.Contract.TotalBidder(&_Bidder.CallOpts)
}

// RefundDeposit is a paid mutator transaction binding the contract method 0xf1471676.
//
// Solidity: function refundDeposit(address _auctionAddress) payable returns()
func (_Bidder *BidderTransactor) RefundDeposit(opts *bind.TransactOpts, _auctionAddress common.Address) (*types.Transaction, error) {
	return _Bidder.contract.Transact(opts, "refundDeposit", _auctionAddress)
}

// RefundDeposit is a paid mutator transaction binding the contract method 0xf1471676.
//
// Solidity: function refundDeposit(address _auctionAddress) payable returns()
func (_Bidder *BidderSession) RefundDeposit(_auctionAddress common.Address) (*types.Transaction, error) {
	return _Bidder.Contract.RefundDeposit(&_Bidder.TransactOpts, _auctionAddress)
}

// RefundDeposit is a paid mutator transaction binding the contract method 0xf1471676.
//
// Solidity: function refundDeposit(address _auctionAddress) payable returns()
func (_Bidder *BidderTransactorSession) RefundDeposit(_auctionAddress common.Address) (*types.Transaction, error) {
	return _Bidder.Contract.RefundDeposit(&_Bidder.TransactOpts, _auctionAddress)
}

// RegisterBidder is a paid mutator transaction binding the contract method 0x907e5cf7.
//
// Solidity: function registerBidder(address _auctionAddress, uint256 _nonceVal) payable returns()
func (_Bidder *BidderTransactor) RegisterBidder(opts *bind.TransactOpts, _auctionAddress common.Address, _nonceVal *big.Int) (*types.Transaction, error) {
	return _Bidder.contract.Transact(opts, "registerBidder", _auctionAddress, _nonceVal)
}

// RegisterBidder is a paid mutator transaction binding the contract method 0x907e5cf7.
//
// Solidity: function registerBidder(address _auctionAddress, uint256 _nonceVal) payable returns()
func (_Bidder *BidderSession) RegisterBidder(_auctionAddress common.Address, _nonceVal *big.Int) (*types.Transaction, error) {
	return _Bidder.Contract.RegisterBidder(&_Bidder.TransactOpts, _auctionAddress, _nonceVal)
}

// RegisterBidder is a paid mutator transaction binding the contract method 0x907e5cf7.
//
// Solidity: function registerBidder(address _auctionAddress, uint256 _nonceVal) payable returns()
func (_Bidder *BidderTransactorSession) RegisterBidder(_auctionAddress common.Address, _nonceVal *big.Int) (*types.Transaction, error) {
	return _Bidder.Contract.RegisterBidder(&_Bidder.TransactOpts, _auctionAddress, _nonceVal)
}

// SendBid is a paid mutator transaction binding the contract method 0x7dafed42.
//
// Solidity: function sendBid(address _auctionAddress, string _encryptedBid) payable returns()
func (_Bidder *BidderTransactor) SendBid(opts *bind.TransactOpts, _auctionAddress common.Address, _encryptedBid string) (*types.Transaction, error) {
	return _Bidder.contract.Transact(opts, "sendBid", _auctionAddress, _encryptedBid)
}

// SendBid is a paid mutator transaction binding the contract method 0x7dafed42.
//
// Solidity: function sendBid(address _auctionAddress, string _encryptedBid) payable returns()
func (_Bidder *BidderSession) SendBid(_auctionAddress common.Address, _encryptedBid string) (*types.Transaction, error) {
	return _Bidder.Contract.SendBid(&_Bidder.TransactOpts, _auctionAddress, _encryptedBid)
}

// SendBid is a paid mutator transaction binding the contract method 0x7dafed42.
//
// Solidity: function sendBid(address _auctionAddress, string _encryptedBid) payable returns()
func (_Bidder *BidderTransactorSession) SendBid(_auctionAddress common.Address, _encryptedBid string) (*types.Transaction, error) {
	return _Bidder.Contract.SendBid(&_Bidder.TransactOpts, _auctionAddress, _encryptedBid)
}

// SignatureVerification is a paid mutator transaction binding the contract method 0xcbb95f6a.
//
// Solidity: function signatureVerification(address _auctionAddress, address winner, uint256 id, bytes signature) returns()
func (_Bidder *BidderTransactor) SignatureVerification(opts *bind.TransactOpts, _auctionAddress common.Address, winner common.Address, id *big.Int, signature []byte) (*types.Transaction, error) {
	return _Bidder.contract.Transact(opts, "signatureVerification", _auctionAddress, winner, id, signature)
}

// SignatureVerification is a paid mutator transaction binding the contract method 0xcbb95f6a.
//
// Solidity: function signatureVerification(address _auctionAddress, address winner, uint256 id, bytes signature) returns()
func (_Bidder *BidderSession) SignatureVerification(_auctionAddress common.Address, winner common.Address, id *big.Int, signature []byte) (*types.Transaction, error) {
	return _Bidder.Contract.SignatureVerification(&_Bidder.TransactOpts, _auctionAddress, winner, id, signature)
}

// SignatureVerification is a paid mutator transaction binding the contract method 0xcbb95f6a.
//
// Solidity: function signatureVerification(address _auctionAddress, address winner, uint256 id, bytes signature) returns()
func (_Bidder *BidderTransactorSession) SignatureVerification(_auctionAddress common.Address, winner common.Address, id *big.Int, signature []byte) (*types.Transaction, error) {
	return _Bidder.Contract.SignatureVerification(&_Bidder.TransactOpts, _auctionAddress, winner, id, signature)
}
