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

// IAuctionMetaData contains all meta data concerning the IAuction contract.
var IAuctionMetaData = &bind.MetaData{
	ABI: "[{\"inputs\":[{\"internalType\":\"address\",\"name\":\"_auctionAdress\",\"type\":\"address\"},{\"internalType\":\"address\",\"name\":\"_winner\",\"type\":\"address\"}],\"name\":\"declareWinner\",\"outputs\":[],\"stateMutability\":\"nonpayable\",\"type\":\"function\"},{\"inputs\":[{\"internalType\":\"address\",\"name\":\"_auctionAddress\",\"type\":\"address\"},{\"internalType\":\"uint256\",\"name\":\"_auctionNonce\",\"type\":\"uint256\"}],\"name\":\"updateNonce\",\"outputs\":[],\"stateMutability\":\"nonpayable\",\"type\":\"function\"}]",
}

// IAuctionABI is the input ABI used to generate the binding from.
// Deprecated: Use IAuctionMetaData.ABI instead.
var IAuctionABI = IAuctionMetaData.ABI

// IAuction is an auto generated Go binding around an Ethereum contract.
type IAuction struct {
	IAuctionCaller     // Read-only binding to the contract
	IAuctionTransactor // Write-only binding to the contract
	IAuctionFilterer   // Log filterer for contract events
}

// IAuctionCaller is an auto generated read-only Go binding around an Ethereum contract.
type IAuctionCaller struct {
	contract *bind.BoundContract // Generic contract wrapper for the low level calls
}

// IAuctionTransactor is an auto generated write-only Go binding around an Ethereum contract.
type IAuctionTransactor struct {
	contract *bind.BoundContract // Generic contract wrapper for the low level calls
}

// IAuctionFilterer is an auto generated log filtering Go binding around an Ethereum contract events.
type IAuctionFilterer struct {
	contract *bind.BoundContract // Generic contract wrapper for the low level calls
}

// IAuctionSession is an auto generated Go binding around an Ethereum contract,
// with pre-set call and transact options.
type IAuctionSession struct {
	Contract     *IAuction         // Generic contract binding to set the session for
	CallOpts     bind.CallOpts     // Call options to use throughout this session
	TransactOpts bind.TransactOpts // Transaction auth options to use throughout this session
}

// IAuctionCallerSession is an auto generated read-only Go binding around an Ethereum contract,
// with pre-set call options.
type IAuctionCallerSession struct {
	Contract *IAuctionCaller // Generic contract caller binding to set the session for
	CallOpts bind.CallOpts   // Call options to use throughout this session
}

// IAuctionTransactorSession is an auto generated write-only Go binding around an Ethereum contract,
// with pre-set transact options.
type IAuctionTransactorSession struct {
	Contract     *IAuctionTransactor // Generic contract transactor binding to set the session for
	TransactOpts bind.TransactOpts   // Transaction auth options to use throughout this session
}

// IAuctionRaw is an auto generated low-level Go binding around an Ethereum contract.
type IAuctionRaw struct {
	Contract *IAuction // Generic contract binding to access the raw methods on
}

// IAuctionCallerRaw is an auto generated low-level read-only Go binding around an Ethereum contract.
type IAuctionCallerRaw struct {
	Contract *IAuctionCaller // Generic read-only contract binding to access the raw methods on
}

// IAuctionTransactorRaw is an auto generated low-level write-only Go binding around an Ethereum contract.
type IAuctionTransactorRaw struct {
	Contract *IAuctionTransactor // Generic write-only contract binding to access the raw methods on
}

// NewIAuction creates a new instance of IAuction, bound to a specific deployed contract.
func NewIAuction(address common.Address, backend bind.ContractBackend) (*IAuction, error) {
	contract, err := bindIAuction(address, backend, backend, backend)
	if err != nil {
		return nil, err
	}
	return &IAuction{IAuctionCaller: IAuctionCaller{contract: contract}, IAuctionTransactor: IAuctionTransactor{contract: contract}, IAuctionFilterer: IAuctionFilterer{contract: contract}}, nil
}

// NewIAuctionCaller creates a new read-only instance of IAuction, bound to a specific deployed contract.
func NewIAuctionCaller(address common.Address, caller bind.ContractCaller) (*IAuctionCaller, error) {
	contract, err := bindIAuction(address, caller, nil, nil)
	if err != nil {
		return nil, err
	}
	return &IAuctionCaller{contract: contract}, nil
}

// NewIAuctionTransactor creates a new write-only instance of IAuction, bound to a specific deployed contract.
func NewIAuctionTransactor(address common.Address, transactor bind.ContractTransactor) (*IAuctionTransactor, error) {
	contract, err := bindIAuction(address, nil, transactor, nil)
	if err != nil {
		return nil, err
	}
	return &IAuctionTransactor{contract: contract}, nil
}

// NewIAuctionFilterer creates a new log filterer instance of IAuction, bound to a specific deployed contract.
func NewIAuctionFilterer(address common.Address, filterer bind.ContractFilterer) (*IAuctionFilterer, error) {
	contract, err := bindIAuction(address, nil, nil, filterer)
	if err != nil {
		return nil, err
	}
	return &IAuctionFilterer{contract: contract}, nil
}

