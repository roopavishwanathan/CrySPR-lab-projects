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

// AuctionMetaData contains all meta data concerning the Auction contract.
var AuctionMetaData = &bind.MetaData{
	ABI: "[{\"inputs\":[],\"name\":\"ADMIN\",\"outputs\":[{\"internalType\":\"address\",\"name\":\"\",\"type\":\"address\"}],\"stateMutability\":\"view\",\"type\":\"function\"},{\"inputs\":[],\"name\":\"CLOUD_ADDRESS\",\"outputs\":[{\"internalType\":\"address\",\"name\":\"\",\"type\":\"address\"}],\"stateMutability\":\"view\",\"type\":\"function\"},{\"inputs\":[],\"name\":\"MANAGER_ADDRESS\",\"outputs\":[{\"internalType\":\"address\",\"name\":\"\",\"type\":\"address\"}],\"stateMutability\":\"view\",\"type\":\"function\"},{\"inputs\":[{\"internalType\":\"uint256\",\"name\":\"_auctionStartTime\",\"type\":\"uint256\"},{\"internalType\":\"uint256\",\"name\":\"_auctionEndTime\",\"type\":\"uint256\"}],\"name\":\"auctioneerRegister\",\"outputs\":[],\"stateMutability\":\"payable\",\"type\":\"function\"},{\"inputs\":[{\"internalType\":\"address\",\"name\":\"\",\"type\":\"address\"}],\"name\":\"auctions\",\"outputs\":[{\"internalType\":\"uint256\",\"name\":\"paymentOffered\",\"type\":\"uint256\"},{\"internalType\":\"uint256\",\"name\":\"auctionNonce\",\"type\":\"uint256\"},{\"internalType\":\"bool\",\"name\":\"isValid\",\"type\":\"bool\"},{\"internalType\":\"address\",\"name\":\"winner\",\"type\":\"address\"},{\"internalType\":\"uint256\",\"name\":\"auctionStartTime\",\"type\":\"uint256\"},{\"internalType\":\"uint256\",\"name\":\"auctionEndTime\",\"type\":\"uint256\"}],\"stateMutability\":\"view\",\"type\":\"function\"},{\"inputs\":[{\"internalType\":\"address\",\"name\":\"_auctionAddress\",\"type\":\"address\"},{\"internalType\":\"address\",\"name\":\"_winner\",\"type\":\"address\"}],\"name\":\"declareWinner\",\"outputs\":[],\"stateMutability\":\"nonpayable\",\"type\":\"function\"},{\"inputs\":[{\"internalType\":\"address\",\"name\":\"_auctionAddress\",\"type\":\"address\"},{\"internalType\":\"string\",\"name\":\"_newBid\",\"type\":\"string\"}],\"name\":\"newBid\",\"outputs\":[],\"stateMutability\":\"nonpayable\",\"type\":\"function\"},{\"inputs\":[],\"name\":\"pk\",\"outputs\":[{\"internalType\":\"bytes32\",\"name\":\"\",\"type\":\"bytes32\"}],\"stateMutability\":\"view\",\"type\":\"function\"},{\"inputs\":[{\"internalType\":\"address\",\"name\":\"_auctionAddress\",\"type\":\"address\"}],\"name\":\"resetAuction\",\"outputs\":[],\"stateMutability\":\"nonpayable\",\"type\":\"function\"},{\"inputs\":[{\"internalType\":\"address\",\"name\":\"index\",\"type\":\"address\"}],\"name\":\"returnAuctionDetails\",\"outputs\":[{\"internalType\":\"uint256\",\"name\":\"\",\"type\":\"uint256\"}],\"stateMutability\":\"view\",\"type\":\"function\"},{\"inputs\":[],\"name\":\"returnBidders\",\"outputs\":[{\"internalType\":\"address[]\",\"name\":\"array\",\"type\":\"address[]\"}],\"stateMutability\":\"view\",\"type\":\"function\"},{\"inputs\":[{\"internalType\":\"address\",\"name\":\"_auctionAddress\",\"type\":\"address\"}],\"name\":\"returnEncryptedBids\",\"outputs\":[{\"internalType\":\"string[]\",\"name\":\"array\",\"type\":\"string[]\"}],\"stateMutability\":\"view\",\"type\":\"function\"},{\"inputs\":[{\"internalType\":\"address\",\"name\":\"_auctionAddress\",\"type\":\"address\"},{\"internalType\":\"uint256\",\"name\":\"_auctionNonce\",\"type\":\"uint256\"}],\"name\":\"updateNonce\",\"outputs\":[],\"stateMutability\":\"nonpayable\",\"type\":\"function\"},{\"inputs\":[{\"internalType\":\"bytes32\",\"name\":\"_pk\",\"type\":\"bytes32\"}],\"name\":\"update_pk\",\"outputs\":[],\"stateMutability\":\"nonpayable\",\"type\":\"function\"}]",
}

