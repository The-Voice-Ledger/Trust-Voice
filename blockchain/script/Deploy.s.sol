// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Script} from "forge-std/Script.sol";
import {console} from "forge-std/console.sol";
import {TaxReceiptNFT} from "../src/TaxReceiptNFT.sol";

/**
 * @title DeployScript
 * @dev Foundry deployment script for TaxReceiptNFT
 * 
 * Usage:
 * 
 * Deploy to Base Sepolia (testnet) - Etherscan V2 API (Chain ID: 84532):
 * forge script script/Deploy.s.sol:DeployScript \
 *   --rpc-url $BASE_SEPOLIA_RPC_URL \
 *   --private-key $PRIVATE_KEY_SEP \
 *   --broadcast \
 *   --verify \
 *   --verifier-url "https://api.etherscan.io/v2/api?chainid=84532" \
 *   --etherscan-api-key $ETHERSCAN_API_KEY \
 *   --via-ir
 * 
 * Deploy to Base Mainnet (Chain ID: 8453):
 * forge script script/Deploy.s.sol:DeployScript \
 *   --rpc-url $BASE_RPC_URL \
 *   --private-key $PRIVATE_KEY_SEP \
 *   --broadcast \
 *   --verify \
 *   --verifier-url "https://api.etherscan.io/v2/api?chainid=8453" \
 *   --etherscan-api-key $ETHERSCAN_API_KEY \
 *   --via-ir
 * 
 * Deploy to Polygon Amoy (testnet - Chain ID: 80002):
 * forge script script/Deploy.s.sol:DeployScript \
 *   --rpc-url $POLYGON_AMOY_RPC_URL \
 *   --private-key $PRIVATE_KEY_SEP \
 *   --broadcast \
 *   --verify \
 *   --verifier-url "https://api.etherscan.io/v2/api?chainid=80002" \
 *   --etherscan-api-key $ETHERSCAN_API_KEY \
 *   --via-ir
 */
contract DeployScript is Script {
    function run() external {
        // Get deployer private key from environment
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY_SEP");
        
        // Start broadcasting transactions
        vm.startBroadcast(deployerPrivateKey);
        
        // Deploy TaxReceiptNFT contract
        TaxReceiptNFT taxReceipt = new TaxReceiptNFT();
        
        console.log("TaxReceiptNFT deployed to:", address(taxReceipt));
        console.log("Owner:", taxReceipt.owner());
        console.log("Total supply:", taxReceipt.totalSupply());
        
        vm.stopBroadcast();
        
        // Log deployment info for easy copy-paste
        console.log("\n=== DEPLOYMENT SUCCESSFUL ===");
        console.log("Add this to your .env file:");
        console.log("BASE_RECEIPT_CONTRACT=%s", address(taxReceipt));
        console.log("\nVerify on BaseScan:");
        console.log("https://sepolia.basescan.org/address/%s", address(taxReceipt));
    }
}
