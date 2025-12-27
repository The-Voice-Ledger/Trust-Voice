"""
LAB 6 STUDENT TEST SUITE
=========================

Welcome! This file contains tests for Lab 6: Voice Command Execution.

This test suite is designed to help you:
1. Verify each handler works correctly
2. Understand how intent routing works
3. Test entity validation
4. Verify multi-turn conversations
5. Practice debugging voice commands

STRUCTURE:
- Part 1: Command Router Tests (routing, validation)
- Part 2: Donor Handler Tests (search, donate, history)
- Part 3: NGO Handler Tests (create, withdraw, report)
- Part 4: General Handler Tests (help, greeting, language)
- Part 5: Integration Tests (complete workflows)

HOW TO RUN:
-----------
# Run all Lab 6 tests
pytest tests/LAB_06_STUDENT_TESTS.py -v

# Run specific test class
pytest tests/LAB_06_STUDENT_TESTS.py::TestSearchCampaigns -v

# Run single test
pytest tests/LAB_06_STUDENT_TESTS.py::TestSearchCampaigns::test_search_all_campaigns -v

# Run with detailed output
pytest tests/LAB_06_STUDENT_TESTS.py -v -s

PREREQUISITES:
--------------
- Lab 1-5 completed
- Database populated with test campaigns
- All services running
- pytest and pytest-asyncio installed:
  pip install pytest pytest-asyncio
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import models
from campaigns.models import Campaign, Donation, CampaignUpdate, ImpactReport, Base
from users.models import User

# Import handlers
from voice.command_router import (
    route_command,
    validate_entities,
    generate_clarification_question,
    REQUIRED_ENTITIES
)
from voice.handlers.donor_handlers import (
    handle_search_campaigns,
    handle_view_campaign_details,
    handle_make_donation,
    handle_donation_history,
    handle_campaign_updates,
    handle_impact_report
)
from voice.handlers.ngo_handlers import (
    handle_create_campaign,
    handle_withdraw_funds,
    handle_field_report,
    handle_ngo_dashboard
)
from voice.handlers.general_handlers import (
    handle_help,
    handle_greeting,
    handle_change_language,
    handle_unknown
)
from voice.context import (
    get_context,
    clear_context,
    store_search_results,
    get_search_results
)


# ============================================================================
# TEST DATABASE SETUP
# ============================================================================

@pytest.fixture
def db_session():
    """
    Create an in-memory test database.
    
    This fixture:
    1. Creates a fresh SQLite database in memory
    2. Creates all tables
    3. Populates with test data
    4. Yields the session for tests
    5. Cleans up after tests complete
    """
    print("\n📦 Setting up test database...")
    
    # Create in-memory database
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Add test data
    _setup_test_data(session)
    
    print("✅ Test database ready!")
    
    yield session
    
    session.close()
    print("🧹 Test database cleaned up")


def _setup_test_data(db):
    """
    Populate database with test users, campaigns, donations.
    
    Creates:
    - 2 donors (registered and guest)
    - 1 NGO organization
    - 3 campaigns (2 active, 1 completed)
    - 2 donations
    - 1 campaign update
    - 1 impact report
    """
    # ===== USERS =====
    
    # Donor 1 (Registered)
    donor = User(
        id="donor-123",
        email="donor@test.com",
        phone_number="+251911111111",
        full_name="Test Donor",
        user_type="donor",
        is_verified=True,
        preferred_language="en"
    )
    
    # Donor 2 (Guest - unregistered)
    guest_donor = User(
        id="guest-456",
        telegram_user_id="guest456",
        full_name="Guest User",
        user_type="donor",
        is_verified=False,
        preferred_language="en"
    )
    
    # NGO Organization
    ngo = User(
        id="ngo-789",
        email="ngo@test.com",
        phone_number="+251922222222",
        organization_name="Test NGO Foundation",
        user_type="ngo",
        is_verified=True,
        preferred_language="en",
        bank_account_number="1234567890"
    )
    
    db.add_all([donor, guest_donor, ngo])
    
    # ===== CAMPAIGNS =====
    
    # Campaign 1: Education (Active, partially funded)
    campaign1 = Campaign(
        id=1,
        ngo_id="ngo-789",
        title="Build School in Addis Ababa",
        description="Help us build a school for 200 children in need of education",
        category="education",
        goal_amount=50000,
        current_amount=15000,  # 30% funded
        location="Addis Ababa",
        status="active",
        is_approved=True,
        created_at=datetime.utcnow() - timedelta(days=10),
        end_date=datetime.utcnow() + timedelta(days=50)
    )
    
    # Campaign 2: Water (Active, urgent - ends soon)
    campaign2 = Campaign(
        id=2,
        ngo_id="ngo-789",
        title="Clean Water for Rural Villages",
        description="Provide clean water access to 500 families",
        category="water",
        goal_amount=30000,
        current_amount=25000,  # 83% funded - almost complete!
        location="Bahir Dar",
        status="active",
        is_approved=True,
        created_at=datetime.utcnow() - timedelta(days=50),
        end_date=datetime.utcnow() + timedelta(days=5)  # Urgent! Only 5 days left
    )
    
    # Campaign 3: Health (Completed)
    campaign3 = Campaign(
        id=3,
        ngo_id="ngo-789",
        title="Medical Supplies for Clinic",
        description="Essential medical supplies for rural health clinic",
        category="health",
        goal_amount=20000,
        current_amount=20000,  # 100% funded
        location="Gondar",
        status="completed",
        is_approved=True,
        created_at=datetime.utcnow() - timedelta(days=90),
        end_date=datetime.utcnow() - timedelta(days=10)
    )
    
    db.add_all([campaign1, campaign2, campaign3])
    
    # ===== DONATIONS =====
    
    # Donation 1: To education campaign
    donation1 = Donation(
        id=1,
        donor_id="donor-123",
        campaign_id=1,
        amount=500,
        currency="ETB",
        status="completed",
        payment_method="telebirr",
        anonymous=False,
        created_at=datetime.utcnow() - timedelta(days=5)
    )
    
    # Donation 2: To water campaign
    donation2 = Donation(
        id=2,
        donor_id="donor-123",
        campaign_id=2,
        amount=1000,
        currency="ETB",
        status="completed",
        payment_method="mpesa",
        anonymous=False,
        created_at=datetime.utcnow() - timedelta(days=3)
    )
    
    db.add_all([donation1, donation2])
    
    # ===== CAMPAIGN UPDATES =====
    
    # Update for campaign 1
    update = CampaignUpdate(
        id=1,
        campaign_id=1,
        title="Construction Started!",
        message="We've broken ground and construction is progressing well. Foundation is 50% complete. Thank you to all our generous donors!",
        created_at=datetime.utcnow() - timedelta(days=2)
    )
    
    db.add(update)
    
    # ===== IMPACT REPORTS =====
    
    # Impact report for completed campaign
    impact = ImpactReport(
        id=1,
        campaign_id=3,
        title="Clinic Successfully Supplied",
        summary="The clinic now has essential medical supplies and serves 500 patients per month. 3 doctors and 5 nurses are now able to provide quality care.",
        beneficiaries_reached=500,
        created_at=datetime.utcnow() - timedelta(days=8)
    )
    
    db.add(impact)
    
    # Commit all data
    db.commit()
    
    print("  ✓ Created 3 test users (1 donor, 1 guest, 1 NGO)")
    print("  ✓ Created 3 test campaigns (2 active, 1 completed)")
    print("  ✓ Created 2 test donations")
    print("  ✓ Created 1 campaign update")
    print("  ✓ Created 1 impact report")


# ============================================================================
# PART 1: COMMAND ROUTER TESTS
# ============================================================================

class TestCommandRouter:
    """
    Test the command router's core functionality.
    
    WHAT YOU'RE TESTING:
    - Intent routing to correct handlers
    - Entity validation
    - Missing entity detection
    - Clarification question generation
    """
    
    def test_required_entities_configuration(self):
        """
        TEST 1.1: Verify REQUIRED_ENTITIES is properly configured.
        
        LEARNING GOAL: Understand which intents require which entities.
        
        EXPECTED BEHAVIOR:
        - make_donation requires: amount, campaign_id
        - search_campaigns requires: nothing (all optional)
        - create_campaign requires: title, goal_amount, category
        """
        print("\n🧪 Test 1.1: Required entities configuration")
        
        # Check donation requirements
        donation_required = REQUIRED_ENTITIES["make_donation"]
        assert "amount" in donation_required
        assert "campaign_id" in donation_required
        print("  ✓ make_donation requires: amount, campaign_id")
        
        # Check search has no requirements
        search_required = REQUIRED_ENTITIES["search_campaigns"]
        assert len(search_required) == 0
        print("  ✓ search_campaigns has no required entities")
        
        # Check campaign creation requirements
        create_required = REQUIRED_ENTITIES["create_campaign"]
        assert "title" in create_required
        assert "goal_amount" in create_required
        assert "category" in create_required
        print("  ✓ create_campaign requires: title, goal_amount, category")
    
    def test_entity_validation_pass(self):
        """
        TEST 1.2: Test entity validation with all required entities present.
        
        LEARNING GOAL: Understand how the router validates entities.
        
        SCENARIO: User says "Donate 100 birr to campaign 1"
        Expected: Validation passes, no missing entities
        """
        print("\n🧪 Test 1.2: Entity validation (pass)")
        
        # Valid entities for donation
        is_valid, missing = validate_entities(
            intent="make_donation",
            entities={"amount": 100, "campaign_id": 1}
        )
        
        assert is_valid is True
        assert len(missing) == 0
        print("  ✓ Validation passed with all required entities")
    
    def test_entity_validation_fail(self):
        """
        TEST 1.3: Test entity validation with missing entities.
        
        LEARNING GOAL: Learn how the system handles incomplete commands.
        
        SCENARIO: User says "I want to donate 100" (no campaign specified)
        Expected: Validation fails, campaign_id is missing
        """
        print("\n🧪 Test 1.3: Entity validation (fail)")
        
        # Missing campaign_id
        is_valid, missing = validate_entities(
            intent="make_donation",
            entities={"amount": 100}  # No campaign_id
        )
        
        assert is_valid is False
        assert "campaign_id" in missing
        print("  ✓ Validation correctly detected missing entity: campaign_id")
    
    def test_clarification_question_generation(self):
        """
        TEST 1.4: Test clarification question generation.
        
        LEARNING GOAL: Learn how the bot asks for missing information.
        
        SCENARIO: User forgot to specify which campaign
        Expected: Bot asks "Which campaign would you like to donate to?"
        """
        print("\n🧪 Test 1.4: Clarification question generation")
        
        question = generate_clarification_question(
            intent="make_donation",
            missing_entities=["campaign_id"]
        )
        
        assert "campaign" in question.lower()
        print(f"  ✓ Generated question: \"{question}\"")
    
    @pytest.mark.asyncio
    async def test_route_to_handler(self, db_session):
        """
        TEST 1.5: Test routing intent to correct handler.
        
        LEARNING GOAL: Understand how intents map to handler functions.
        
        SCENARIO: User says "Help"
        Expected: Routes to help handler, returns help message
        """
        print("\n🧪 Test 1.5: Route to handler")
        
        result = await route_command(
            intent="help",
            entities={},
            user_id="donor-123",
            db=db_session,
            conversation_context={}
        )
        
        assert result["success"] is True
        assert "help" in result["message"].lower() or "can" in result["message"].lower()
        print("  ✓ Successfully routed 'help' intent to handler")
        print(f"  ℹ️  Response: {result['message'][:100]}...")
    
    @pytest.mark.asyncio
    async def test_missing_entity_clarification(self, db_session):
        """
        TEST 1.6: Test missing entity triggers clarification.
        
        LEARNING GOAL: See how the router handles incomplete commands.
        
        SCENARIO: User says "Donate 50" (no campaign)
        Expected: Router asks for campaign_id
        """
        print("\n🧪 Test 1.6: Missing entity clarification")
        
        result = await route_command(
            intent="make_donation",
            entities={"amount": 50},  # Missing campaign_id
            user_id="donor-123",
            db=db_session,
            conversation_context={}
        )
        
        assert result["success"] is False
        assert result["needs_clarification"] is True
        assert "campaign_id" in result["missing_entities"]
        print("  ✓ Router correctly requested clarification")
        print(f"  ℹ️  Clarification: {result['message']}")


# ============================================================================
# PART 2: DONOR HANDLER TESTS
# ============================================================================

class TestSearchCampaigns:
    """
    Test campaign search functionality.
    
    WHAT YOU'RE TESTING:
    - Search all campaigns
    - Filter by category
    - Filter by location
    - Filter by status (active/urgent/completed)
    - Handle no results
    """
    
    @pytest.mark.asyncio
    async def test_search_all_campaigns(self, db_session):
        """
        TEST 2.1: Search for all active campaigns.
        
        SCENARIO: User says "Show me campaigns"
        Expected: Returns 2 active campaigns
        """
        print("\n🧪 Test 2.1: Search all campaigns")
        
        result = await handle_search_campaigns(
            entities={},
            user_id="donor-123",
            db=db_session,
            context={}
        )
        
        assert result["success"] is True
        assert result["data"]["count"] == 2  # 2 active campaigns
        assert "Build School" in result["message"] or "Clean Water" in result["message"]
        print(f"  ✓ Found {result['data']['count']} active campaigns")
        print(f"  ℹ️  Response: {result['message'][:150]}...")
    
    @pytest.mark.asyncio
    async def test_search_by_category(self, db_session):
        """
        TEST 2.2: Search campaigns by category.
        
        SCENARIO: User says "Show me education campaigns"
        Expected: Returns only education campaign
        """
        print("\n🧪 Test 2.2: Search by category (education)")
        
        result = await handle_search_campaigns(
            entities={"category": "education"},
            user_id="donor-123",
            db=db_session,
            context={}
        )
        
        assert result["success"] is True
        assert result["data"]["count"] == 1
        campaigns = result["data"]["campaigns"]
        assert all(c["category"] == "education" for c in campaigns)
        print("  ✓ Filtered to education campaigns only")
    
    @pytest.mark.asyncio
    async def test_search_urgent_campaigns(self, db_session):
        """
        TEST 2.3: Search for urgent campaigns (ending soon or almost funded).
        
        SCENARIO: User says "Show me urgent campaigns"
        Expected: Returns water campaign (ends in 5 days)
        """
        print("\n🧪 Test 2.3: Search urgent campaigns")
        
        result = await handle_search_campaigns(
            entities={"status": "urgent"},
            user_id="donor-123",
            db=db_session,
            context={}
        )
        
        assert result["success"] is True
        assert result["data"]["count"] >= 1
        print(f"  ✓ Found {result['data']['count']} urgent campaign(s)")
    
    @pytest.mark.asyncio
    async def test_search_no_results(self, db_session):
        """
        TEST 2.4: Handle search with no matching campaigns.
        
        SCENARIO: User says "Show me space exploration campaigns"
        Expected: Helpful message, no results
        """
        print("\n🧪 Test 2.4: Search with no results")
        
        result = await handle_search_campaigns(
            entities={"category": "space"},  # No space campaigns
            user_id="donor-123",
            db=db_session,
            context={}
        )
        
        assert result["success"] is True
        assert result["data"]["count"] == 0
        assert "couldn't find" in result["message"].lower() or "no" in result["message"].lower()
        print("  ✓ Handled no results gracefully")


class TestViewCampaignDetails:
    """
    Test viewing detailed campaign information.
    
    WHAT YOU'RE TESTING:
    - View campaign details
    - Calculate progress percentage
    - Show donor count
    - Show days remaining
    - Handle non-existent campaigns
    """
    
    @pytest.mark.asyncio
    async def test_view_existing_campaign(self, db_session):
        """
        TEST 2.5: View details of existing campaign.
        
        SCENARIO: User says "Tell me about campaign 1"
        Expected: Returns full campaign details
        """
        print("\n🧪 Test 2.5: View campaign details")
        
        result = await handle_view_campaign_details(
            entities={"campaign_id": 1},
            user_id="donor-123",
            db=db_session,
            context={}
        )
        
        assert result["success"] is True
        campaign = result["data"]["campaign"]
        assert campaign["id"] == 1
        assert campaign["title"] == "Build School in Addis Ababa"
        assert campaign["progress_percent"] == 30.0  # 15000/50000 = 30%
        assert campaign["donor_count"] >= 1
        print("  ✓ Retrieved campaign details successfully")
        print(f"  ℹ️  Progress: {campaign['progress_percent']}%")
        print(f"  ℹ️  Donors: {campaign['donor_count']}")
    
    @pytest.mark.asyncio
    async def test_view_nonexistent_campaign(self, db_session):
        """
        TEST 2.6: Handle viewing non-existent campaign.
        
        SCENARIO: User says "Tell me about campaign 9999"
        Expected: Error message
        """
        print("\n🧪 Test 2.6: View non-existent campaign")
        
        result = await handle_view_campaign_details(
            entities={"campaign_id": 9999},
            user_id="donor-123",
            db=db_session,
            context={}
        )
        
        assert result["success"] is False
        assert "couldn't find" in result["message"].lower()
        print("  ✓ Handled missing campaign gracefully")


class TestMakeDonation:
    """
    Test donation creation and validation.
    
    WHAT YOU'RE TESTING:
    - Create valid donation
    - Validate minimum amount
    - Validate campaign exists and is active
    - Reject donations to completed campaigns
    - Anonymous donations
    """
    
    @pytest.mark.asyncio
    async def test_create_valid_donation(self, db_session):
        """
        TEST 2.7: Create a valid donation.
        
        SCENARIO: User says "Donate 100 birr to campaign 1"
        Expected: Donation created, payment link provided
        """
        print("\n🧪 Test 2.7: Create valid donation")
        
        result = await handle_make_donation(
            entities={"amount": 100, "campaign_id": 1},
            user_id="donor-123",
            db=db_session,
            context={}
        )
        
        assert result["success"] is True
        assert result["data"]["amount"] == 100
        assert result["data"]["campaign_id"] == 1
        assert result["data"]["status"] == "pending"
        assert "payment" in result["message"].lower()
        print("  ✓ Donation created successfully")
        print(f"  ℹ️  Donation ID: {result['data']['donation_id']}")
    
    @pytest.mark.asyncio
    async def test_donation_below_minimum(self, db_session):
        """
        TEST 2.8: Reject donation below minimum amount.
        
        SCENARIO: User says "Donate 5 birr" (below 10 birr minimum)
        Expected: Error message about minimum
        """
        print("\n🧪 Test 2.8: Reject below-minimum donation")
        
        result = await handle_make_donation(
            entities={"amount": 5, "campaign_id": 1},  # Below 10 minimum
            user_id="donor-123",
            db=db_session,
            context={}
        )
        
        assert result["success"] is False
        assert "minimum" in result["message"].lower()
        print("  ✓ Correctly rejected donation below minimum")
    
    @pytest.mark.asyncio
    async def test_donation_to_completed_campaign(self, db_session):
        """
        TEST 2.9: Reject donation to completed campaign.
        
        SCENARIO: User tries to donate to completed campaign 3
        Expected: Error message about campaign status
        """
        print("\n🧪 Test 2.9: Reject donation to completed campaign")
        
        result = await handle_make_donation(
            entities={"amount": 100, "campaign_id": 3},  # Completed campaign
            user_id="donor-123",
            db=db_session,
            context={}
        )
        
        assert result["success"] is False
        assert "no longer accepting" in result["message"].lower()
        print("  ✓ Correctly rejected donation to completed campaign")
    
    @pytest.mark.asyncio
    async def test_anonymous_donation(self, db_session):
        """
        TEST 2.10: Create anonymous donation.
        
        SCENARIO: User says "Donate 50 anonymously to campaign 1"
        Expected: Donation created with anonymous=True
        """
        print("\n🧪 Test 2.10: Create anonymous donation")
        
        result = await handle_make_donation(
            entities={"amount": 50, "campaign_id": 1, "anonymous": True},
            user_id="donor-123",
            db=db_session,
            context={}
        )
        
        assert result["success"] is True
        assert result["data"]["anonymous"] is True
        assert "anonymous" in result["message"].lower()
        print("  ✓ Anonymous donation created")


class TestDonationHistory:
    """
    Test donation history retrieval.
    
    WHAT YOU'RE TESTING:
    - View donation history
    - Calculate total donated
    - Handle users with no donations
    - Filter by period
    """
    
    @pytest.mark.asyncio
    async def test_get_donation_history(self, db_session):
        """
        TEST 2.11: View donation history for donor with donations.
        
        SCENARIO: User says "Show my donation history"
        Expected: Returns 2 donations totaling 1500 birr
        """
        print("\n🧪 Test 2.11: Get donation history")
        
        result = await handle_donation_history(
            entities={},
            user_id="donor-123",
            db=db_session,
            context={}
        )
        
        assert result["success"] is True
        assert result["data"]["count"] >= 2
        assert result["data"]["total_amount"] == 1500  # 500 + 1000
        assert result["data"]["completed_count"] == 2
        print(f"  ✓ Found {result['data']['count']} donations")
        print(f"  ℹ️  Total donated: {result['data']['total_amount']} birr")
    
    @pytest.mark.asyncio
    async def test_empty_donation_history(self, db_session):
        """
        TEST 2.12: Handle user with no donations.
        
        SCENARIO: Guest user with no donations says "My donations"
        Expected: Friendly message encouraging first donation
        """
        print("\n🧪 Test 2.12: Empty donation history")
        
        result = await handle_donation_history(
            entities={},
            user_id="guest-456",  # Guest user with no donations
            db=db_session,
            context={}
        )
        
        assert result["success"] is True
        assert result["data"]["count"] == 0
        assert "haven't made any" in result["message"].lower() or "no donations" in result["message"].lower()
        print("  ✓ Handled empty history gracefully")


# ============================================================================
# PART 3: NGO HANDLER TESTS
# ============================================================================

class TestCreateCampaign:
    """
    Test campaign creation by NGOs.
    
    WHAT YOU'RE TESTING:
    - Create valid campaign
    - Validate minimum/maximum goal
    - Validate category
    - Reject non-NGO users
    - Require verification
    """
    
    @pytest.mark.asyncio
    async def test_create_valid_campaign(self, db_session):
        """
        TEST 3.1: NGO creates a valid campaign.
        
        SCENARIO: NGO says "Create campaign School Books with goal 25000"
        Expected: Campaign created with pending_approval status
        """
        print("\n🧪 Test 3.1: Create valid campaign")
        
        result = await handle_create_campaign(
            entities={
                "title": "School Books Distribution",
                "goal_amount": 25000,
                "category": "education",
                "description": "Distribute books to 500 students"
            },
            user_id="ngo-789",
            db=db_session,
            context={}
        )
        
        assert result["success"] is True
        assert result["data"]["title"] == "School Books Distribution"
        assert result["data"]["status"] == "pending_approval"
        assert "pending approval" in result["message"].lower()
        print("  ✓ Campaign created successfully")
        print(f"  ℹ️  Campaign ID: {result['data']['campaign_id']}")
    
    @pytest.mark.asyncio
    async def test_create_campaign_below_minimum(self, db_session):
        """
        TEST 3.2: Reject campaign with goal below minimum.
        
        SCENARIO: NGO tries to create campaign with 500 birr goal (minimum is 1000)
        Expected: Error about minimum goal
        """
        print("\n🧪 Test 3.2: Reject below-minimum goal")
        
        result = await handle_create_campaign(
            entities={
                "title": "Small Campaign",
                "goal_amount": 500,  # Below 1000 minimum
                "category": "education"
            },
            user_id="ngo-789",
            db=db_session,
            context={}
        )
        
        assert result["success"] is False
        assert "minimum" in result["message"].lower()
        print("  ✓ Rejected campaign with below-minimum goal")
    
    @pytest.mark.asyncio
    async def test_create_campaign_invalid_category(self, db_session):
        """
        TEST 3.3: Reject campaign with invalid category.
        
        SCENARIO: NGO tries invalid category "space exploration"
        Expected: Error listing valid categories
        """
        print("\n🧪 Test 3.3: Reject invalid category")
        
        result = await handle_create_campaign(
            entities={
                "title": "Test Campaign",
                "goal_amount": 10000,
                "category": "invalid_category"
            },
            user_id="ngo-789",
            db=db_session,
            context={}
        )
        
        assert result["success"] is False
        assert "valid category" in result["message"].lower()
        print("  ✓ Rejected invalid category")
    
    @pytest.mark.asyncio
    async def test_create_campaign_as_donor(self, db_session):
        """
        TEST 3.4: Reject campaign creation by non-NGO user.
        
        SCENARIO: Donor tries to create a campaign
        Expected: Error - only NGOs can create campaigns
        """
        print("\n🧪 Test 3.4: Reject campaign creation by donor")
        
        result = await handle_create_campaign(
            entities={
                "title": "Test Campaign",
                "goal_amount": 10000,
                "category": "education"
            },
            user_id="donor-123",  # Donor, not NGO
            db=db_session,
            context={}
        )
        
        assert result["success"] is False
        assert "only" in result["message"].lower() and "ngo" in result["message"].lower()
        print("  ✓ Correctly rejected non-NGO user")


class TestWithdrawFunds:
    """
    Test NGO fund withdrawal.
    
    WHAT YOU'RE TESTING:
    - Create valid withdrawal
    - Check sufficient balance
    - Validate minimum withdrawal
    - Reject non-NGO users
    """
    
    @pytest.mark.asyncio
    async def test_withdraw_valid_amount(self, db_session):
        """
        TEST 3.5: NGO withdraws valid amount.
        
        SCENARIO: NGO says "Withdraw 5000 from campaign 1"
        Expected: Withdrawal request created
        """
        print("\n🧪 Test 3.5: Create valid withdrawal")
        
        result = await handle_withdraw_funds(
            entities={"amount": 5000, "campaign_id": 1},
            user_id="ngo-789",
            db=db_session,
            context={}
        )
        
        assert result["success"] is True
        assert result["data"]["amount"] == 5000
        assert result["data"]["status"] == "pending"
        assert "3 to 5 business days" in result["message"]
        print("  ✓ Withdrawal request created")
        print(f"  ℹ️  Available balance: {result['data']['available_balance']} birr")
    
    @pytest.mark.asyncio
    async def test_withdraw_insufficient_funds(self, db_session):
        """
        TEST 3.6: Reject withdrawal exceeding balance.
        
        SCENARIO: NGO tries to withdraw 50000 (more than available)
        Expected: Error about insufficient funds
        """
        print("\n🧪 Test 3.6: Reject insufficient funds")
        
        result = await handle_withdraw_funds(
            entities={"amount": 50000, "campaign_id": 1},  # Campaign 1 only has 15000
            user_id="ngo-789",
            db=db_session,
            context={}
        )
        
        assert result["success"] is False
        assert "insufficient" in result["message"].lower()
        print("  ✓ Rejected withdrawal exceeding balance")


# ============================================================================
# PART 4: GENERAL HANDLER TESTS
# ============================================================================

class TestGeneralHandlers:
    """
    Test general intent handlers.
    
    WHAT YOU'RE TESTING:
    - Help command (personalized)
    - Greeting response
    - Language change
    - Unknown intent handling
    """
    
    @pytest.mark.asyncio
    async def test_help_donor(self, db_session):
        """
        TEST 4.1: Help command for donor.
        
        SCENARIO: Donor says "Help"
        Expected: Donor-specific help menu
        """
        print("\n🧪 Test 4.1: Help for donor")
        
        result = await handle_help(
            entities={},
            user_id="donor-123",
            db=db_session,
            context={}
        )
        
        assert result["success"] is True
        assert "search" in result["message"].lower() or "donate" in result["message"].lower()
        assert result["data"]["user_type"] == "donor"
        print("  ✓ Provided donor-specific help")
        print(f"  ℹ️  Response: {result['message'][:150]}...")
    
    @pytest.mark.asyncio
    async def test_help_ngo(self, db_session):
        """
        TEST 4.2: Help command for NGO.
        
        SCENARIO: NGO says "Help"
        Expected: NGO-specific help menu
        """
        print("\n🧪 Test 4.2: Help for NGO")
        
        result = await handle_help(
            entities={},
            user_id="ngo-789",
            db=db_session,
            context={}
        )
        
        assert result["success"] is True
        assert "create" in result["message"].lower() or "campaign" in result["message"].lower()
        assert result["data"]["user_type"] == "ngo"
        print("  ✓ Provided NGO-specific help")
    
    @pytest.mark.asyncio
    async def test_greeting(self, db_session):
        """
        TEST 4.3: Greeting response.
        
        SCENARIO: User says "Hello"
        Expected: Personalized greeting with name
        """
        print("\n🧪 Test 4.3: Greeting")
        
        result = await handle_greeting(
            entities={},
            user_id="donor-123",
            db=db_session,
            context={}
        )
        
        assert result["success"] is True
        assert "hello" in result["message"].lower() or "hi" in result["message"].lower()
        assert "Test Donor" in result["message"] or "donor" in result["message"].lower()
        print("  ✓ Greeted user by name")
    
    @pytest.mark.asyncio
    async def test_change_language_to_amharic(self, db_session):
        """
        TEST 4.4: Change language to Amharic.
        
        SCENARIO: User says "Switch to Amharic"
        Expected: Language changed, confirmation in Amharic
        """
        print("\n🧪 Test 4.4: Change to Amharic")
        
        result = await handle_change_language(
            entities={"language": "amharic"},
            user_id="donor-123",
            db=db_session,
            context={}
        )
        
        assert result["success"] is True
        assert result["data"]["language"] == "am"
        # Response should contain Amharic text
        assert "እሺ" in result["message"] or "አማርኛ" in result["message"]
        print("  ✓ Language changed to Amharic")
    
    @pytest.mark.asyncio
    async def test_unknown_intent(self, db_session):
        """
        TEST 4.5: Handle unknown intent.
        
        SCENARIO: User says something unrecognized
        Expected: Helpful suggestions
        """
        print("\n🧪 Test 4.5: Unknown intent")
        
        result = await handle_unknown(
            entities={},
            user_id="donor-123",
            db=db_session,
            context={}
        )
        
        assert result["success"] is True
        assert "not sure" in result["message"].lower() or "help" in result["message"].lower()
        print("  ✓ Provided helpful suggestions for unknown intent")


# ============================================================================
# PART 5: CONTEXT & INTEGRATION TESTS
# ============================================================================

class TestConversationContext:
    """
    Test conversation context management.
    
    WHAT YOU'RE TESTING:
    - Store and retrieve search results
    - Store current campaign
    - Context expiration
    - Multi-turn workflows
    """
    
    def test_store_and_retrieve_search_results(self):
        """
        TEST 5.1: Store search results in context.
        
        SCENARIO: User searches, then says "number 1"
        Expected: Context remembers search results
        """
        print("\n🧪 Test 5.1: Store search results")
        
        user_id = "context-test-1"
        clear_context(user_id)
        
        # Store results
        campaign_ids = [1, 2, 3]
        store_search_results(user_id, campaign_ids)
        
        # Retrieve results
        retrieved = get_search_results(user_id)
        
        assert retrieved == campaign_ids
        print("  ✓ Context stored and retrieved search results")
    
    def test_context_independence(self):
        """
        TEST 5.2: Each user has independent context.
        
        SCENARIO: Two users search different campaigns
        Expected: Each user's context is separate
        """
        print("\n🧪 Test 5.2: Context independence")
        
        user1 = "context-test-2"
        user2 = "context-test-3"
        clear_context(user1)
        clear_context(user2)
        
        # User 1 searches
        store_search_results(user1, [1, 2])
        
        # User 2 searches
        store_search_results(user2, [3, 4])
        
        # Verify independence
        results1 = get_search_results(user1)
        results2 = get_search_results(user2)
        
        assert results1 == [1, 2]
        assert results2 == [3, 4]
        print("  ✓ Each user has independent context")


class TestEndToEndWorkflows:
    """
    Test complete user workflows from start to finish.
    
    WHAT YOU'RE TESTING:
    - Search → View → Donate workflow
    - Create campaign → Report → Withdraw workflow
    - Context preservation across multiple turns
    """
    
    @pytest.mark.asyncio
    async def test_donor_workflow_search_to_donation(self, db_session):
        """
        TEST 5.3: Complete donor workflow.
        
        WORKFLOW:
        1. Search for education campaigns
        2. View campaign 1 details
        3. Make donation to campaign 1
        4. Check donation history
        
        Expected: All steps succeed
        """
        print("\n🧪 Test 5.3: Complete donor workflow")
        
        user_id = "workflow-donor"
        clear_context(user_id)
        
        # Step 1: Search
        print("  1️⃣  Search education campaigns...")
        result1 = await route_command(
            intent="search_campaigns",
            entities={"category": "education"},
            user_id=user_id,
            db=db_session,
            conversation_context=get_context(user_id)
        )
        assert result1["success"] is True
        campaign_id = result1["data"]["campaigns"][0]["id"]
        print(f"     ✓ Found campaign {campaign_id}")
        
        # Step 2: View details
        print("  2️⃣  View campaign details...")
        result2 = await route_command(
            intent="view_campaign_details",
            entities={"campaign_id": campaign_id},
            user_id=user_id,
            db=db_session,
            conversation_context=get_context(user_id)
        )
        assert result2["success"] is True
        print("     ✓ Viewed details")
        
        # Step 3: Donate
        print("  3️⃣  Make donation...")
        result3 = await route_command(
            intent="make_donation",
            entities={"amount": 250, "campaign_id": campaign_id},
            user_id=user_id,
            db=db_session,
            conversation_context=get_context(user_id)
        )
        assert result3["success"] is True
        print(f"     ✓ Donated {result3['data']['amount']} birr")
        
        # Step 4: Check history
        print("  4️⃣  Check donation history...")
        result4 = await route_command(
            intent="donation_history",
            entities={},
            user_id=user_id,
            db=db_session,
            conversation_context=get_context(user_id)
        )
        assert result4["success"] is True
        print(f"     ✓ History shows {result4['data']['count']} donation(s)")
        
        print("  🎉 Complete workflow successful!")
    
    @pytest.mark.asyncio
    async def test_ngo_workflow_create_to_withdraw(self, db_session):
        """
        TEST 5.4: Complete NGO workflow.
        
        WORKFLOW:
        1. View dashboard
        2. Create new campaign
        3. Submit field report
        4. Request withdrawal
        
        Expected: All steps succeed
        """
        print("\n🧪 Test 5.4: Complete NGO workflow")
        
        user_id = "ngo-789"
        clear_context(user_id)
        
        # Step 1: Dashboard
        print("  1️⃣  View dashboard...")
        result1 = await route_command(
            intent="ngo_dashboard",
            entities={},
            user_id=user_id,
            db=db_session,
            conversation_context=get_context(user_id)
        )
        assert result1["success"] is True
        print(f"     ✓ Total campaigns: {result1['data']['total_campaigns']}")
        print(f"     ℹ️  Total raised: {result1['data']['total_raised']} birr")
        
        # Step 2: Create campaign
        print("  2️⃣  Create new campaign...")
        result2 = await route_command(
            intent="create_campaign",
            entities={
                "title": "Workflow Test Campaign",
                "goal_amount": 15000,
                "category": "health"
            },
            user_id=user_id,
            db=db_session,
            conversation_context=get_context(user_id)
        )
        assert result2["success"] is True
        new_campaign_id = result2["data"]["campaign_id"]
        print(f"     ✓ Created campaign {new_campaign_id}")
        
        # Step 3: Field report (on existing campaign)
        print("  3️⃣  Submit field report...")
        result3 = await route_command(
            intent="field_report",
            entities={
                "campaign_id": 1,
                "description": "Work progressing well. Foundation 75% complete."
            },
            user_id=user_id,
            db=db_session,
            conversation_context=get_context(user_id)
        )
        assert result3["success"] is True
        print("     ✓ Field report submitted")
        
        # Step 4: Withdraw funds
        print("  4️⃣  Request withdrawal...")
        result4 = await route_command(
            intent="withdraw_funds",
            entities={"amount": 3000, "campaign_id": 1},
            user_id=user_id,
            db=db_session,
            conversation_context=get_context(user_id)
        )
        assert result4["success"] is True
        print(f"     ✓ Withdrawal requested: {result4['data']['amount']} birr")
        
        print("  🎉 Complete workflow successful!")


# ============================================================================
# TEST SUMMARY HELPER
# ============================================================================

def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """
    Print a nice summary after all tests run.
    """
    print("\n" + "=" * 80)
    print("LAB 6 TEST SUMMARY")
    print("=" * 80)
    
    passed = len([i for i in terminalreporter.stats.get('passed', [])])
    failed = len([i for i in terminalreporter.stats.get('failed', [])])
    skipped = len([i for i in terminalreporter.stats.get('skipped', [])])
    total = passed + failed + skipped
    
    if passed == total:
        print("🎉 CONGRATULATIONS! All tests passed!")
        print("✅ Your Lab 6 implementation is working correctly!")
        print("\nYou have successfully:")
        print("  ✓ Implemented command routing")
        print("  ✓ Created all 14 intent handlers")
        print("  ✓ Added entity validation")
        print("  ✓ Implemented context management")
        print("  ✓ Tested complete user workflows")
        print("\n🎓 You're ready to move on to Lab 7!")
    elif failed > 0:
        print(f"⚠️  {failed} test(s) failed")
        print("\nReview the failures above and:")
        print("  1. Check handler implementation")
        print("  2. Verify entity validation logic")
        print("  3. Ensure database queries are correct")
        print("  4. Test with manual Telegram commands")
        print("\n💡 Run specific failed tests with:")
        print("   pytest tests/LAB_06_STUDENT_TESTS.py::TestClassName::test_name -v")
    
    print("=" * 80 + "\n")


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════════════════╗
║                      LAB 6 STUDENT TEST SUITE                           ║
║                   Voice Command Execution Tests                         ║
╚══════════════════════════════════════════════════════════════════════════╝

Running comprehensive tests for Lab 6...
    """)
    
    pytest.main([__file__, "-v", "-s"])