// AuctionABI is the input ABI used to generate the binding from.
// Deprecated: Use AuctionMetaData.ABI instead.
var AuctionABI = AuctionMetaData.ABI

// Auction is an auto generated Go binding around an Ethereum contract.
type Auction struct {
	AuctionCaller     // Read-only binding to the contract
	AuctionTransactor // Write-only binding to the contract
	AuctionFilterer   // Log filterer for contract events
}

// AuctionCaller is an auto generated read-only Go binding around an Ethereum contract.
type AuctionCaller struct {
	contract *bind.BoundContract // Generic contract wrapper for the low level calls
}

// AuctionTransactor is an auto generated write-only Go binding around an Ethereum contract.
type AuctionTransactor struct {
	contract *bind.BoundContract // Generic contract wrapper for the low level calls
}

// AuctionFilterer is an auto generated log filtering Go binding around an Ethereum contract events.
type AuctionFilterer struct {
	contract *bind.BoundContract // Generic contract wrapper for the low level calls
}

// AuctionSession is an auto generated Go binding around an Ethereum contract,
// with pre-set call and transact options.
type AuctionSession struct {
	Contract     *Auction          // Generic contract binding to set the session for
	CallOpts     bind.CallOpts     // Call options to use throughout this session
	TransactOpts bind.TransactOpts // Transaction auth options to use throughout this session
}

// AuctionCallerSession is an auto generated read-only Go binding around an Ethereum contract,
// with pre-set call options.
type AuctionCallerSession struct {
	Contract *AuctionCaller // Generic contract caller binding to set the session for
	CallOpts bind.CallOpts  // Call options to use throughout this session
}

// AuctionTransactorSession is an auto generated write-only Go binding around an Ethereum contract,
// with pre-set transact options.
type AuctionTransactorSession struct {
	Contract     *AuctionTransactor // Generic contract transactor binding to set the session for
	TransactOpts bind.TransactOpts  // Transaction auth options to use throughout this session
}

// AuctionRaw is an auto generated low-level Go binding around an Ethereum contract.
type AuctionRaw struct {
	Contract *Auction // Generic contract binding to access the raw methods on
}

// AuctionCallerRaw is an auto generated low-level read-only Go binding around an Ethereum contract.
type AuctionCallerRaw struct {
	Contract *AuctionCaller // Generic read-only contract binding to access the raw methods on
}

// AuctionTransactorRaw is an auto generated low-level write-only Go binding around an Ethereum contract.
type AuctionTransactorRaw struct {
	Contract *AuctionTransactor // Generic write-only contract binding to access the raw methods on
}

// NewAuction creates a new instance of Auction, bound to a specific deployed contract.
func NewAuction(address common.Address, backend bind.ContractBackend) (*Auction, error) {
	contract, err := bindAuction(address, backend, backend, backend)
	if err != nil {
		return nil, err
	}
	return &Auction{AuctionCaller: AuctionCaller{contract: contract}, AuctionTransactor: AuctionTransactor{contract: contract}, AuctionFilterer: AuctionFilterer{contract: contract}}, nil
}

