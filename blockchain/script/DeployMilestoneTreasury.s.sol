// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Script} from "forge-std/Script.sol";
import {console} from "forge-std/console.sol";
import {MilestoneTreasury} from "../src/MilestoneTreasury.sol";

/**
 * @title DeployMilestoneTreasury
 * @dev Foundry deployment script for MilestoneTreasury
 *
 * Deploy to Base Sepolia (testnet) — Etherscan V2 API (Chain ID: 84532):
 * cd blockchain && source ../.env && forge script script/DeployMilestoneTreasury.s.sol:DeployMilestoneTreasury \
 *   --rpc-url $BASE_SEPOLIA_RPC_URL \
 *   --private-key $PRIVATE_KEY_SEP \
 *   --broadcast \
 *   --verify \
 *   --verifier-url "https://api.etherscan.io/v2/api?chainid=84532" \
 *   --etherscan-api-key $ETHERSCAN_API_KEY \
 *   --via-ir
 */
contract DeployMilestoneTreasury is Script {
    function run() external {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY_SEP");

        vm.startBroadcast(deployerPrivateKey);

        MilestoneTreasury treasury = new MilestoneTreasury();

        console.log("MilestoneTreasury deployed to:", address(treasury));
        console.log("Owner:", treasury.owner());

        vm.stopBroadcast();

        console.log("\n=== DEPLOYMENT SUCCESSFUL ===");
        console.log("Add this to your .env file:");
        console.log("MILESTONE_TREASURY_CONTRACT=%s", address(treasury));
        console.log("\nVerify on BaseScan:");
        console.log("https://sepolia.basescan.org/address/%s", address(treasury));
    }
}
