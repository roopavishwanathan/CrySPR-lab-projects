pushd contract_scripts/
brownie run scripts/deploy_general.py --network sepolia
popd
export 
solc --abi contract_scripts/contracts/optimized_auction.sol -o build --overwrite
abigen --abi build/Auction.abi  --out pkg/solidity_wrapper/auction_contract_wrappers.go --type=Auction --pkg solidity_wrapper
abigen --abi build/Bidders.abi  --out pkg/solidity_wrapper/bidders_contract_wrappers.go --type=Bidder --pkg solidity_wrapper
abigen --abi build/IAuction.abi --out pkg/solidity_wrapper/interface.go --type=IAuction --pkg solidity_wrapper
# Manager address (Account 5): 0xa8d9645E2927fD08a776A120DBc9096B9Fa8Eeb5
export MANAGER_PRIVATE_KEY=a0b5efc679841c091c1e64e7aeb0c08a06f39ba81b6b7bb0f9c8331046257521

# Enclave address (Account 1): 0xAFdE38Bbd62946DcE61BE9c53c797d01d5Ce19F8
#export SGX_PRIVATE_KEY=d8182dce616e33743a1121989974d1a68f86909d07df69de8308a084e80af449

# Bidder1 address: 
export bidder_1=export PRIVATE_KEY=2b089947435becc6c3766bf3d3ae1ebc51a009d4033023fb751cceebfe621460