// NewAuctionCaller creates a new read-only instance of Auction, bound to a specific deployed contract.
func NewAuctionCaller(address common.Address, caller bind.ContractCaller) (*AuctionCaller, error) {
	contract, err := bindAuction(address, caller, nil, nil)
	if err != nil {
		return nil, err
	}
	return &AuctionCaller{contract: contract}, nil
}

// NewAuctionTransactor creates a new write-only instance of Auction, bound to a specific deployed contract.
func NewAuctionTransactor(address common.Address, transactor bind.ContractTransactor) (*AuctionTransactor, error) {
	contract, err := bindAuction(address, nil, transactor, nil)
	if err != nil {
		return nil, err
	}
	return &AuctionTransactor{contract: contract}, nil
}

// NewAuctionFilterer creates a new log filterer instance of Auction, bound to a specific deployed contract.
func NewAuctionFilterer(address common.Address, filterer bind.ContractFilterer) (*AuctionFilterer, error) {
	contract, err := bindAuction(address, nil, nil, filterer)
	if err != nil {
		return nil, err
	}
	return &AuctionFilterer{contract: contract}, nil
}

// bindAuction binds a generic wrapper to an already deployed contract.
func bindAuction(address common.Address, caller bind.ContractCaller, transactor bind.ContractTransactor, filterer bind.ContractFilterer) (*bind.BoundContract, error) {
	parsed, err := abi.JSON(strings.NewReader(AuctionABI))
	if err != nil {
		return nil, err
	}
	return bind.NewBoundContract(address, parsed, caller, transactor, filterer), nil
}

// Call invokes the (constant) contract method with params as input values and
// sets the output to result. The result type might be a single field for simple
// returns, a slice of interfaces for anonymous returns and a struct for named
// returns.
func (_Auction *AuctionRaw) Call(opts *bind.CallOpts, result *[]interface{}, method string, params ...interface{}) error {
	return _Auction.Contract.AuctionCaller.contract.Call(opts, result, method, params...)
}

// Transfer initiates a plain transaction to move funds to the contract, calling
// its default method if one is available.
func (_Auction *AuctionRaw) Transfer(opts *bind.TransactOpts) (*types.Transaction, error) {
	return _Auction.Contract.AuctionTransactor.contract.Transfer(opts)
}

// Transact invokes the (paid) contract method with params as input values.
func (_Auction *AuctionRaw) Transact(opts *bind.TransactOpts, method string, params ...interface{}) (*types.Transaction, error) {
	return _Auction.Contract.AuctionTransactor.contract.Transact(opts, method, params...)
}

// Call invokes the (constant) contract method with params as input values and
// sets the output to result. The result type might be a single field for simple
// returns, a slice of interfaces for anonymous returns and a struct for named
// returns.
func (_Auction *AuctionCallerRaw) Call(opts *bind.CallOpts, result *[]interface{}, method string, params ...interface{}) error {
	return _Auction.Contract.contract.Call(opts, result, method, params...)
}

// Transfer initiates a plain transaction to move funds to the contract, calling
// its default method if one is available.
func (_Auction *AuctionTransactorRaw) Transfer(opts *bind.TransactOpts) (*types.Transaction, error) {
	return _Auction.Contract.contract.Transfer(opts)
}

// Transact invokes the (paid) contract method with params as input values.
func (_Auction *AuctionTransactorRaw) Transact(opts *bind.TransactOpts, method string, params ...interface{}) (*types.Transaction, error) {
	return _Auction.Contract.contract.Transact(opts, method, params...)
}

