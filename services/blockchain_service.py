"""
Blockchain Service for Tax Receipt NFTs

Manages NFT-based tax receipts on blockchain for donation verification.
Supports multiple networks:
- Polygon (recommended): Low fees (~$0.01), fast, eco-friendly
- Base: Coinbase L2, US-friendly, cheap
- Ethereum: Most recognized but expensive
- Arbitrum: L2 with low fees

Smart Contract: ERC-721 tokens for donation receipts
"""

import os
import logging
import json
from typing import Dict, Optional, Any
from decimal import Decimal
from datetime import datetime

# Web3 imports
try:
    from web3 import Web3
    from web3.middleware import ExtraDataToPOAMiddleware
    from eth_account import Account
    WEB3_AVAILABLE = True
except ImportError:
    WEB3_AVAILABLE = False
    logging.warning("web3 not installed. Blockchain functionality disabled.")

logger = logging.getLogger(__name__)


class BlockchainService:
    """
    Service for minting and managing tax receipt NFTs on blockchain.
    
    Usage:
        from services.blockchain_service import blockchain_service
        
        # Mint receipt NFT
        result = blockchain_service.mint_receipt_nft(
            donor_wallet="0x123...",
            metadata_ipfs_hash="QmXxxx...",
            donation_id=12345
        )
        
        # Verify receipt
        is_valid = blockchain_service.verify_receipt(token_id=100)
    """
    
    def __init__(self, network: str = "polygon"):
        """
        Initialize blockchain service.
        
        Args:
            network: Blockchain network to use (polygon, base, ethereum, arbitrum)
        """
        if not WEB3_AVAILABLE:
            logger.warning("Web3 not available. Blockchain service disabled.")
            self.enabled = False
            return
        
        self.network = network.lower()
        self.enabled = True
        
        # RPC endpoints (using Alchemy or public RPCs)
        self.rpc_urls = {
            "ethereum": os.getenv("ETH_RPC_URL", "https://eth-mainnet.g.alchemy.com/v2/demo"),
            "polygon": os.getenv("POLYGON_RPC_URL", "https://polygon-mainnet.g.alchemy.com/v2/demo"),
            "base": os.getenv("BASE_RPC_URL", "https://mainnet.base.org"),
            "arbitrum": os.getenv("ARBITRUM_RPC_URL", "https://arb1.arbitrum.io/rpc"),
            # Testnets for development
            "polygon_mumbai": "https://rpc-mumbai.maticvigil.com",
            "base_goerli": "https://goerli.base.org",
        }
        
        # Initialize Web3
        rpc_url = self.rpc_urls.get(self.network)
        if not rpc_url:
            raise ValueError(f"Unsupported network: {self.network}")
        
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        
        # Add middleware for PoA chains (Polygon)
        if self.network in ["polygon", "polygon_mumbai"]:
            self.w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
        
        # Contract addresses (deployed once per network)
        self.contract_addresses = {
            "ethereum": os.getenv("ETH_RECEIPT_CONTRACT"),
            "polygon": os.getenv("POLYGON_RECEIPT_CONTRACT"),
            "base": os.getenv("BASE_RECEIPT_CONTRACT"),
            "arbitrum": os.getenv("ARBITRUM_RECEIPT_CONTRACT"),
            "polygon_mumbai": os.getenv("POLYGON_MUMBAI_RECEIPT_CONTRACT"),
        }
        
        self.contract_address = self.contract_addresses.get(self.network)
        
        # Private key for minting (only for backend, never expose!)
        self.private_key = os.getenv("BLOCKCHAIN_PRIVATE_KEY")
        if self.private_key:
            self.account = Account.from_key(self.private_key)
            logger.info(f"✅ Blockchain account loaded: {self.account.address}")
        else:
            self.account = None
            logger.warning("⚠️ BLOCKCHAIN_PRIVATE_KEY not set. NFT minting disabled.")
        
        # Load contract ABI
        self.contract_abi = self._load_contract_abi()
        
        # Initialize contract if address is available
        if self.contract_address and self.contract_abi:
            self.contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(self.contract_address),
                abi=self.contract_abi
            )
            logger.info(f"✅ Connected to {self.network} network")
        else:
            self.contract = None
            logger.warning(f"⚠️ Contract not configured for {self.network}")
    
    def _load_contract_abi(self) -> Optional[list]:
        """
        Load smart contract ABI from file.
        
        Returns:
            Contract ABI as list, or None if not found
        """
        abi_path = os.path.join(os.path.dirname(__file__), "..", "blockchain", "TaxReceiptNFT.json")
        
        try:
            with open(abi_path, "r") as f:
                contract_json = json.load(f)
                return contract_json.get("abi", [])
        except FileNotFoundError:
            logger.warning(f"Contract ABI not found at {abi_path}")
            # Return minimal ABI for testing
            return [
                {
                    "inputs": [
                        {"name": "donor", "type": "address"},
                        {"name": "donationId", "type": "uint256"},
                        {"name": "tokenURI", "type": "string"}
                    ],
                    "name": "mintReceipt",
                    "outputs": [{"name": "tokenId", "type": "uint256"}],
                    "stateMutability": "nonpayable",
                    "type": "function"
                },
                {
                    "inputs": [{"name": "tokenId", "type": "uint256"}],
                    "name": "ownerOf",
                    "outputs": [{"name": "owner", "type": "address"}],
                    "stateMutability": "view",
                    "type": "function"
                },
                {
                    "inputs": [{"name": "tokenId", "type": "uint256"}],
                    "name": "tokenURI",
                    "outputs": [{"name": "uri", "type": "string"}],
                    "stateMutability": "view",
                    "type": "function"
                }
            ]
    
    def mint_receipt_nft(
        self,
        donor_wallet: str,
        metadata_ipfs_hash: str,
        donation_id: int
    ) -> Dict[str, Any]:
        """
        Mint a tax receipt NFT to donor's wallet.
        
        Args:
            donor_wallet: Donor's blockchain address (0x...)
            metadata_ipfs_hash: IPFS hash of receipt metadata (QmXxxx...)
            donation_id: Database ID of the donation
        
        Returns:
            {
                "success": True,
                "tx_hash": "0xabc123...",
                "token_id": 12345,
                "explorer_url": "https://polygonscan.com/tx/0xabc123...",
                "opensea_url": "https://opensea.io/assets/matic/0xcontract/12345",
                "network": "polygon"
            }
        
        Raises:
            ValueError: If service not configured or parameters invalid
            Exception: If minting fails
        """
        if not self.enabled:
            raise ValueError("Blockchain service not available (web3 not installed)")
        
        if not self.contract:
            raise ValueError(f"Contract not configured for network: {self.network}")
        
        if not self.account:
            raise ValueError("Blockchain private key not configured")
        
        # Validate donor wallet address
        if not Web3.is_address(donor_wallet):
            raise ValueError(f"Invalid donor wallet address: {donor_wallet}")
        
        donor_wallet = Web3.to_checksum_address(donor_wallet)
        
        try:
            # Generate token URI (ipfs://QmXxxx...)
            token_uri = f"ipfs://{metadata_ipfs_hash}"
            
            # Build transaction
            nonce = self.w3.eth.get_transaction_count(self.account.address)
            
            # Estimate gas
            try:
                gas_estimate = self.contract.functions.mintReceipt(
                    donor_wallet,
                    donation_id,
                    token_uri
                ).estimate_gas({'from': self.account.address})
                gas_limit = int(gas_estimate * 1.2)  # Add 20% buffer
            except Exception as e:
                logger.warning(f"Gas estimation failed: {e}. Using default gas limit.")
                gas_limit = 200000
            
            # Get current gas price
            gas_price = self.w3.eth.gas_price
            
            # Build transaction
            tx = self.contract.functions.mintReceipt(
                donor_wallet,
                donation_id,
                token_uri
            ).build_transaction({
                'from': self.account.address,
                'nonce': nonce,
                'gas': gas_limit,
                'gasPrice': gas_price
            })
            
            # Sign transaction
            signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)
            
            # Send transaction
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            logger.info(f"⏳ NFT minting transaction sent: {tx_hash.hex()}")
            
            # Wait for confirmation (with timeout)
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
            
            if receipt['status'] != 1:
                raise Exception(f"Transaction failed: {tx_hash.hex()}")
            
            # Extract token ID from event logs
            token_id = self._extract_token_id_from_receipt(receipt)
            
            # Calculate gas cost
            gas_used = receipt['gasUsed']
            gas_cost_wei = gas_used * gas_price
            gas_cost_eth = self.w3.from_wei(gas_cost_wei, 'ether')
            
            result = {
                "success": True,
                "tx_hash": tx_hash.hex(),
                "token_id": token_id,
                "explorer_url": self._get_explorer_url(tx_hash.hex()),
                "opensea_url": self._get_opensea_url(token_id) if token_id else None,
                "network": self.network,
                "gas_used": gas_used,
                "gas_cost_eth": float(gas_cost_eth),
                "block_number": receipt['blockNumber']
            }
            
            logger.info(f"✅ NFT minted successfully: token_id={token_id}, tx={tx_hash.hex()}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to mint NFT: {e}")
            return {
                "success": False,
                "error": str(e),
                "network": self.network
            }
    
    def _extract_token_id_from_receipt(self, receipt: Dict) -> Optional[int]:
        """Extract token ID from transaction receipt event logs."""
        try:
            # Parse logs for ReceiptMinted event
            for log in receipt['logs']:
                try:
                    decoded = self.contract.events.ReceiptMinted().process_log(log)
                    return decoded['args']['tokenId']
                except:
                    continue
            
            # Fallback: try to extract from last log
            if receipt['logs']:
                last_log = receipt['logs'][-1]
                # Token ID is typically in the last topic or data field
                if len(last_log['topics']) > 3:
                    token_id = int(last_log['topics'][3].hex(), 16)
                    return token_id
            
            return None
            
        except Exception as e:
            logger.warning(f"Could not extract token ID from receipt: {e}")
            return None
    
    def verify_receipt(self, token_id: int) -> Dict[str, Any]:
        """
        Verify a receipt NFT exists and get its details.
        
        Args:
            token_id: NFT token ID to verify
        
        Returns:
            {
                "valid": True,
                "owner": "0x123...",
                "token_uri": "ipfs://QmXxxx...",
                "network": "polygon",
                "contract": "0xabc..."
            }
        
        Used by:
        - Donors to verify their receipt
        - Tax authorities to validate donations
        - Auditors for compliance checks
        """
        if not self.enabled or not self.contract:
            return {"valid": False, "error": "Blockchain service not available"}
        
        try:
            # Get owner
            owner = self.contract.functions.ownerOf(token_id).call()
            
            # Get metadata URI
            token_uri = self.contract.functions.tokenURI(token_id).call()
            
            return {
                "valid": True,
                "token_id": token_id,
                "owner": owner,
                "token_uri": token_uri,
                "network": self.network,
                "contract": self.contract_address,
                "explorer_url": self._get_token_explorer_url(token_id)
            }
            
        except Exception as e:
            logger.error(f"Failed to verify receipt NFT {token_id}: {e}")
            return {
                "valid": False,
                "error": str(e),
                "network": self.network
            }
    
    def _get_explorer_url(self, tx_hash: str) -> str:
        """Get block explorer URL for transaction."""
        explorers = {
            "ethereum": f"https://etherscan.io/tx/{tx_hash}",
            "polygon": f"https://polygonscan.com/tx/{tx_hash}",
            "base": f"https://basescan.org/tx/{tx_hash}",
            "arbitrum": f"https://arbiscan.io/tx/{tx_hash}",
            "polygon_mumbai": f"https://mumbai.polygonscan.com/tx/{tx_hash}",
        }
        return explorers.get(self.network, f"https://etherscan.io/tx/{tx_hash}")
    
    def _get_token_explorer_url(self, token_id: int) -> str:
        """Get block explorer URL for NFT token."""
        explorers = {
            "ethereum": f"https://etherscan.io/token/{self.contract_address}?a={token_id}",
            "polygon": f"https://polygonscan.com/token/{self.contract_address}?a={token_id}",
            "base": f"https://basescan.org/token/{self.contract_address}?a={token_id}",
            "arbitrum": f"https://arbiscan.io/token/{self.contract_address}?a={token_id}",
        }
        return explorers.get(self.network, "")
    
    def _get_opensea_url(self, token_id: int) -> str:
        """Generate OpenSea URL for NFT."""
        network_slugs = {
            "ethereum": "ethereum",
            "polygon": "matic",
            "base": "base",
            "arbitrum": "arbitrum"
        }
        
        network_slug = network_slugs.get(self.network, "ethereum")
        return f"https://opensea.io/assets/{network_slug}/{self.contract_address}/{token_id}"
    
    def get_balance(self) -> Dict[str, Any]:
        """
        Get balance of the minting account.
        
        Returns:
            {
                "address": "0x123...",
                "balance_wei": 1000000000000000000,
                "balance_eth": 1.0,
                "network": "polygon"
            }
        """
        if not self.enabled or not self.account:
            return {"error": "Account not configured"}
        
        try:
            balance_wei = self.w3.eth.get_balance(self.account.address)
            balance_eth = self.w3.from_wei(balance_wei, 'ether')
            
            return {
                "address": self.account.address,
                "balance_wei": balance_wei,
                "balance_eth": float(balance_eth),
                "network": self.network
            }
        except Exception as e:
            return {"error": str(e)}
    
    def estimate_minting_cost(self) -> Dict[str, Any]:
        """
        Estimate cost to mint one NFT.
        
        Returns:
            {
                "gas_estimate": 150000,
                "gas_price_gwei": 30,
                "cost_eth": 0.0045,
                "cost_usd": 15.0  # Approximate
            }
        """
        if not self.enabled:
            return {"error": "Service not available"}
        
        try:
            gas_price = self.w3.eth.gas_price
            gas_price_gwei = self.w3.from_wei(gas_price, 'gwei')
            
            # Typical gas usage for ERC-721 mint
            gas_estimate = 150000
            
            cost_wei = gas_estimate * gas_price
            cost_eth = self.w3.from_wei(cost_wei, 'ether')
            
            # Rough USD estimate (would need price oracle in production)
            eth_price_usd = {
                "ethereum": 3000,
                "polygon": 0.80,  # MATIC price
                "base": 3000,  # Uses ETH
                "arbitrum": 3000  # Uses ETH
            }.get(self.network, 3000)
            
            cost_usd = float(cost_eth) * eth_price_usd
            
            return {
                "gas_estimate": gas_estimate,
                "gas_price_wei": gas_price,
                "gas_price_gwei": float(gas_price_gwei),
                "cost_wei": cost_wei,
                "cost_eth": float(cost_eth),
                "cost_usd_estimate": round(cost_usd, 4),
                "network": self.network
            }
        except Exception as e:
            return {"error": str(e)}
    
    def is_configured(self) -> bool:
        """Check if service is properly configured."""
        return (
            self.enabled and 
            self.contract is not None and 
            self.account is not None
        )


# Global instance (Polygon by default)
blockchain_service = BlockchainService(network=os.getenv("BLOCKCHAIN_NETWORK", "polygon"))


if __name__ == "__main__":
    # Test blockchain connection
    print(f"Testing blockchain service on {blockchain_service.network}...")
    
    if blockchain_service.is_configured():
        print("✅ Blockchain service configured")
        
        balance = blockchain_service.get_balance()
        print(f"Account: {balance.get('address')}")
        print(f"Balance: {balance.get('balance_eth')} ETH/MATIC")
        
        cost = blockchain_service.estimate_minting_cost()
        print(f"Estimated minting cost: ${cost.get('cost_usd_estimate')}")
    else:
        print("❌ Blockchain service not configured")
        print("Set BLOCKCHAIN_PRIVATE_KEY and POLYGON_RECEIPT_CONTRACT in .env")
