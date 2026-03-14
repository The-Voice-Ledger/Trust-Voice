"""
Tests for voice-first tools (Tier 1–3) in voice/livekit_agent.py.

Uses an in-memory SQLite database with the real SQLAlchemy models to
test each @function_tool in isolation, without needing LiveKit or
a real Postgres instance.

Run:
    pytest tests/test_voice_tools.py -v
"""

import json
import sys
import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from types import ModuleType
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# ── Mock out heavy optional deps that aren't in venv-livekit ───
#    donate_to_campaign and milestone tools do deferred imports from
#    voice.handlers, which transitively pull in stripe, redis, etc.
#    We stub these base libraries so the real handler modules can import
#    without installing every service SDK.
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
    Payout,
)

# ── Fixtures ────────────────────────────────────────────────────


@pytest.fixture
def db_engine():
    """Create an in-memory SQLite engine with all tables."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def db_session(db_engine):
    """Provide a fresh DB session per test, rolled back after.

    We neuter ``close()`` so that the production tool code's
    ``finally: db.close()`` doesn't destroy the session mid-test.
    """
    Session = sessionmaker(bind=db_engine)
    session = Session()
    session.close = lambda: None  # keep it open for assertions
    yield session
    session.rollback()
    Session.close_all()


@pytest.fixture
def seed_data(db_session):
    """Create baseline test records: NGO, users, campaign, donor, donations, milestones."""
    # NGO
    ngo = NGOOrganization(
        id=1,
        name="Test Foundation",
        description="A test NGO",
        verification_status="VERIFIED",
    )
    db_session.add(ngo)
    db_session.flush()

    # Users
    admin_user = User(
        id=1,
        email="admin@test.org",
        full_name="Admin User",
        role="SYSTEM_ADMIN",
        ngo_id=1,
    )
    donor_user = User(
        id=2,
        email="donor@test.org",
        full_name="Jane Donor",
        role="DONOR",
        telegram_user_id="tg_jane",
        phone_number="+1234567890",
    )
    ngo_admin = User(
        id=3,
        email="ngo@test.org",
        full_name="NGO Manager",
        role="NGO_ADMIN",
        ngo_id=1,
    )
    field_agent = User(
        id=4,
        email="field@test.org",
        full_name="Field Agent",
        role="FIELD_AGENT",
    )
    db_session.add_all([admin_user, donor_user, ngo_admin, field_agent])
    db_session.flush()

    # Campaign
    campaign = Campaign(
        id=1,
        ngo_id=1,
        title="Clean Water for Mwanza",
        description="Build 10 wells for 3000 families",
        goal_amount_usd=Decimal("50000"),
        raised_amount_usd=Decimal("12500"),
        category="water",
        location_country="Tanzania",
        location_region="Mwanza",
        status="active",
    )
    db_session.add(campaign)
    db_session.flush()

    # Donor record (linked to donor_user)
    donor = Donor(
        id=1,
        telegram_user_id="tg_jane",
        phone_number="+1234567890",
        preferred_name="Jane",
        email="donor@test.org",
        total_donated_usd=Decimal("500"),
    )
    db_session.add(donor)
    db_session.flush()

    # Past donations
    for i, (amt, status) in enumerate([(100, "completed"), (200, "completed"), (200, "pending")]):
        d = Donation(
            id=i + 1,
            donor_id=1,
            campaign_id=1,
            amount=Decimal(str(amt)),
            currency="USD",
            status=status,
            payment_method="stripe",
            created_at=datetime.utcnow() - timedelta(days=30 - i * 10),
        )
        db_session.add(d)
    db_session.flush()

    # Milestones
    for seq, (title, status) in enumerate(
        [
            ("Land Preparation", MilestoneStatus.RELEASED.value),
            ("Seedling Purchase", MilestoneStatus.EVIDENCE_SUBMITTED.value),
            ("Irrigation Setup", MilestoneStatus.VERIFIED.value),
            ("First Harvest", MilestoneStatus.PENDING.value),
        ],
        start=1,
    ):
        ms = ProjectMilestone(
            id=seq,
            campaign_id=1,
            title=title,
            sequence=seq,
            target_amount_usd=Decimal("12500"),
            released_amount_usd=Decimal("12500") if status == MilestoneStatus.RELEASED.value else Decimal("0"),
            status=status,
        )
        db_session.add(ms)
    db_session.flush()

    # Payout
    payout = Payout(
        id=1,
        campaign_id=1,
        ngo_id=1,
        recipient_name="Test Foundation",
        amount=Decimal("12000"),
        currency="USD",
        status="pending",
    )
    db_session.add(payout)
    db_session.commit()

    return {
        "admin_user": admin_user,
        "donor_user": donor_user,
        "ngo_admin": ngo_admin,
        "field_agent": field_agent,
        "campaign": campaign,
        "donor": donor,
        "ngo": ngo,
        "payout": payout,
    }


def _make_ctx(user_id, name="Test", role="DONOR", extra=None):
    """Create a mock RunContext with userdata."""
    userdata = {"user_id": str(user_id), "name": name, "role": role}
    if extra:
        userdata.update(extra)

    ctx = MagicMock()
    ctx.userdata = userdata

    # Mock the session.room_io.room.local_participant.send_text chain
    send_text = AsyncMock()
    ctx.session.room_io.room.local_participant.send_text = send_text
    return ctx


# ── Tier 1: Read-only tool tests ───────────────────────────────

class TestSearchCampaigns:
    async def test_search_no_filter(self, db_session, seed_data):
        from voice.livekit_agent import search_campaigns

        with patch("voice.livekit_agent._get_db", return_value=db_session):
            result = json.loads(await search_campaigns())
        assert "campaigns" in result
        assert len(result["campaigns"]) >= 1
        assert result["campaigns"][0]["title"] == "Clean Water for Mwanza"

    async def test_search_by_category(self, db_session, seed_data):
        from voice.livekit_agent import search_campaigns

        with patch("voice.livekit_agent._get_db", return_value=db_session):
            result = json.loads(await search_campaigns(category="water"))
        assert len(result["campaigns"]) == 1

        with patch("voice.livekit_agent._get_db", return_value=db_session):
            result = json.loads(await search_campaigns(category="education"))
        assert len(result["campaigns"]) == 0

    async def test_search_by_location(self, db_session, seed_data):
        from voice.livekit_agent import search_campaigns

        with patch("voice.livekit_agent._get_db", return_value=db_session):
            result = json.loads(await search_campaigns(location="Tanzania"))
        assert len(result["campaigns"]) == 1

    async def test_search_by_keyword(self, db_session, seed_data):
        from voice.livekit_agent import search_campaigns

        with patch("voice.livekit_agent._get_db", return_value=db_session):
            result = json.loads(await search_campaigns(keyword="water"))
        assert len(result["campaigns"]) >= 1

    async def test_search_no_results(self, db_session, seed_data):
        from voice.livekit_agent import search_campaigns

        with patch("voice.livekit_agent._get_db", return_value=db_session):
            result = json.loads(await search_campaigns(keyword="nonexistent_xyz"))
        assert result["campaigns"] == []
        assert "message" in result


class TestGetCampaignDetails:
    async def test_valid_campaign(self, db_session, seed_data):
        from voice.livekit_agent import get_campaign_details

        with patch("voice.livekit_agent._get_db", return_value=db_session):
            result = json.loads(await get_campaign_details(campaign_id=1))
        c = result["campaign"]
        assert c["title"] == "Clean Water for Mwanza"
        assert c["goal_usd"] == 50000.0
        assert c["raised_usd"] == 12500.0
        assert c["progress_pct"] == 25.0
        assert c["ngo_name"] == "Test Foundation"

    async def test_invalid_campaign(self, db_session, seed_data):
        from voice.livekit_agent import get_campaign_details

        with patch("voice.livekit_agent._get_db", return_value=db_session):
            result = json.loads(await get_campaign_details(campaign_id=9999))
        assert "error" in result


class TestGetPlatformStats:
    async def test_stats(self, db_session, seed_data):
        from voice.livekit_agent import get_platform_stats

        with patch("voice.livekit_agent._get_db", return_value=db_session):
            result = json.loads(await get_platform_stats())
        stats = result["stats"]
        assert stats["active_campaigns"] == 1
        assert stats["total_donors"] == 1
        # 2 completed donations totaling 300
        assert stats["total_donations"] == 2
        assert stats["total_raised_usd"] == 300.0


class TestGetProjectMilestones:
    async def test_milestones(self, db_session, seed_data):
        from voice.livekit_agent import get_project_milestones

        with patch("voice.livekit_agent._get_db", return_value=db_session):
            result = json.loads(await get_project_milestones(campaign_id=1))
        assert result["campaign_title"] == "Clean Water for Mwanza"
        ms = result["milestones"]
        assert len(ms) == 4
        assert ms[0]["title"] == "Land Preparation"
        assert ms[0]["sequence"] == 1
        assert ms[0]["released_amount_usd"] == 12500.0

    async def test_invalid_campaign(self, db_session, seed_data):
        from voice.livekit_agent import get_project_milestones

        with patch("voice.livekit_agent._get_db", return_value=db_session):
            result = json.loads(await get_project_milestones(campaign_id=9999))
        assert "error" in result


class TestGetHelp:
    async def test_help(self):
        from voice.livekit_agent import get_help

        result = json.loads(await get_help())
        assert "capabilities" in result
        assert len(result["capabilities"]) > 0
        assert "message" in result


# ── Tier 1: Write tool tests ───────────────────────────────────


class TestCheckMyDonations:
    async def test_authenticated_donor(self, db_session, seed_data):
        from voice.livekit_agent import check_my_donations

        ctx = _make_ctx(user_id=2, name="Jane", role="DONOR")
        with patch("voice.livekit_agent._get_db", return_value=db_session):
            result = json.loads(await check_my_donations(ctx, limit=5))

        assert result["count"] == 3
        assert result["total_donated_usd"] == 500.0
        # Most recent first
        assert result["donations"][0]["campaign"] == "Clean Water for Mwanza"

    async def test_anonymous_user(self, db_session, seed_data):
        from voice.livekit_agent import check_my_donations

        ctx = _make_ctx(user_id="web_anonymous", role="DONOR")
        with patch("voice.livekit_agent._get_db", return_value=db_session):
            result = json.loads(await check_my_donations(ctx))
        assert "error" in result

    async def test_user_no_donations(self, db_session, seed_data):
        from voice.livekit_agent import check_my_donations

        ctx = _make_ctx(user_id=4, name="Field", role="FIELD_AGENT")
        with patch("voice.livekit_agent._get_db", return_value=db_session):
            result = json.loads(await check_my_donations(ctx))
        assert result["donations"] == []

    async def test_sends_action_card(self, db_session, seed_data):
        """Tier 2: check_my_donations should push a donation_history card."""
        from voice.livekit_agent import check_my_donations

        ctx = _make_ctx(user_id=2, name="Jane", role="DONOR")
        with patch("voice.livekit_agent._get_db", return_value=db_session):
            await check_my_donations(ctx, limit=5)

        send_text = ctx.session.room_io.room.local_participant.send_text
        assert send_text.called
        card = json.loads(send_text.call_args[0][0])
        assert card["type"] == "donation_history"
        assert card["count"] == 3


class TestDonateToCampaign:
    async def test_anonymous_blocked(self, db_session, seed_data):
        from voice.livekit_agent import donate_to_campaign

        ctx = _make_ctx(user_id="web_anonymous")
        with patch("voice.livekit_agent._get_db", return_value=db_session):
            result = json.loads(await donate_to_campaign(ctx, campaign_id=1, amount=50.0))
        assert "error" in result
        assert "signed in" in result["error"]

    async def test_invalid_campaign(self, db_session, seed_data):
        from voice.livekit_agent import donate_to_campaign

        ctx = _make_ctx(user_id=2, role="DONOR")
        with patch("voice.livekit_agent._get_db", return_value=db_session):
            result = json.loads(await donate_to_campaign(ctx, campaign_id=9999, amount=50.0))
        assert "error" in result

    async def test_inactive_campaign(self, db_session, seed_data):
        from voice.livekit_agent import donate_to_campaign

        # Make campaign inactive
        seed_data["campaign"].status = "completed"
        db_session.commit()

        ctx = _make_ctx(user_id=2, role="DONOR")
        with patch("voice.livekit_agent._get_db", return_value=db_session):
            result = json.loads(await donate_to_campaign(ctx, campaign_id=1, amount=50.0))
        assert "error" in result
        assert "not active" in result["error"]

    async def test_stripe_donation_sends_payment_card(self, db_session, seed_data):
        """Successful Stripe donation should push a payment_link action card."""
        from voice.livekit_agent import donate_to_campaign

        mock_result = {
            "success": True,
            "donation_id": 99,
            "payment_method": "stripe",
            "checkout_url": "https://checkout.stripe.com/test",
        }

        ctx = _make_ctx(user_id=2, name="Jane", role="DONOR")
        with patch("voice.livekit_agent._get_db", return_value=db_session), \
             patch("voice.handlers.donation_handler.initiate_voice_donation",
                   new_callable=AsyncMock, return_value=mock_result):
            result = json.loads(await donate_to_campaign(
                ctx, campaign_id=1, amount=50.0, currency="USD", payment_method="stripe",
            ))

        assert result["success"] is True
        assert result["checkout_url"] == "https://checkout.stripe.com/test"

        # Verify action card was pushed
        send_text = ctx.session.room_io.room.local_participant.send_text
        assert send_text.called
        card = json.loads(send_text.call_args[0][0])
        assert card["type"] == "payment_link"
        assert card["url"] == "https://checkout.stripe.com/test"
        assert card["amount"] == 50.0

    async def test_mpesa_donation_sends_receipt_card(self, db_session, seed_data):
        """Successful M-Pesa donation should push a donation_receipt card."""
        from voice.livekit_agent import donate_to_campaign

        mock_result = {
            "success": True,
            "donation_id": 100,
            "payment_method": "mpesa",
            "instructions": "Check your phone for the M-Pesa prompt.",
        }

        ctx = _make_ctx(user_id=2, name="Jane", role="DONOR")
        with patch("voice.livekit_agent._get_db", return_value=db_session), \
             patch("voice.handlers.donation_handler.initiate_voice_donation",
                   new_callable=AsyncMock, return_value=mock_result):
            result = json.loads(await donate_to_campaign(
                ctx, campaign_id=1, amount=1000.0, currency="KES", payment_method="mpesa",
            ))

        assert result["success"] is True

        send_text = ctx.session.room_io.room.local_participant.send_text
        card = json.loads(send_text.call_args[0][0])
        assert card["type"] == "donation_receipt"
        assert card["payment_method"] == "mpesa"
        assert card["status"] == "pending"

    async def test_auto_creates_donor_record(self, db_session, seed_data):
        """When user has no donor record, one should be created."""
        from voice.livekit_agent import donate_to_campaign

        # Use admin user (id=1) who has no donor record
        mock_result = {
            "success": True,
            "donation_id": 101,
            "payment_method": "stripe",
            "checkout_url": "https://checkout.stripe.com/new",
        }
        ctx = _make_ctx(user_id=1, name="Admin", role="SYSTEM_ADMIN")
        with patch("voice.livekit_agent._get_db", return_value=db_session), \
             patch("voice.handlers.donation_handler.initiate_voice_donation",
                   new_callable=AsyncMock, return_value=mock_result):
            result = json.loads(await donate_to_campaign(
                ctx, campaign_id=1, amount=25.0, currency="USD",
            ))
        assert result["success"] is True

        # Verify donor was created
        new_donor = db_session.query(Donor).filter(Donor.email == "admin@test.org").first()
        assert new_donor is not None


class TestApprovePayout:
    async def test_admin_approve(self, db_session, seed_data):
        from voice.livekit_agent import approve_payout

        ctx = _make_ctx(user_id=1, name="Admin", role="SYSTEM_ADMIN")
        with patch("voice.livekit_agent._get_db", return_value=db_session):
            result = json.loads(await approve_payout(ctx, payout_id=1))

        assert result["success"] is True
        assert result["status"] == "approved"
        assert result["amount"] == 12000.0

        # Verify DB updated
        payout = db_session.query(Payout).get(1)
        assert payout.status == "approved"
        assert payout.approved_by == 1

    async def test_donor_cannot_approve(self, db_session, seed_data):
        from voice.livekit_agent import approve_payout

        ctx = _make_ctx(user_id=2, name="Jane", role="DONOR")
        with patch("voice.livekit_agent._get_db", return_value=db_session):
            result = json.loads(await approve_payout(ctx, payout_id=1))
        assert "error" in result
        assert "Only admins" in result["error"]

    async def test_already_approved(self, db_session, seed_data):
        from voice.livekit_agent import approve_payout

        seed_data["payout"].status = "approved"
        db_session.commit()

        ctx = _make_ctx(user_id=1, role="SYSTEM_ADMIN")
        with patch("voice.livekit_agent._get_db", return_value=db_session):
            result = json.loads(await approve_payout(ctx, payout_id=1))
        assert "error" in result
        assert "already" in result["error"]

    async def test_ngo_admin_own_ngo_only(self, db_session, seed_data):
        from voice.livekit_agent import approve_payout

        # NGO admin (ngo_id=1) should be able to approve payout for ngo_id=1
        ctx = _make_ctx(user_id=3, name="NGO Mgr", role="NGO_ADMIN")
        with patch("voice.livekit_agent._get_db", return_value=db_session):
            result = json.loads(await approve_payout(ctx, payout_id=1))
        assert result["success"] is True

    async def test_ngo_admin_other_ngo_blocked(self, db_session, seed_data):
        from voice.livekit_agent import approve_payout

        # Change payout to a different NGO
        seed_data["payout"].ngo_id = 999
        db_session.commit()

        ctx = _make_ctx(user_id=3, name="NGO Mgr", role="NGO_ADMIN")
        with patch("voice.livekit_agent._get_db", return_value=db_session):
            result = json.loads(await approve_payout(ctx, payout_id=1))
        assert "error" in result
        assert "own NGO" in result["error"]

    async def test_sends_payout_status_card(self, db_session, seed_data):
        from voice.livekit_agent import approve_payout

        ctx = _make_ctx(user_id=1, role="SYSTEM_ADMIN")
        with patch("voice.livekit_agent._get_db", return_value=db_session):
            await approve_payout(ctx, payout_id=1)

        send_text = ctx.session.room_io.room.local_participant.send_text
        assert send_text.called
        card = json.loads(send_text.call_args[0][0])
        assert card["type"] == "payout_status"
        assert card["action"] == "approved"


class TestRejectPayout:
    async def test_reject_with_reason(self, db_session, seed_data):
        from voice.livekit_agent import reject_payout

        ctx = _make_ctx(user_id=1, role="SYSTEM_ADMIN")
        with patch("voice.livekit_agent._get_db", return_value=db_session):
            result = json.loads(await reject_payout(ctx, payout_id=1, reason="Incomplete docs"))

        assert result["success"] is True
        assert result["status"] == "rejected"

        payout = db_session.query(Payout).get(1)
        assert payout.status == "rejected"
        assert payout.rejection_reason == "Incomplete docs"

    async def test_anonymous_blocked(self, db_session, seed_data):
        from voice.livekit_agent import reject_payout

        ctx = _make_ctx(user_id="web_anonymous")
        with patch("voice.livekit_agent._get_db", return_value=db_session):
            result = json.loads(await reject_payout(ctx, payout_id=1, reason="test"))
        assert "error" in result


class TestCreateCampaign:
    async def test_ngo_admin_create(self, db_session, seed_data):
        from voice.livekit_agent import create_campaign

        ctx = _make_ctx(user_id=3, name="NGO Mgr", role="NGO_ADMIN")
        with patch("voice.livekit_agent._get_db", return_value=db_session):
            result = json.loads(await create_campaign(
                ctx,
                title="Solar Panels for Schools",
                description="Install solar panels in 5 rural schools",
                category="infrastructure",
                goal_amount_usd=25000.0,
                location_country="Kenya",
                location_region="Kisumu",
            ))

        assert result["success"] is True
        assert result["title"] == "Solar Panels for Schools"
        assert result["goal_usd"] == 25000.0

        # Verify in DB
        c = db_session.query(Campaign).filter(Campaign.title == "Solar Panels for Schools").first()
        assert c is not None
        assert c.ngo_id == 1
        assert c.location_country == "Kenya"
        assert c.location_region == "Kisumu"

    async def test_donor_cannot_create(self, db_session, seed_data):
        from voice.livekit_agent import create_campaign

        ctx = _make_ctx(user_id=2, role="DONOR")
        with patch("voice.livekit_agent._get_db", return_value=db_session):
            result = json.loads(await create_campaign(
                ctx, title="T", description="D", category="water", goal_amount_usd=100,
            ))
        assert "error" in result

    async def test_sends_campaign_card(self, db_session, seed_data):
        from voice.livekit_agent import create_campaign

        ctx = _make_ctx(user_id=3, name="NGO Mgr", role="NGO_ADMIN")
        with patch("voice.livekit_agent._get_db", return_value=db_session):
            await create_campaign(
                ctx, title="Test Camp", description="Testing campaign",
                category="health", goal_amount_usd=5000.0,
            )

        send_text = ctx.session.room_io.room.local_participant.send_text
        assert send_text.called
        card = json.loads(send_text.call_args[0][0])
        assert card["type"] == "campaign_card"
        assert card["just_created"] is True
        assert card["title"] == "Test Camp"

    async def test_anonymous_blocked(self, db_session, seed_data):
        from voice.livekit_agent import create_campaign

        ctx = _make_ctx(user_id="web_anonymous")
        with patch("voice.livekit_agent._get_db", return_value=db_session):
            result = json.loads(await create_campaign(
                ctx, title="T", description="D", category="water", goal_amount_usd=100,
            ))
        assert "error" in result
        assert "signed in" in result["error"]


# ── Tier 2: Action card helper tests ───────────────────────────


class TestSendActionCard:
    async def test_sends_json(self):
        from voice.livekit_agent import _send_action_card

        ctx = _make_ctx(user_id=1)
        card = {"type": "test", "data": 42}
        await _send_action_card(ctx, card)

        send = ctx.session.room_io.room.local_participant.send_text
        send.assert_called_once()
        payload = json.loads(send.call_args[0][0])
        assert payload["type"] == "test"
        assert send.call_args[1]["topic"] == "vbv.action"

    async def test_error_does_not_raise(self):
        """_send_action_card should swallow exceptions gracefully."""
        from voice.livekit_agent import _send_action_card

        ctx = _make_ctx(user_id=1)
        ctx.session.room_io.room.local_participant.send_text = AsyncMock(
            side_effect=RuntimeError("boom")
        )
        # Should NOT raise
        await _send_action_card(ctx, {"type": "test"})


# ── Tier 3: Ambient context tests ──────────────────────────────


class TestLoadAmbientContext:
    def test_admin_gets_pending_items(self, db_session, seed_data):
        from voice.livekit_agent import _load_ambient_context

        with patch("voice.livekit_agent._get_db", return_value=db_session):
            result = _load_ambient_context("1", "SYSTEM_ADMIN")

        assert "context_text" in result
        text = result["context_text"]
        # Should mention pending payouts and milestones
        assert "payout" in text.lower()
        assert "milestone" in text.lower()

        # Should have admin_summary card
        cards = result["cards"]
        assert len(cards) >= 1
        admin_card = cards[0]
        assert admin_card["type"] == "admin_summary"
        assert admin_card["pending_payouts"] == 1
        assert admin_card["pending_milestones"] == 1  # EVIDENCE_SUBMITTED
        assert admin_card["funded_milestones"] == 1   # VERIFIED

    def test_returning_donor_detection(self, db_session, seed_data):
        from voice.livekit_agent import _load_ambient_context

        with patch("voice.livekit_agent._get_db", return_value=db_session):
            result = _load_ambient_context("2", "DONOR")

        extra = result["extra_userdata"]
        assert extra["is_returning_donor"] is True
        assert extra["lifetime_donated_usd"] == 500.0
        assert "returning" in result["context_text"].lower() or "lifetime" in result["context_text"].lower()

    def test_first_time_user(self, db_session, seed_data):
        from voice.livekit_agent import _load_ambient_context

        # field agent (id=4) has no donor record
        with patch("voice.livekit_agent._get_db", return_value=db_session):
            result = _load_ambient_context("4", "FIELD_AGENT")

        text = result["context_text"]
        assert "active campaign" in text.lower()

    def test_anonymous_returns_empty(self, db_session, seed_data):
        from voice.livekit_agent import _load_ambient_context

        with patch("voice.livekit_agent._get_db", return_value=db_session):
            result = _load_ambient_context("web_anonymous", "DONOR")

        assert result["context_text"] == ""
        assert result["cards"] == []
        assert result["extra_userdata"] == {}

    def test_ngo_admin_gets_campaign_stats(self, db_session, seed_data):
        from voice.livekit_agent import _load_ambient_context

        with patch("voice.livekit_agent._get_db", return_value=db_session):
            result = _load_ambient_context("3", "NGO_ADMIN")

        text = result["context_text"]
        assert "active campaign" in text.lower()
        assert "$12,500" in text or "12500" in text or "12,500" in text

    def test_field_agent_pending_verifications(self, db_session, seed_data):
        from voice.livekit_agent import _load_ambient_context

        with patch("voice.livekit_agent._get_db", return_value=db_session):
            result = _load_ambient_context("4", "FIELD_AGENT")

        text = result["context_text"]
        assert "evidence" in text.lower() or "verification" in text.lower() or "milestone" in text.lower()


# ── Role gating tests ──────────────────────────────────────────


class TestRoleGating:
    """Verify that role-gated tools reject unauthorized roles."""

    @pytest.mark.parametrize("tool_name,required_roles,kwargs", [
        ("submit_milestone_evidence", ["NGO_ADMIN", "CAMPAIGN_CREATOR", "SYSTEM_ADMIN", "SUPER_ADMIN"],
         {"milestone_id": 2, "notes": "Done"}),
        ("verify_milestone", ["FIELD_AGENT", "SYSTEM_ADMIN", "SUPER_ADMIN"],
         {"milestone_id": 2, "trust_score": 85}),
        ("release_milestone_funds", ["SYSTEM_ADMIN", "SUPER_ADMIN"],
         {"milestone_id": 3}),
    ])
    async def test_donor_blocked(self, db_session, seed_data, tool_name, required_roles, kwargs):
        import voice.livekit_agent as agent
        tool_fn = getattr(agent, tool_name)

        ctx = _make_ctx(user_id=2, role="DONOR")

        # For milestone tools, we need to mock the handler too
        handler_mock = AsyncMock(return_value={"success": True})
        handler_path = {
            "submit_milestone_evidence": "voice.handlers.milestone_handler.submit_milestone_evidence",
            "verify_milestone": "voice.handlers.milestone_handler.verify_milestone",
            "release_milestone_funds": "voice.handlers.milestone_handler.release_milestone_funds",
        }.get(tool_name)

        with patch("voice.livekit_agent._get_db", return_value=db_session):
            if handler_path:
                with patch(handler_path, handler_mock):
                    result = json.loads(await tool_fn(ctx, **kwargs))
            else:
                result = json.loads(await tool_fn(ctx, **kwargs))

        assert "error" in result, f"DONOR should be blocked from {tool_name}"

    @pytest.mark.parametrize("tool_name,user_id,role,kwargs", [
        ("approve_payout", 1, "SYSTEM_ADMIN", {"payout_id": 1}),
        ("reject_payout", 1, "SYSTEM_ADMIN", {"payout_id": 1, "reason": "test"}),
    ])
    async def test_admin_allowed(self, db_session, seed_data, tool_name, user_id, role, kwargs):
        import voice.livekit_agent as agent
        tool_fn = getattr(agent, tool_name)

        ctx = _make_ctx(user_id=user_id, role=role)
        with patch("voice.livekit_agent._get_db", return_value=db_session):
            result = json.loads(await tool_fn(ctx, **kwargs))
        # Should succeed or at least not be a role error
        if "error" in result:
            assert "Only" not in result["error"], f"Admin should be allowed to {tool_name}"


# ── VBVAssistant class tests ───────────────────────────────────


class TestVBVAssistant:
    def test_default_construction(self):
        from voice.livekit_agent import VBVAssistant

        agent = VBVAssistant(user_name="Alice", user_role="DONOR")
        assert "Alice" in agent._instructions
        assert "DONOR" in agent._instructions

    def test_context_addendum(self):
        from voice.livekit_agent import VBVAssistant

        agent = VBVAssistant(
            user_name="Bob",
            user_role="SYSTEM_ADMIN",
            context_addendum="3 pending payouts, 2 milestones to verify.",
        )
        assert "SESSION CONTEXT" in agent._instructions
        assert "3 pending payouts" in agent._instructions

    def test_tools_registered(self):
        from voice.livekit_agent import VBVAssistant, ALL_TOOLS

        agent = VBVAssistant()
        # Agent should have all tools
        assert len(agent._tools) == len(ALL_TOOLS)