// ADMIN is a free data retrieval call binding the contract method 0x2a0acc6a.
//
// Solidity: function ADMIN() view returns(address)
func (_Auction *AuctionCaller) ADMIN(opts *bind.CallOpts) (common.Address, error) {
	var out []interface{}
	err := _Auction.contract.Call(opts, &out, "ADMIN")

	if err != nil {
		return *new(common.Address), err
	}

	out0 := *abi.ConvertType(out[0], new(common.Address)).(*common.Address)

	return out0, err

}

// ADMIN is a free data retrieval call binding the contract method 0x2a0acc6a.
//
// Solidity: function ADMIN() view returns(address)
func (_Auction *AuctionSession) ADMIN() (common.Address, error) {
	return _Auction.Contract.ADMIN(&_Auction.CallOpts)
}

// ADMIN is a free data retrieval call binding the contract method 0x2a0acc6a.
//
// Solidity: function ADMIN() view returns(address)
func (_Auction *AuctionCallerSession) ADMIN() (common.Address, error) {
	return _Auction.Contract.ADMIN(&_Auction.CallOpts)
}

// CLOUDADDRESS is a free data retrieval call binding the contract method 0x2710167f.
//
// Solidity: function CLOUD_ADDRESS() view returns(address)
func (_Auction *AuctionCaller) CLOUDADDRESS(opts *bind.CallOpts) (common.Address, error) {
	var out []interface{}
	err := _Auction.contract.Call(opts, &out, "CLOUD_ADDRESS")

	if err != nil {
		return *new(common.Address), err
	}

	out0 := *abi.ConvertType(out[0], new(common.Address)).(*common.Address)

	return out0, err

}

// CLOUDADDRESS is a free data retrieval call binding the contract method 0x2710167f.
//
// Solidity: function CLOUD_ADDRESS() view returns(address)
func (_Auction *AuctionSession) CLOUDADDRESS() (common.Address, error) {
	return _Auction.Contract.CLOUDADDRESS(&_Auction.CallOpts)
}

// CLOUDADDRESS is a free data retrieval call binding the contract method 0x2710167f.
//
// Solidity: function CLOUD_ADDRESS() view returns(address)
func (_Auction *AuctionCallerSession) CLOUDADDRESS() (common.Address, error) {
	return _Auction.Contract.CLOUDADDRESS(&_Auction.CallOpts)
}

// MANAGERADDRESS is a free data retrieval call binding the contract method 0x380d4244.
//
// Solidity: function MANAGER_ADDRESS() view returns(address)
func (_Auction *AuctionCaller) MANAGERADDRESS(opts *bind.CallOpts) (common.Address, error) {
	var out []interface{}
	err := _Auction.contract.Call(opts, &out, "MANAGER_ADDRESS")

	if err != nil {
		return *new(common.Address), err
	}

	out0 := *abi.ConvertType(out[0], new(common.Address)).(*common.Address)

	return out0, err

}

// MANAGERADDRESS is a free data retrieval call binding the contract method 0x380d4244.
//
// Solidity: function MANAGER_ADDRESS() view returns(address)
func (_Auction *AuctionSession) MANAGERADDRESS() (common.Address, error) {
	return _Auction.Contract.MANAGERADDRESS(&_Auction.CallOpts)
}

// MANAGERADDRESS is a free data retrieval call binding the contract method 0x380d4244.
//
// Solidity: function MANAGER_ADDRESS() view returns(address)
func (_Auction *AuctionCallerSession) MANAGERADDRESS() (common.Address, error) {
	return _Auction.Contract.MANAGERADDRESS(&_Auction.CallOpts)
}

