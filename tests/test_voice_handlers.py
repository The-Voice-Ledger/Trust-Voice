"""
Tests for voice handler business logic:
  - milestone_handler: submit evidence, verify, release funds, treasury
  - donation_handler: initiate donations (M-Pesa / Stripe paths)

Uses an in-memory SQLite database with real SQLAlchemy models.
External services (Stripe, M-Pesa, IPFS, blockchain) are mocked.

Run:
    pytest tests/test_voice_handlers.py -v
"""

import json
import sys
import math
from datetime import datetime
from decimal import Decimal
from types import ModuleType
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# ── Stub heavy service deps before importing handlers ──────────
# stripe — used by services.stripe_service
if "stripe" not in sys.modules:
    _stripe = ModuleType("stripe")
    _stripe.Event = type("Event", (), {})
    _stripe_error = ModuleType("stripe.error")
    _stripe_error.StripeError = type("StripeError", (Exception,), {})
    _stripe_error.CardError = type("CardError", (Exception,), {})
    _stripe.error = _stripe_error
    _stripe.PaymentIntent = MagicMock()
    _stripe.Webhook = MagicMock()
    _stripe.checkout = MagicMock()
    _stripe.api_key = None
    sys.modules["stripe"] = _stripe
    sys.modules["stripe.error"] = _stripe_error

# redis — used by voice.session_manager
if "redis" not in sys.modules:
    _redis = ModuleType("redis")
    _redis.from_url = MagicMock(return_value=MagicMock())
    _redis.ConnectionError = type("ConnectionError", (Exception,), {})
    sys.modules["redis"] = _redis

from database.models import (
    Base,
    User,
    Donor,
    Donation,
    Campaign,
    NGOOrganization,
    ProjectMilestone,
    MilestoneStatus,
    MilestoneVerification,
    PlatformFee,
    Payout,
)

# ── Fixtures ────────────────────────────────────────────────────


@pytest.fixture
def db_engine():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def db_session(db_engine):
    Session = sessionmaker(bind=db_engine)
    session = Session()
    session._real_close = session.close
    session.close = lambda: None  # keep open for assertions
    yield session
    session.rollback()
    Session.close_all()


