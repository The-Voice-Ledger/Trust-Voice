"""
MilestoneTreasury Service — on-chain audit trail for milestone lifecycle.

Calls the deployed MilestoneTreasury.sol contract to record immutable
events: milestone creation, evidence submission, verification, fund
release, and failure.  The contract does NOT hold funds — it is a
transparent audit trail for donors, auditors, and regulators.

Contract: 0xB84245fCf8A5fBb8127C65278417c982652609af  (Base Sepolia)
"""

import os
import json
import logging
from typing import Optional, Dict, Any
from decimal import Decimal

logger = logging.getLogger(__name__)

try:
    from web3 import Web3
    from eth_account import Account
    WEB3_AVAILABLE = True
except ImportError:
    WEB3_AVAILABLE = False
    logger.warning("web3 not installed — MilestoneTreasury service disabled.")


class MilestoneTreasuryService:
    """
    Writes to the MilestoneTreasury.sol contract on Base Sepolia.

    Usage:
        from services.milestone_treasury_service import milestone_treasury

        tx = milestone_treasury.record_create(campaign_id=28, milestone_id=1, target_usd=110000)
        tx = milestone_treasury.record_evidence(campaign_id=28, milestone_id=1, ipfs_hash="Qm...")
        tx = milestone_treasury.record_verify(campaign_id=28, milestone_id=1, agent_addr, score)
        tx = milestone_treasury.record_release(campaign_id=28, milestone_id=1, gross, fee)
    """

    def __init__(self):
        self.enabled = False
        self.contract = None
        self.account = None
        self.w3 = None
        self._nonce = None  # Managed nonce to avoid race conditions

        if not WEB3_AVAILABLE:
            return

        contract_address = os.getenv("MILESTONE_TREASURY_CONTRACT")
        rpc_url = os.getenv("BASE_SEPOLIA_RPC_URL")
        private_key = os.getenv("PRIVATE_KEY_SEP")

        if not contract_address or not rpc_url:
            logger.info("MilestoneTreasury not configured (missing env vars).")
            return

        try:
            self.w3 = Web3(Web3.HTTPProvider(rpc_url))
            if not self.w3.is_connected():
                logger.warning("Cannot connect to Base Sepolia RPC.")
                return

            # Load ABI from forge output
            abi = self._load_abi()
            if not abi:
                return

            self.contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(contract_address),
                abi=abi,
            )

            if private_key:
                self.account = Account.from_key(private_key)
                logger.info(
                    f"✅ MilestoneTreasury connected: {contract_address[:10]}… "
                    f"signer={self.account.address[:10]}…"
                )
                self.enabled = True
            else:
                logger.warning("PRIVATE_KEY_SEP not set — read-only mode.")
        except Exception as e:
            logger.error(f"MilestoneTreasury init failed: {e}")

    # ── ABI loader ──────────────────────────────────────────────

    def _load_abi(self) -> Optional[list]:
        abi_path = os.path.join(
            os.path.dirname(__file__), "..",
            "blockchain", "out",
            "MilestoneTreasury.sol", "MilestoneTreasury.json",
        )
        try:
            with open(abi_path) as f:
                return json.load(f).get("abi", [])
        except FileNotFoundError:
            logger.warning(f"ABI not found at {abi_path}")
            return None

    # ── Tx helper ───────────────────────────────────────────────

    def _send_tx(self, fn) -> Dict[str, Any]:
        """Build, sign, send a transaction and return result dict."""
        if not self.enabled:
            return {"success": False, "error": "Service not enabled"}
        try:
            # Use managed nonce to avoid race conditions on rapid calls
            if self._nonce is None:
                self._nonce = self.w3.eth.get_transaction_count(self.account.address)

            gas_price = self.w3.eth.gas_price
            tx = fn.build_transaction({
                "from": self.account.address,
                "nonce": self._nonce,
                "gas": 300_000,
                "gasPrice": int(gas_price * 1.2),
            })
            signed = self.w3.eth.account.sign_transaction(tx, self.account.key)
            tx_hash = self.w3.eth.send_raw_transaction(signed.rawTransaction)
            self._nonce += 1  # Increment immediately for next call
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

            success = receipt["status"] == 1
            result = {
                "success": success,
                "tx_hash": tx_hash.hex(),
                "block": receipt["blockNumber"],
                "gas_used": receipt["gasUsed"],
                "explorer": f"https://sepolia.basescan.org/tx/{tx_hash.hex()}",
            }
            if success:
                logger.info(f"✅ On-chain tx: {tx_hash.hex()}")
            else:
                logger.error(f"❌ On-chain tx reverted: {tx_hash.hex()}")
            return result
        except Exception as e:
            logger.error(f"❌ On-chain tx failed: {e}")
            self._nonce = None  # Reset nonce on failure
            return {"success": False, "error": str(e)}

    # ── Public write methods ────────────────────────────────────

    def record_create(
        self, campaign_id: int, milestone_id: int, target_usd: Decimal
    ) -> Dict[str, Any]:
        """Record milestone creation on-chain."""
        cents = int(target_usd * 100)
        fn = self.contract.functions.createMilestone(campaign_id, milestone_id, cents)
        return self._send_tx(fn)

    def record_evidence(
        self, campaign_id: int, milestone_id: int, ipfs_hash: str
    ) -> Dict[str, Any]:
        """Record evidence submission on-chain."""
        fn = self.contract.functions.submitEvidence(
            campaign_id, milestone_id, ipfs_hash or ""
        )
        return self._send_tx(fn)

    def record_verify(
        self,
        campaign_id: int,
        milestone_id: int,
        field_agent_address: str,
        trust_score: int,
    ) -> Dict[str, Any]:
        """Record field-agent verification on-chain."""
        # Use zero-address if agent has no wallet
        agent_addr = (
            Web3.to_checksum_address(field_agent_address)
            if field_agent_address and Web3.is_address(field_agent_address)
            else "0x0000000000000000000000000000000000000000"
        )
        fn = self.contract.functions.verifyMilestone(
            campaign_id, milestone_id, agent_addr, trust_score
        )
        return self._send_tx(fn)

    def record_release(
        self,
        campaign_id: int,
        milestone_id: int,
        gross_usd: Decimal,
        fee_usd: Decimal,
    ) -> Dict[str, Any]:
        """Record fund release on-chain."""
        fn = self.contract.functions.releaseFunds(
            campaign_id, milestone_id,
            int(gross_usd * 100),
            int(fee_usd * 100),
        )
        return self._send_tx(fn)

    def record_fail(
        self, campaign_id: int, milestone_id: int, reason: str
    ) -> Dict[str, Any]:
        """Record milestone failure on-chain."""
        fn = self.contract.functions.failMilestone(campaign_id, milestone_id, reason)
        return self._send_tx(fn)

    # ── Read methods ────────────────────────────────────────────

    def get_on_chain_milestone(
        self, campaign_id: int, milestone_id: int
    ) -> Optional[Dict[str, Any]]:
        """Read milestone struct from the contract."""
        if not self.contract:
            return None
        try:
            result = self.contract.functions.getMilestone(
                campaign_id, milestone_id
            ).call()
            statuses = [
                "Pending", "Active", "EvidenceSubmitted",
                "UnderReview", "Verified", "Released", "Failed",
            ]
            return {
                "campaign_id": result[0],
                "milestone_id": result[1],
                "target_amount_cents": result[2],
                "status": statuses[result[3]] if result[3] < len(statuses) else str(result[3]),
                "created_at": result[4],
                "released_at": result[5],
            }
        except Exception as e:
            logger.error(f"Failed to read on-chain milestone: {e}")
            return None

    def is_configured(self) -> bool:
        return self.enabled


# ── Global singleton ────────────────────────────────────────────
milestone_treasury = MilestoneTreasuryService()