// Auctions is a free data retrieval call binding the contract method 0x1d59410a.
//
// Solidity: function auctions(address ) view returns(uint256 paymentOffered, uint256 auctionNonce, bool isValid, address winner, uint256 auctionStartTime, uint256 auctionEndTime)
func (_Auction *AuctionCaller) Auctions(opts *bind.CallOpts, arg0 common.Address) (struct {
	PaymentOffered   *big.Int
	AuctionNonce     *big.Int
	IsValid          bool
	Winner           common.Address
	AuctionStartTime *big.Int
	AuctionEndTime   *big.Int
}, error) {
	var out []interface{}
	err := _Auction.contract.Call(opts, &out, "auctions", arg0)

	outstruct := new(struct {
		PaymentOffered   *big.Int
		AuctionNonce     *big.Int
		IsValid          bool
		Winner           common.Address
		AuctionStartTime *big.Int
		AuctionEndTime   *big.Int
	})
	if err != nil {
		return *outstruct, err
	}

	outstruct.PaymentOffered = *abi.ConvertType(out[0], new(*big.Int)).(**big.Int)
	outstruct.AuctionNonce = *abi.ConvertType(out[1], new(*big.Int)).(**big.Int)
	outstruct.IsValid = *abi.ConvertType(out[2], new(bool)).(*bool)
	outstruct.Winner = *abi.ConvertType(out[3], new(common.Address)).(*common.Address)
	outstruct.AuctionStartTime = *abi.ConvertType(out[4], new(*big.Int)).(**big.Int)
	outstruct.AuctionEndTime = *abi.ConvertType(out[5], new(*big.Int)).(**big.Int)

	return *outstruct, err

}

// Auctions is a free data retrieval call binding the contract method 0x1d59410a.
//
// Solidity: function auctions(address ) view returns(uint256 paymentOffered, uint256 auctionNonce, bool isValid, address winner, uint256 auctionStartTime, uint256 auctionEndTime)
func (_Auction *AuctionSession) Auctions(arg0 common.Address) (struct {
	PaymentOffered   *big.Int
	AuctionNonce     *big.Int
	IsValid          bool
	Winner           common.Address
	AuctionStartTime *big.Int
	AuctionEndTime   *big.Int
}, error) {
	return _Auction.Contract.Auctions(&_Auction.CallOpts, arg0)
}

// Auctions is a free data retrieval call binding the contract method 0x1d59410a.
//
// Solidity: function auctions(address ) view returns(uint256 paymentOffered, uint256 auctionNonce, bool isValid, address winner, uint256 auctionStartTime, uint256 auctionEndTime)
func (_Auction *AuctionCallerSession) Auctions(arg0 common.Address) (struct {
	PaymentOffered   *big.Int
	AuctionNonce     *big.Int
	IsValid          bool
	Winner           common.Address
	AuctionStartTime *big.Int
	AuctionEndTime   *big.Int
}, error) {
	return _Auction.Contract.Auctions(&_Auction.CallOpts, arg0)
}

// Pk is a free data retrieval call binding the contract method 0x58e14a45.
//
// Solidity: function pk() view returns(bytes32)
func (_Auction *AuctionCaller) Pk(opts *bind.CallOpts) ([32]byte, error) {
	var out []interface{}
	err := _Auction.contract.Call(opts, &out, "pk")

	if err != nil {
		return *new([32]byte), err
	}

	out0 := *abi.ConvertType(out[0], new([32]byte)).(*[32]byte)

	return out0, err

}

// Pk is a free data retrieval call binding the contract method 0x58e14a45.
//
// Solidity: function pk() view returns(bytes32)
func (_Auction *AuctionSession) Pk() ([32]byte, error) {
	return _Auction.Contract.Pk(&_Auction.CallOpts)
}

// Pk is a free data retrieval call binding the contract method 0x58e14a45.
//
// Solidity: function pk() view returns(bytes32)
func (_Auction *AuctionCallerSession) Pk() ([32]byte, error) {
	return _Auction.Contract.Pk(&_Auction.CallOpts)
}