@pytest.fixture
def seed(db_session):
    """Baseline test records for handler tests."""
    ngo = NGOOrganization(id=1, name="Ukulima Foundation", verification_status="VERIFIED")
    db_session.add(ngo)
    db_session.flush()

    admin = User(id=1, email="admin@ukulima.org", full_name="Admin User",
                 role="SYSTEM_ADMIN", ngo_id=1, telegram_user_id="tg_admin")
    ngo_mgr = User(id=2, email="ngo@ukulima.org", full_name="NGO Manager",
                   role="NGO_ADMIN", ngo_id=1, telegram_user_id="tg_ngo")
    field = User(id=3, email="field@ukulima.org", full_name="Field Agent",
                 role="FIELD_AGENT", telegram_user_id="tg_field")
    donor_user = User(id=4, email="donor@example.com", full_name="Jane Donor",
                      role="DONOR", telegram_user_id="tg_donor",
                      phone_number="+254712345678")
    db_session.add_all([admin, ngo_mgr, field, donor_user])
    db_session.flush()

    campaign = Campaign(
        id=1, ngo_id=1, title="Solar Schools", description="Install solar panels",
        goal_amount_usd=Decimal("25000"), raised_amount_usd=Decimal("15000"),
        category="infrastructure", location_country="Kenya",
        status="active", use_milestones=True,
        platform_fee_rate=Decimal("0.0600"),
    )
    db_session.add(campaign)
    db_session.flush()

    # Milestones across different statuses
    ms1 = ProjectMilestone(id=1, campaign_id=1, title="Site Survey",
                           sequence=1, target_amount_usd=Decimal("5000"),
                           status=MilestoneStatus.RELEASED.value,
                           released_amount_usd=Decimal("4700"),
                           platform_fee_usd=Decimal("300"))
    ms2 = ProjectMilestone(id=2, campaign_id=1, title="Panel Purchase",
                           sequence=2, target_amount_usd=Decimal("10000"),
                           status=MilestoneStatus.PENDING.value)
    ms3 = ProjectMilestone(id=3, campaign_id=1, title="Installation",
                           sequence=3, target_amount_usd=Decimal("10000"),
                           status=MilestoneStatus.EVIDENCE_SUBMITTED.value,
                           evidence_notes="Panels installed on 3 roofs",
                           evidence_submitted_at=datetime.utcnow())
    db_session.add_all([ms1, ms2, ms3])
    db_session.flush()

    # Donor + past donation
    donor = Donor(id=1, telegram_user_id="tg_donor", phone_number="+254712345678",
                  preferred_name="Jane", email="donor@example.com",
                  total_donated_usd=Decimal("200"))
    db_session.add(donor)
    db_session.flush()

    donation = Donation(id=1, donor_id=1, campaign_id=1, amount=Decimal("200"),
                        currency="USD", status="completed", payment_method="stripe",
                        created_at=datetime.utcnow())
    db_session.add(donation)
    db_session.commit()

    return {
        "admin": admin, "ngo_mgr": ngo_mgr, "field": field,
        "donor_user": donor_user, "donor": donor, "campaign": campaign,
        "ms_released": ms1, "ms_pending": ms2, "ms_evidence": ms3,
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Milestone Handler Tests
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestSubmitMilestoneEvidence:
    async def test_success(self, db_session, seed):
        from voice.handlers.milestone_handler import submit_milestone_evidence

        result = await submit_milestone_evidence(
            milestone_id=2, notes="Survey complete, photos attached",
            ipfs_hashes=["QmABC123"], user_id="tg_admin", db=db_session,
        )
        assert result["success"] is True
        assert result["status"] == MilestoneStatus.EVIDENCE_SUBMITTED.value

        ms = db_session.query(ProjectMilestone).filter(ProjectMilestone.id == 2).first()
        assert ms.status == MilestoneStatus.EVIDENCE_SUBMITTED.value
        assert ms.evidence_notes == "Survey complete, photos attached"
        assert ms.evidence_ipfs_hashes == ["QmABC123"]
        assert ms.evidence_submitted_at is not None

    async def test_wrong_status_rejected(self, db_session, seed):
        """Cannot submit evidence for an already-released milestone."""
        from voice.handlers.milestone_handler import submit_milestone_evidence

        result = await submit_milestone_evidence(
            milestone_id=1, notes="late docs", ipfs_hashes=None,
            user_id="tg_admin", db=db_session,
        )
        assert "error" in result
        assert "released" in result["error"].lower()

    async def test_resubmit_after_fail(self, db_session, seed):
        """Can resubmit evidence for a FAILED milestone."""
        from voice.handlers.milestone_handler import submit_milestone_evidence

        seed["ms_pending"].status = MilestoneStatus.FAILED.value
        db_session.commit()

        result = await submit_milestone_evidence(
            milestone_id=2, notes="Retrying with new photos",
            ipfs_hashes=None, user_id="tg_admin", db=db_session,
        )
        assert result["success"] is True

    async def test_non_owner_blocked(self, db_session, seed):
        """Random user can't submit evidence for another NGO's milestone."""
        from voice.handlers.milestone_handler import submit_milestone_evidence

        result = await submit_milestone_evidence(
            milestone_id=2, notes="hack", ipfs_hashes=None,
            user_id="tg_field", db=db_session,  # field agent, not owner
        )
        assert "error" in result
        assert "owner" in result["error"].lower()

    async def test_not_found(self, db_session, seed):
        from voice.handlers.milestone_handler import submit_milestone_evidence

        result = await submit_milestone_evidence(
            milestone_id=999, notes="x", ipfs_hashes=None,
            user_id="tg_admin", db=db_session,
        )
        assert "error" in result


class TestVerifyMilestone:
    async def test_high_score_auto_approves(self, db_session, seed):
        from voice.handlers.milestone_handler import verify_milestone

        result = await verify_milestone(
            milestone_id=3, trust_score=90, agent_notes="All good",
            user_id="tg_field", db=db_session,  # field agent
        )
        assert result["success"] is True
        assert result["auto_approved"] is True
        assert result["status"] == MilestoneStatus.VERIFIED.value

        ms = db_session.query(ProjectMilestone).filter(ProjectMilestone.id == 3).first()
        assert ms.status == MilestoneStatus.VERIFIED.value

        # Check verification record created
        v = db_session.query(MilestoneVerification).filter(
            MilestoneVerification.milestone_id == 3
        ).first()
        assert v is not None
        assert v.trust_score == 90
        assert v.status == "approved"
        assert v.field_agent_id == 3
        assert v.agent_payout_amount_usd == Decimal("30.00")

    async def test_low_score_under_review(self, db_session, seed):
        from voice.handlers.milestone_handler import verify_milestone

        result = await verify_milestone(
            milestone_id=3, trust_score=60, agent_notes="Looks incomplete",
            user_id="tg_field", db=db_session,
        )
        assert result["success"] is True
        assert result["auto_approved"] is False
        assert result["status"] == MilestoneStatus.UNDER_REVIEW.value

    async def test_donor_cannot_verify(self, db_session, seed):
        from voice.handlers.milestone_handler import verify_milestone

        result = await verify_milestone(
            milestone_id=3, trust_score=100, agent_notes="Trust me",
            user_id="tg_donor", db=db_session,  # donor
        )
        assert "error" in result
        assert "field agent" in result["error"].lower()

    async def test_wrong_status_rejected(self, db_session, seed):
        """Can only verify milestones with EVIDENCE_SUBMITTED status."""
        from voice.handlers.milestone_handler import verify_milestone

        result = await verify_milestone(
            milestone_id=2, trust_score=90, agent_notes="N/A",
            user_id="tg_field", db=db_session,  # ms2 is PENDING
        )
        assert "error" in result
        assert "evidence" in result["error"].lower()

    async def test_score_clamped(self, db_session, seed):
        """Trust score is clamped to 0-100."""
        from voice.handlers.milestone_handler import verify_milestone

        result = await verify_milestone(
            milestone_id=3, trust_score=150, agent_notes="Over the top",
            user_id="tg_field", db=db_session,
        )
        assert result["success"] is True
        assert result["trust_score"] == 100  # clamped

    async def test_with_gps_and_photos(self, db_session, seed):
        from voice.handlers.milestone_handler import verify_milestone

        result = await verify_milestone(
            milestone_id=3, trust_score=95, agent_notes="Verified on site",
            user_id="tg_field", db=db_session,
            photos=["https://ipfs.io/abc"], gps_lat=-1.286, gps_lng=36.817,
        )
        assert result["success"] is True

        v = db_session.query(MilestoneVerification).filter(
            MilestoneVerification.milestone_id == 3
        ).first()
        assert v.gps_latitude == pytest.approx(-1.286)
        assert v.gps_longitude == pytest.approx(36.817)
        assert v.photos == ["https://ipfs.io/abc"]


class TestReleaseMilestoneFunds:
    async def test_release_with_platform_fee(self, db_session, seed):
        """Release deducts 6% fee and records PlatformFee."""
        from voice.handlers.milestone_handler import release_milestone_funds

        # First verify ms3 so it can be released
        seed["ms_evidence"].status = MilestoneStatus.VERIFIED.value
        db_session.commit()

        result = await release_milestone_funds(
            milestone_id=3, user_id="tg_admin", db=db_session,
        )
        assert result["success"] is True
        assert result["status"] == "released"

        # Check amounts (6% of 10000 = 600)
        assert result["gross_amount_usd"] == 10000.0
        assert result["fee_rate_pct"] == pytest.approx(6.0)
        assert result["fee_amount_usd"] == 600.0
        assert result["net_to_project_usd"] == 9400.0

        # DB state
        ms = db_session.query(ProjectMilestone).filter(ProjectMilestone.id == 3).first()
        assert ms.status == MilestoneStatus.RELEASED.value
        assert ms.released_amount_usd == Decimal("9400.00")
        assert ms.platform_fee_usd == Decimal("600.00")
        assert ms.released_at is not None

        # PlatformFee record
        fee = db_session.query(PlatformFee).filter(PlatformFee.milestone_id == 3).first()
        assert fee is not None
        assert fee.gross_amount_usd == Decimal("10000")
        assert fee.fee_rate == Decimal("0.0600")
        assert fee.fee_amount_usd == Decimal("600.00")
        assert fee.net_to_project_usd == Decimal("9400.00")

    async def test_not_verified_rejected(self, db_session, seed):
        """Cannot release a milestone that isn't verified."""
        from voice.handlers.milestone_handler import release_milestone_funds

        result = await release_milestone_funds(
            milestone_id=2, user_id="tg_admin", db=db_session,
        )
        assert "error" in result
        assert "verified" in result["error"].lower()

    async def test_non_admin_blocked(self, db_session, seed):
        """Field agent can't release funds."""
        from voice.handlers.milestone_handler import release_milestone_funds

        seed["ms_evidence"].status = MilestoneStatus.VERIFIED.value
        db_session.commit()

        result = await release_milestone_funds(
            milestone_id=3, user_id="tg_field", db=db_session,  # field agent
        )
        assert "error" in result
        assert "owner" in result["error"].lower() or "admin" in result["error"].lower()


class TestGetMilestones:
    async def test_returns_all_milestones(self, db_session, seed):
        from voice.handlers.milestone_handler import get_milestones

        result = await get_milestones(campaign_id=1, db=db_session)
        assert result["campaign_title"] == "Solar Schools"
        assert len(result["milestones"]) == 3
        assert result["total_released_usd"] == 4700.0

        # Verify ordering by sequence
        seqs = [m["sequence"] for m in result["milestones"]]
        assert seqs == [1, 2, 3]

    async def test_not_found(self, db_session, seed):
        from voice.handlers.milestone_handler import get_milestones

        result = await get_milestones(campaign_id=999, db=db_session)
        assert "error" in result


class TestCreateMilestones:
    async def test_creates_milestones(self, db_session, seed):
        from voice.handlers.milestone_handler import create_milestones

        # Add a second campaign without milestones
        c2 = Campaign(id=2, ngo_id=1, title="Water Wells", description="Dig wells",
                       goal_amount_usd=Decimal("20000"), raised_amount_usd=Decimal("0"),
                       category="water", status="active")
        db_session.add(c2)
        db_session.commit()

        result = await create_milestones(
            campaign_id=2,
            milestones_data=[
                {"title": "Land Survey", "target_amount": 5000},
                {"title": "Drilling", "target_amount": 10000},
                {"title": "Testing", "target_amount": 5000},
            ],
            user_id="tg_admin",
            db=db_session,
        )
        assert result["success"] is True
        assert len(result["milestones"]) == 3
        assert result["total_target_usd"] == 20000.0

        # DB check
        ms = db_session.query(ProjectMilestone).filter(
            ProjectMilestone.campaign_id == 2
        ).all()
        assert len(ms) == 3
        assert all(m.status == MilestoneStatus.PENDING.value for m in ms)

    async def test_duplicate_milestones_rejected(self, db_session, seed):
        """Campaign 1 already has milestones — can't create more."""
        from voice.handlers.milestone_handler import create_milestones

        result = await create_milestones(
            campaign_id=1,
            milestones_data=[{"title": "Extra", "target_amount": 1000}],
            user_id="tg_admin", db=db_session,
        )
        assert "error" in result
        assert "already exist" in result["error"].lower()


class TestGetProjectTreasury:
    async def test_treasury_overview(self, db_session, seed):
        from voice.handlers.milestone_handler import get_project_treasury

        result = await get_project_treasury(campaign_id=1, db=db_session)
        assert result["campaign_title"] == "Solar Schools"
        assert result["total_raised_usd"] == 15000.0
        assert result["total_released_usd"] == 4700.0
        assert result["total_fees_collected_usd"] == 300.0
        assert result["funds_held_usd"] == 10000.0  # 15000 - 4700 - 300
        assert len(result["milestones"]) == 3


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Donation Handler Tests
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestInitiateVoiceDonation:

    async def test_stripe_success(self, db_session, seed):
        """Stripe path: creates donation + returns checkout URL."""
        from voice.handlers.donation_handler import initiate_voice_donation

        fake_pi = {"id": "pi_test123", "client_secret": "cs_test_secret"}

        with patch("services.stripe_service.create_payment_intent",
                   return_value=fake_pi):
            result = await initiate_voice_donation(
                db=db_session, telegram_user_id="tg_donor",
                campaign_id=1, amount=50.0, currency="USD",
                payment_method="stripe",
            )

        assert result["success"] is True
        assert result["payment_method"] == "stripe"
        assert "checkout_url" in result
        assert result["donation_id"] is not None

        # Verify donation record
        d = db_session.query(Donation).filter(
            Donation.payment_intent_id == "pi_test123"
        ).first()
        assert d is not None
        assert float(d.amount) == 50.0
        assert d.status == "pending"
        assert d.payment_method == "stripe"

    async def test_mpesa_success(self, db_session, seed):
        """M-Pesa path: creates donation + initiates STK push."""
        from voice.handlers.donation_handler import initiate_voice_donation

        fake_stk = {"success": True, "CheckoutRequestID": "ws_CO_123"}

        with patch("services.mpesa.mpesa_stk_push",
                   return_value=fake_stk):
            result = await initiate_voice_donation(
                db=db_session, telegram_user_id="tg_donor",
                campaign_id=1, amount=5000, currency="KES",
                payment_method="mpesa",
            )

        assert result["success"] is True
        assert result["payment_method"] == "mpesa"
        assert "M-Pesa" in result.get("instructions", "")

    async def test_unregistered_user_rejected(self, db_session, seed):
        from voice.handlers.donation_handler import initiate_voice_donation

        result = await initiate_voice_donation(
            db=db_session, telegram_user_id="tg_nonexistent",
            campaign_id=1, amount=10.0,
        )
        assert result["success"] is False
        assert "not registered" in result["error"].lower() or "not found" in result["error"].lower()

    async def test_inactive_campaign_rejected(self, db_session, seed):
        from voice.handlers.donation_handler import initiate_voice_donation

        seed["campaign"].status = "completed"
        db_session.commit()

        with patch("services.stripe_service.create_payment_intent",
                   return_value={"id": "pi_x", "client_secret": "cs_x"}):
            result = await initiate_voice_donation(
                db=db_session, telegram_user_id="tg_donor",
                campaign_id=1, amount=10.0,
            )
        assert result["success"] is False
        assert "not active" in result["error"].lower()

    async def test_auto_creates_donor_record(self, db_session, seed):
        """User without a Donor row gets one created automatically."""
        from voice.handlers.donation_handler import initiate_voice_donation

        fake_pi = {"id": "pi_auto", "client_secret": "cs_auto"}

        with patch("services.stripe_service.create_payment_intent",
                   return_value=fake_pi):
            result = await initiate_voice_donation(
                db=db_session, telegram_user_id="tg_admin",  # admin has no Donor record
                campaign_id=1, amount=100.0, currency="USD",
            )

        assert result["success"] is True
        donor = db_session.query(Donor).filter(
            Donor.telegram_user_id == "tg_admin"
        ).first()
        assert donor is not None
        assert donor.preferred_name == "Admin User"

    async def test_auto_detects_mpesa(self, db_session, seed):
        """Kenyan phone → auto-selects M-Pesa."""
        from voice.handlers.donation_handler import initiate_voice_donation

        fake_stk = {"success": True, "CheckoutRequestID": "ws_auto"}

        with patch("services.mpesa.mpesa_stk_push",
                   return_value=fake_stk):
            result = await initiate_voice_donation(
                db=db_session, telegram_user_id="tg_donor",
                campaign_id=1, amount=1000, currency="KES",
                # no payment_method — should auto-select mpesa
            )
        assert result["success"] is True
        assert result["payment_method"] == "mpesa"

    async def test_stripe_failure_rolls_back(self, db_session, seed):
        """If Stripe fails, donation should be rolled back."""
        from voice.handlers.donation_handler import initiate_voice_donation

        with patch("services.stripe_service.create_payment_intent",
                   return_value={"error": "card_declined"}):
            result = await initiate_voice_donation(
                db=db_session, telegram_user_id="tg_donor",
                campaign_id=1, amount=50.0, currency="USD",
                payment_method="stripe",
            )

        assert result["success"] is False

    async def test_campaign_not_found(self, db_session, seed):
        from voice.handlers.donation_handler import initiate_voice_donation

        result = await initiate_voice_donation(
            db=db_session, telegram_user_id="tg_donor",
            campaign_id=9999, amount=10.0,
        )
        assert result["success"] is False
        assert "not found" in result["error"].lower()


class TestGetDonationStatus:
    async def test_returns_latest(self, db_session, seed):
        from voice.handlers.donation_handler import get_donation_status

        result = await get_donation_status(
            db=db_session, telegram_user_id="tg_donor",
        )
        assert result["success"] is True
        d = result["donation"]
        assert float(d["amount"]) == 200.0
        assert d["status"] == "completed"
        assert d["campaign_title"] == "Solar Schools"

    async def test_no_donor(self, db_session, seed):
        from voice.handlers.donation_handler import get_donation_status

        result = await get_donation_status(
            db=db_session, telegram_user_id="tg_nobody",
        )
        assert result["success"] is False


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Full lifecycle integration test
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class TestMilestoneLifecycle:
    """End-to-end: submit evidence → verify → release funds."""

    async def test_full_flow(self, db_session, seed):
        from voice.handlers.milestone_handler import (
            submit_milestone_evidence,
            verify_milestone,
            release_milestone_funds,
            get_project_treasury,
        )

        # 1. Submit evidence for ms2 (PENDING)
        r1 = await submit_milestone_evidence(
            milestone_id=2, notes="Survey report attached",
            ipfs_hashes=["QmSurveyPDF"], user_id="tg_admin", db=db_session,
        )
        assert r1["success"] is True
        assert r1["status"] == MilestoneStatus.EVIDENCE_SUBMITTED.value

        # 2. Field agent verifies with high score
        r2 = await verify_milestone(
            milestone_id=2, trust_score=92, agent_notes="Visited site, confirmed",
            user_id="tg_field", db=db_session,
        )
        assert r2["success"] is True
        assert r2["auto_approved"] is True
        assert r2["status"] == MilestoneStatus.VERIFIED.value

        # 3. Admin releases funds
        r3 = await release_milestone_funds(
            milestone_id=2, user_id="tg_admin", db=db_session,
        )
        assert r3["success"] is True
        assert r3["gross_amount_usd"] == 10000.0
        assert r3["fee_amount_usd"] == 600.0  # 6% of 10000
        assert r3["net_to_project_usd"] == 9400.0

        # 4. Treasury reflects new release
        t = await get_project_treasury(campaign_id=1, db=db_session)
        # ms1 released 4700, ms2 just released 9400 = 14100 total
        assert t["total_released_usd"] == 14100.0
        # ms1 fee 300 + ms2 fee 600 = 900
        assert t["total_fees_collected_usd"] == 900.0

    async def test_low_score_needs_review_before_release(self, db_session, seed):
        """Low trust score → UNDER_REVIEW → can't release."""
        from voice.handlers.milestone_handler import (
            submit_milestone_evidence,
            verify_milestone,
            release_milestone_funds,
        )

        # Submit evidence for ms2
        await submit_milestone_evidence(
            milestone_id=2, notes="Done", ipfs_hashes=None,
            user_id="tg_admin", db=db_session,
        )

        # Verify with low score
        r = await verify_milestone(
            milestone_id=2, trust_score=50, agent_notes="Doubtful",
            user_id="tg_field", db=db_session,
        )
        assert r["status"] == MilestoneStatus.UNDER_REVIEW.value

        # Attempt release — should fail
        r3 = await release_milestone_funds(
            milestone_id=2, user_id="tg_admin", db=db_session,
        )
        assert "error" in r3
        assert "verified" in r3["error"].lower()