// bindIAuction binds a generic wrapper to an already deployed contract.
func bindIAuction(address common.Address, caller bind.ContractCaller, transactor bind.ContractTransactor, filterer bind.ContractFilterer) (*bind.BoundContract, error) {
	parsed, err := abi.JSON(strings.NewReader(IAuctionABI))
	if err != nil {
		return nil, err
	}
	return bind.NewBoundContract(address, parsed, caller, transactor, filterer), nil
}

// Call invokes the (constant) contract method with params as input values and
// sets the output to result. The result type might be a single field for simple
// returns, a slice of interfaces for anonymous returns and a struct for named
// returns.
func (_IAuction *IAuctionRaw) Call(opts *bind.CallOpts, result *[]interface{}, method string, params ...interface{}) error {
	return _IAuction.Contract.IAuctionCaller.contract.Call(opts, result, method, params...)
}

// Transfer initiates a plain transaction to move funds to the contract, calling
// its default method if one is available.
func (_IAuction *IAuctionRaw) Transfer(opts *bind.TransactOpts) (*types.Transaction, error) {
	return _IAuction.Contract.IAuctionTransactor.contract.Transfer(opts)
}

// Transact invokes the (paid) contract method with params as input values.
func (_IAuction *IAuctionRaw) Transact(opts *bind.TransactOpts, method string, params ...interface{}) (*types.Transaction, error) {
	return _IAuction.Contract.IAuctionTransactor.contract.Transact(opts, method, params...)
}

// Call invokes the (constant) contract method with params as input values and
// sets the output to result. The result type might be a single field for simple
// returns, a slice of interfaces for anonymous returns and a struct for named
// returns.
func (_IAuction *IAuctionCallerRaw) Call(opts *bind.CallOpts, result *[]interface{}, method string, params ...interface{}) error {
	return _IAuction.Contract.contract.Call(opts, result, method, params...)
}

// Transfer initiates a plain transaction to move funds to the contract, calling
// its default method if one is available.
func (_IAuction *IAuctionTransactorRaw) Transfer(opts *bind.TransactOpts) (*types.Transaction, error) {
	return _IAuction.Contract.contract.Transfer(opts)
}

// Transact invokes the (paid) contract method with params as input values.
func (_IAuction *IAuctionTransactorRaw) Transact(opts *bind.TransactOpts, method string, params ...interface{}) (*types.Transaction, error) {
	return _IAuction.Contract.contract.Transact(opts, method, params...)
}

// DeclareWinner is a paid mutator transaction binding the contract method 0x9083d3fa.
//
// Solidity: function declareWinner(address _auctionAdress, address _winner) returns()
func (_IAuction *IAuctionTransactor) DeclareWinner(opts *bind.TransactOpts, _auctionAdress common.Address, _winner common.Address) (*types.Transaction, error) {
	return _IAuction.contract.Transact(opts, "declareWinner", _auctionAdress, _winner)
}

// DeclareWinner is a paid mutator transaction binding the contract method 0x9083d3fa.
//
// Solidity: function declareWinner(address _auctionAdress, address _winner) returns()
func (_IAuction *IAuctionSession) DeclareWinner(_auctionAdress common.Address, _winner common.Address) (*types.Transaction, error) {
	return _IAuction.Contract.DeclareWinner(&_IAuction.TransactOpts, _auctionAdress, _winner)
}

// DeclareWinner is a paid mutator transaction binding the contract method 0x9083d3fa.
//
// Solidity: function declareWinner(address _auctionAdress, address _winner) returns()
func (_IAuction *IAuctionTransactorSession) DeclareWinner(_auctionAdress common.Address, _winner common.Address) (*types.Transaction, error) {
	return _IAuction.Contract.DeclareWinner(&_IAuction.TransactOpts, _auctionAdress, _winner)
}

// UpdateNonce is a paid mutator transaction binding the contract method 0x441344af.
//
// Solidity: function updateNonce(address _auctionAddress, uint256 _auctionNonce) returns()
func (_IAuction *IAuctionTransactor) UpdateNonce(opts *bind.TransactOpts, _auctionAddress common.Address, _auctionNonce *big.Int) (*types.Transaction, error) {
	return _IAuction.contract.Transact(opts, "updateNonce", _auctionAddress, _auctionNonce)
}

// UpdateNonce is a paid mutator transaction binding the contract method 0x441344af.
//
// Solidity: function updateNonce(address _auctionAddress, uint256 _auctionNonce) returns()
func (_IAuction *IAuctionSession) UpdateNonce(_auctionAddress common.Address, _auctionNonce *big.Int) (*types.Transaction, error) {
	return _IAuction.Contract.UpdateNonce(&_IAuction.TransactOpts, _auctionAddress, _auctionNonce)
}

// UpdateNonce is a paid mutator transaction binding the contract method 0x441344af.
//
// Solidity: function updateNonce(address _auctionAddress, uint256 _auctionNonce) returns()
func (_IAuction *IAuctionTransactorSession) UpdateNonce(_auctionAddress common.Address, _auctionNonce *big.Int) (*types.Transaction, error) {
	return _IAuction.Contract.UpdateNonce(&_IAuction.TransactOpts, _auctionAddress, _auctionNonce)
}