// ReturnAuctionDetails is a free data retrieval call binding the contract method 0x3264adf7.
//
// Solidity: function returnAuctionDetails(address index) view returns(uint256)
func (_Auction *AuctionCaller) ReturnAuctionDetails(opts *bind.CallOpts, index common.Address) (*big.Int, error) {
	var out []interface{}
	err := _Auction.contract.Call(opts, &out, "returnAuctionDetails", index)

	if err != nil {
		return *new(*big.Int), err
	}

	out0 := *abi.ConvertType(out[0], new(*big.Int)).(**big.Int)

	return out0, err

}

// ReturnAuctionDetails is a free data retrieval call binding the contract method 0x3264adf7.
//
// Solidity: function returnAuctionDetails(address index) view returns(uint256)
func (_Auction *AuctionSession) ReturnAuctionDetails(index common.Address) (*big.Int, error) {
	return _Auction.Contract.ReturnAuctionDetails(&_Auction.CallOpts, index)
}

// ReturnAuctionDetails is a free data retrieval call binding the contract method 0x3264adf7.
//
// Solidity: function returnAuctionDetails(address index) view returns(uint256)
func (_Auction *AuctionCallerSession) ReturnAuctionDetails(index common.Address) (*big.Int, error) {
	return _Auction.Contract.ReturnAuctionDetails(&_Auction.CallOpts, index)
}

// ReturnBidders is a free data retrieval call binding the contract method 0xee740771.
//
// Solidity: function returnBidders() view returns(address[] array)
func (_Auction *AuctionCaller) ReturnBidders(opts *bind.CallOpts) ([]common.Address, error) {
	var out []interface{}
	err := _Auction.contract.Call(opts, &out, "returnBidders")

	if err != nil {
		return *new([]common.Address), err
	}

	out0 := *abi.ConvertType(out[0], new([]common.Address)).(*[]common.Address)

	return out0, err

}

// ReturnBidders is a free data retrieval call binding the contract method 0xee740771.
//
// Solidity: function returnBidders() view returns(address[] array)
func (_Auction *AuctionSession) ReturnBidders() ([]common.Address, error) {
	return _Auction.Contract.ReturnBidders(&_Auction.CallOpts)
}

// ReturnBidders is a free data retrieval call binding the contract method 0xee740771.
//
// Solidity: function returnBidders() view returns(address[] array)
func (_Auction *AuctionCallerSession) ReturnBidders() ([]common.Address, error) {
	return _Auction.Contract.ReturnBidders(&_Auction.CallOpts)
}

// ReturnEncryptedBids is a free data retrieval call binding the contract method 0xabd1d930.
//
// Solidity: function returnEncryptedBids(address _auctionAddress) view returns(string[] array)
func (_Auction *AuctionCaller) ReturnEncryptedBids(opts *bind.CallOpts, _auctionAddress common.Address) ([]string, error) {
	var out []interface{}
	err := _Auction.contract.Call(opts, &out, "returnEncryptedBids", _auctionAddress)

	if err != nil {
		return *new([]string), err
	}

	out0 := *abi.ConvertType(out[0], new([]string)).(*[]string)

	return out0, err

}

// ReturnEncryptedBids is a free data retrieval call binding the contract method 0xabd1d930.
//
// Solidity: function returnEncryptedBids(address _auctionAddress) view returns(string[] array)
func (_Auction *AuctionSession) ReturnEncryptedBids(_auctionAddress common.Address) ([]string, error) {
	return _Auction.Contract.ReturnEncryptedBids(&_Auction.CallOpts, _auctionAddress)
}

// ReturnEncryptedBids is a free data retrieval call binding the contract method 0xabd1d930.
//
// Solidity: function returnEncryptedBids(address _auctionAddress) view returns(string[] array)
func (_Auction *AuctionCallerSession) ReturnEncryptedBids(_auctionAddress common.Address) ([]string, error) {
	return _Auction.Contract.ReturnEncryptedBids(&_Auction.CallOpts, _auctionAddress)
}

