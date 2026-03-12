// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Ownable} from "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title MilestoneTreasury
 * @dev On-chain audit trail for milestone-based crowdfunding.
 *
 * This contract does NOT hold funds.  Actual money movement happens
 * off-chain via Stripe / M-Pesa / bank.  The contract records immutable
 * events so donors, auditors, and regulators can verify:
 *   1. Milestones were created before funding began.
 *   2. Evidence was submitted by the project owner.
 *   3. A field agent verified on-the-ground progress.
 *   4. The platform released funds only after verification.
 *
 * Deployed on: Polygon / Base / Arbitrum (same networks as TaxReceiptNFT)
 */
contract MilestoneTreasury is Ownable {

    // ── Enums ──────────────────────────────────────────────────
    enum Status {
        Pending,
        Active,
        EvidenceSubmitted,
        UnderReview,
        Verified,
        Released,
        Failed
    }

    // ── Structs ────────────────────────────────────────────────
    struct Milestone {
        uint256 campaignId;
        uint256 milestoneId;      // Matches DB primary key
        uint256 targetAmountCents; // USD cents to avoid decimals
        Status  status;
        uint256 createdAt;
        uint256 releasedAt;
    }

    // ── State ──────────────────────────────────────────────────
    /// campaignId => milestoneId => Milestone
    mapping(uint256 => mapping(uint256 => Milestone)) public milestones;

    /// campaignId => number of milestones registered
    mapping(uint256 => uint256) public milestoneCounts;

    // ── Events ─────────────────────────────────────────────────
    event MilestoneCreated(
        uint256 indexed campaignId,
        uint256 indexed milestoneId,
        uint256 targetAmountCents,
        uint256 timestamp
    );

    event EvidenceSubmitted(
        uint256 indexed campaignId,
        uint256 indexed milestoneId,
        string  ipfsHash,
        uint256 timestamp
    );

    event MilestoneVerified(
        uint256 indexed campaignId,
        uint256 indexed milestoneId,
        address indexed fieldAgent,
        uint256 trustScore,
        uint256 timestamp
    );

    event FundsReleased(
        uint256 indexed campaignId,
        uint256 indexed milestoneId,
        uint256 grossAmountCents,
        uint256 feeAmountCents,
        uint256 netAmountCents,
        uint256 timestamp
    );

    event MilestoneFailed(
        uint256 indexed campaignId,
        uint256 indexed milestoneId,
        string  reason,
        uint256 timestamp
    );

    // ── Constructor ────────────────────────────────────────────
    constructor() Ownable(msg.sender) {}

    // ── Write functions (owner only — called by backend) ──────

    /**
     * @notice Register a new milestone on-chain.
     * @param campaignId  Platform campaign ID
     * @param milestoneId Platform milestone ID (DB primary key)
     * @param targetAmountCents Target amount in USD cents
     */
    function createMilestone(
        uint256 campaignId,
        uint256 milestoneId,
        uint256 targetAmountCents
    ) external onlyOwner {
        require(
            milestones[campaignId][milestoneId].createdAt == 0,
            "Milestone already registered"
        );

        milestones[campaignId][milestoneId] = Milestone({
            campaignId: campaignId,
            milestoneId: milestoneId,
            targetAmountCents: targetAmountCents,
            status: Status.Pending,
            createdAt: block.timestamp,
            releasedAt: 0
        });

        milestoneCounts[campaignId]++;

        emit MilestoneCreated(
            campaignId, milestoneId, targetAmountCents, block.timestamp
        );
    }

    /**
     * @notice Record evidence submission by the project owner.
     * @param campaignId  Platform campaign ID
     * @param milestoneId Platform milestone ID
     * @param ipfsHash    IPFS content hash of evidence bundle
     */
    function submitEvidence(
        uint256 campaignId,
        uint256 milestoneId,
        string calldata ipfsHash
    ) external onlyOwner {
        Milestone storage m = milestones[campaignId][milestoneId];
        require(m.createdAt != 0, "Milestone not found");
        require(
            m.status == Status.Pending || m.status == Status.Active,
            "Cannot submit evidence in current status"
        );

        m.status = Status.EvidenceSubmitted;

        emit EvidenceSubmitted(
            campaignId, milestoneId, ipfsHash, block.timestamp
        );
    }

    /**
     * @notice Record field-agent verification result.
     * @param campaignId  Platform campaign ID
     * @param milestoneId Platform milestone ID
     * @param fieldAgent  Wallet of verifying field agent
     * @param trustScore  Trust score 0-100
     */
    function verifyMilestone(
        uint256 campaignId,
        uint256 milestoneId,
        address fieldAgent,
        uint256 trustScore
    ) external onlyOwner {
        Milestone storage m = milestones[campaignId][milestoneId];
        require(m.createdAt != 0, "Milestone not found");
        require(
            m.status == Status.EvidenceSubmitted || m.status == Status.UnderReview,
            "Evidence not yet submitted"
        );

        m.status = Status.Verified;

        emit MilestoneVerified(
            campaignId, milestoneId, fieldAgent, trustScore, block.timestamp
        );
    }

    /**
     * @notice Record fund release after verification.
     * @param campaignId       Platform campaign ID
     * @param milestoneId      Platform milestone ID
     * @param grossAmountCents Full milestone amount in USD cents
     * @param feeAmountCents   Platform fee in USD cents
     */
    function releaseFunds(
        uint256 campaignId,
        uint256 milestoneId,
        uint256 grossAmountCents,
        uint256 feeAmountCents
    ) external onlyOwner {
        Milestone storage m = milestones[campaignId][milestoneId];
        require(m.createdAt != 0, "Milestone not found");
        require(m.status == Status.Verified, "Milestone not verified");

        m.status = Status.Released;
        m.releasedAt = block.timestamp;

        uint256 net = grossAmountCents - feeAmountCents;

        emit FundsReleased(
            campaignId, milestoneId, grossAmountCents, feeAmountCents, net, block.timestamp
        );
    }

    /**
     * @notice Mark a milestone as failed (e.g. verification rejected).
     * @param campaignId  Platform campaign ID
     * @param milestoneId Platform milestone ID
     * @param reason      Human-readable failure reason
     */
    function failMilestone(
        uint256 campaignId,
        uint256 milestoneId,
        string calldata reason
    ) external onlyOwner {
        Milestone storage m = milestones[campaignId][milestoneId];
        require(m.createdAt != 0, "Milestone not found");

        m.status = Status.Failed;

        emit MilestoneFailed(
            campaignId, milestoneId, reason, block.timestamp
        );
    }

    // ── Read functions (public) ────────────────────────────────

    /**
     * @notice Get milestone details.
     */
    function getMilestone(
        uint256 campaignId,
        uint256 milestoneId
    ) external view returns (Milestone memory) {
        return milestones[campaignId][milestoneId];
    }
}