// AuctioneerRegister is a paid mutator transaction binding the contract method 0x2f6dbd4e.
//
// Solidity: function auctioneerRegister(uint256 _auctionStartTime, uint256 _auctionEndTime) payable returns()
func (_Auction *AuctionTransactor) AuctioneerRegister(opts *bind.TransactOpts, _auctionStartTime *big.Int, _auctionEndTime *big.Int) (*types.Transaction, error) {
	return _Auction.contract.Transact(opts, "auctioneerRegister", _auctionStartTime, _auctionEndTime)
}

// AuctioneerRegister is a paid mutator transaction binding the contract method 0x2f6dbd4e.
//
// Solidity: function auctioneerRegister(uint256 _auctionStartTime, uint256 _auctionEndTime) payable returns()
func (_Auction *AuctionSession) AuctioneerRegister(_auctionStartTime *big.Int, _auctionEndTime *big.Int) (*types.Transaction, error) {
	return _Auction.Contract.AuctioneerRegister(&_Auction.TransactOpts, _auctionStartTime, _auctionEndTime)
}

// AuctioneerRegister is a paid mutator transaction binding the contract method 0x2f6dbd4e.
//
// Solidity: function auctioneerRegister(uint256 _auctionStartTime, uint256 _auctionEndTime) payable returns()
func (_Auction *AuctionTransactorSession) AuctioneerRegister(_auctionStartTime *big.Int, _auctionEndTime *big.Int) (*types.Transaction, error) {
	return _Auction.Contract.AuctioneerRegister(&_Auction.TransactOpts, _auctionStartTime, _auctionEndTime)
}

// DeclareWinner is a paid mutator transaction binding the contract method 0x9083d3fa.
//
// Solidity: function declareWinner(address _auctionAddress, address _winner) returns()
func (_Auction *AuctionTransactor) DeclareWinner(opts *bind.TransactOpts, _auctionAddress common.Address, _winner common.Address) (*types.Transaction, error) {
	return _Auction.contract.Transact(opts, "declareWinner", _auctionAddress, _winner)
}

// DeclareWinner is a paid mutator transaction binding the contract method 0x9083d3fa.
//
// Solidity: function declareWinner(address _auctionAddress, address _winner) returns()
func (_Auction *AuctionSession) DeclareWinner(_auctionAddress common.Address, _winner common.Address) (*types.Transaction, error) {
	return _Auction.Contract.DeclareWinner(&_Auction.TransactOpts, _auctionAddress, _winner)
}

// DeclareWinner is a paid mutator transaction binding the contract method 0x9083d3fa.
//
// Solidity: function declareWinner(address _auctionAddress, address _winner) returns()
func (_Auction *AuctionTransactorSession) DeclareWinner(_auctionAddress common.Address, _winner common.Address) (*types.Transaction, error) {
	return _Auction.Contract.DeclareWinner(&_Auction.TransactOpts, _auctionAddress, _winner)
}

// NewBid is a paid mutator transaction binding the contract method 0x23a98c4f.
//
// Solidity: function newBid(address _auctionAddress, string _newBid) returns()
func (_Auction *AuctionTransactor) NewBid(opts *bind.TransactOpts, _auctionAddress common.Address, _newBid string) (*types.Transaction, error) {
	return _Auction.contract.Transact(opts, "newBid", _auctionAddress, _newBid)
}

// NewBid is a paid mutator transaction binding the contract method 0x23a98c4f.
//
// Solidity: function newBid(address _auctionAddress, string _newBid) returns()
func (_Auction *AuctionSession) NewBid(_auctionAddress common.Address, _newBid string) (*types.Transaction, error) {
	return _Auction.Contract.NewBid(&_Auction.TransactOpts, _auctionAddress, _newBid)
}

// NewBid is a paid mutator transaction binding the contract method 0x23a98c4f.
//
// Solidity: function newBid(address _auctionAddress, string _newBid) returns()
func (_Auction *AuctionTransactorSession) NewBid(_auctionAddress common.Address, _newBid string) (*types.Transaction, error) {
	return _Auction.Contract.NewBid(&_Auction.TransactOpts, _auctionAddress, _newBid)
}

// ResetAuction is a paid mutator transaction binding the contract method 0xa23a3759.
//
// Solidity: function resetAuction(address _auctionAddress) returns()
func (_Auction *AuctionTransactor) ResetAuction(opts *bind.TransactOpts, _auctionAddress common.Address) (*types.Transaction, error) {
	return _Auction.contract.Transact(opts, "resetAuction", _auctionAddress)
}

// ResetAuction is a paid mutator transaction binding the contract method 0xa23a3759.
//
// Solidity: function resetAuction(address _auctionAddress) returns()
func (_Auction *AuctionSession) ResetAuction(_auctionAddress common.Address) (*types.Transaction, error) {
	return _Auction.Contract.ResetAuction(&_Auction.TransactOpts, _auctionAddress)
}

// ResetAuction is a paid mutator transaction binding the contract method 0xa23a3759.
//
// Solidity: function resetAuction(address _auctionAddress) returns()
func (_Auction *AuctionTransactorSession) ResetAuction(_auctionAddress common.Address) (*types.Transaction, error) {
	return _Auction.Contract.ResetAuction(&_Auction.TransactOpts, _auctionAddress)
}

// UpdateNonce is a paid mutator transaction binding the contract method 0x441344af.
//
// Solidity: function updateNonce(address _auctionAddress, uint256 _auctionNonce) returns()
func (_Auction *AuctionTransactor) UpdateNonce(opts *bind.TransactOpts, _auctionAddress common.Address, _auctionNonce *big.Int) (*types.Transaction, error) {
	return _Auction.contract.Transact(opts, "updateNonce", _auctionAddress, _auctionNonce)
}

// UpdateNonce is a paid mutator transaction binding the contract method 0x441344af.
//
// Solidity: function updateNonce(address _auctionAddress, uint256 _auctionNonce) returns()
func (_Auction *AuctionSession) UpdateNonce(_auctionAddress common.Address, _auctionNonce *big.Int) (*types.Transaction, error) {
	return _Auction.Contract.UpdateNonce(&_Auction.TransactOpts, _auctionAddress, _auctionNonce)
}

// UpdateNonce is a paid mutator transaction binding the contract method 0x441344af.
//
// Solidity: function updateNonce(address _auctionAddress, uint256 _auctionNonce) returns()
func (_Auction *AuctionTransactorSession) UpdateNonce(_auctionAddress common.Address, _auctionNonce *big.Int) (*types.Transaction, error) {
	return _Auction.Contract.UpdateNonce(&_Auction.TransactOpts, _auctionAddress, _auctionNonce)
}

// UpdatePk is a paid mutator transaction binding the contract method 0xae83b093.
//
// Solidity: function update_pk(bytes32 _pk) returns()
func (_Auction *AuctionTransactor) UpdatePk(opts *bind.TransactOpts, _pk [32]byte) (*types.Transaction, error) {
	return _Auction.contract.Transact(opts, "update_pk", _pk)
}

// UpdatePk is a paid mutator transaction binding the contract method 0xae83b093.
//
// Solidity: function update_pk(bytes32 _pk) returns()
func (_Auction *AuctionSession) UpdatePk(_pk [32]byte) (*types.Transaction, error) {
	return _Auction.Contract.UpdatePk(&_Auction.TransactOpts, _pk)
}

// UpdatePk is a paid mutator transaction binding the contract method 0xae83b093.
//
// Solidity: function update_pk(bytes32 _pk) returns()
func (_Auction *AuctionTransactorSession) UpdatePk(_pk [32]byte) (*types.Transaction, error) {
	return _Auction.Contract.UpdatePk(&_Auction.TransactOpts, _pk)
}
