"""
Integration tests for Lab 3: Payment Processing and Donation Management

Tests donation creation, payment processing, and webhook handling.
"""

import pytest
from fastapi.testclient import TestClient
from main import app
import random
import string
from decimal import Decimal

client = TestClient(app)


# Helper functions
def random_string(length=8):
    """Generate random alphanumeric string."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def random_phone(country_code="+254", digits=9):
    """Generate valid E.164 phone number."""
    number = ''.join(random.choices(string.digits, k=digits))
    return f"{country_code}{number}"


# Test Fixtures - Create required data
@pytest.fixture
def test_ngo():
    """Create a test NGO."""
    response = client.post("/ngos/", json={
        "name": f"Test NGO {random_string()}",
        "description": "Test NGO for donation tests",
        "contact_email": f"test{random_string()}@example.com",
        "contact_phone": random_phone(),
        "website_url": f"https://test{random_string()}.org",
        "blockchain_wallet_address": "0x1234567890123456789012345678901234567890",
        "country_code": "KE"
    })
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def test_campaign(test_ngo):
    """Create a test campaign."""
    response = client.post("/campaigns/", json={
        "ngo_id": test_ngo["id"],
        "title": f"Test Campaign {random_string()}",
        "description": "Test campaign for donation tests",
        "goal_amount_usd": 10000.00,
        "campaign_type": "general",
        "status": "active"
    })
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def test_donor():
    """Create a test donor."""
    phone = random_phone()
    response = client.post("/donors/", json={
        "phone_number": phone,
        "preferred_language": "en",
        "first_name": "Test",
        "last_name": "Donor"
    })
    assert response.status_code == 201
    return response.json()


# ============================================================================
# Donation Creation Tests
# ============================================================================

class TestDonationCreation:
    
    def test_create_mpesa_donation(self, test_donor, test_campaign):
        """Test creating a donation with M-Pesa payment method."""
        response = client.post("/donations/", json={
            "donor_id": test_donor["id"],
            "campaign_id": test_campaign["id"],
            "amount": 100.00,
            "currency": "USD",
            "payment_method": "mpesa",
            "phone_number": test_donor["phone_number"]
        })
        
        assert response.status_code == 201
        data = response.json()
        assert data["donor_id"] == test_donor["id"]
        assert data["campaign_id"] == test_campaign["id"]
        assert float(data["amount"]) == 100.00
        assert data["currency"] == "USD"
        assert data["payment_method"] == "mpesa"
        assert data["status"] in ["pending", "processing"]
        assert "id" in data
        assert "created_at" in data
    
    def test_create_stripe_donation(self, test_donor, test_campaign):
        """Test creating a donation with Stripe payment method."""
        response = client.post("/donations/", json={
            "donor_id": test_donor["id"],
            "campaign_id": test_campaign["id"],
            "amount": 250.00,
            "currency": "USD",
            "payment_method": "stripe",
            "stripe_payment_method_id": "pm_test_123456"
        })
        
        assert response.status_code == 201
        data = response.json()
        assert data["payment_method"] == "stripe"
        assert float(data["amount"]) == 250.00
        assert data["status"] in ["pending", "processing"]
    
    def test_create_crypto_donation(self, test_donor, test_campaign):
        """Test creating a donation with cryptocurrency."""
        response = client.post("/donations/", json={
            "donor_id": test_donor["id"],
            "campaign_id": test_campaign["id"],
            "amount": 1000.00,
            "currency": "USD",
            "payment_method": "crypto",
            "blockchain_wallet_address": "0xAbCdEf1234567890AbCdEf1234567890AbCdEf12"
        })
        
        assert response.status_code == 201
        data = response.json()
        assert data["payment_method"] == "crypto"
        assert float(data["amount"]) == 1000.00
    
    def test_donation_invalid_donor(self, test_campaign):
        """Test donation creation with non-existent donor."""
        response = client.post("/donations/", json={
            "donor_id": 999999,
            "campaign_id": test_campaign["id"],
            "amount": 100.00,
            "currency": "USD",
            "payment_method": "mpesa",
            "phone_number": "+254712345678"
        })
        
        assert response.status_code == 404
        assert "donor" in response.json()["detail"].lower()
    
    def test_donation_invalid_campaign(self, test_donor):
        """Test donation creation with non-existent campaign."""
        response = client.post("/donations/", json={
            "donor_id": test_donor["id"],
            "campaign_id": 999999,
            "amount": 100.00,
            "currency": "USD",
            "payment_method": "mpesa",
            "phone_number": test_donor["phone_number"]
        })
        
        assert response.status_code == 404
        assert "campaign" in response.json()["detail"].lower()
    
    def test_donation_inactive_campaign(self, test_donor, test_ngo):
        """Test donation to inactive campaign."""
        # Create paused campaign
        campaign_response = client.post("/campaigns/", json={
            "ngo_id": test_ngo["id"],
            "title": f"Paused Campaign {random_string()}",
            "description": "This campaign is paused",
            "goal_amount_usd": 5000.00,
            "status": "paused"
        })
        campaign = campaign_response.json()
        
        # Try to donate
        response = client.post("/donations/", json={
            "donor_id": test_donor["id"],
            "campaign_id": campaign["id"],
            "amount": 100.00,
            "currency": "USD",
            "payment_method": "mpesa",
            "phone_number": test_donor["phone_number"]
        })
        
        assert response.status_code == 400
        assert "not accepting donations" in response.json()["detail"].lower()
    
    def test_mpesa_without_phone(self, test_donor, test_campaign):
        """Test M-Pesa donation without phone number."""
        response = client.post("/donations/", json={
            "donor_id": test_donor["id"],
            "campaign_id": test_campaign["id"],
            "amount": 100.00,
            "currency": "USD",
            "payment_method": "mpesa"
            # Missing phone_number
        })
        
        assert response.status_code == 400
        assert "phone_number" in response.json()["detail"].lower()
    
    def test_stripe_without_payment_method(self, test_donor, test_campaign):
        """Test Stripe donation without payment method ID."""
        response = client.post("/donations/", json={
            "donor_id": test_donor["id"],
            "campaign_id": test_campaign["id"],
            "amount": 100.00,
            "currency": "USD",
            "payment_method": "stripe"
            # Missing stripe_payment_method_id
        })
        
        assert response.status_code == 400
        assert "payment_method_id" in response.json()["detail"].lower()
    
    def test_crypto_without_wallet(self, test_donor, test_campaign):
        """Test crypto donation without wallet address."""
        response = client.post("/donations/", json={
            "donor_id": test_donor["id"],
            "campaign_id": test_campaign["id"],
            "amount": 100.00,
            "currency": "USD",
            "payment_method": "crypto"
            # Missing blockchain_wallet_address
        })
        
        assert response.status_code == 400
        assert "wallet" in response.json()["detail"].lower()
    
    def test_donation_with_message(self, test_donor, test_campaign):
        """Test donation with donor message."""
        response = client.post("/donations/", json={
            "donor_id": test_donor["id"],
            "campaign_id": test_campaign["id"],
            "amount": 100.00,
            "currency": "USD",
            "payment_method": "mpesa",
            "phone_number": test_donor["phone_number"],
            "donor_message": "Keep up the great work!"
        })
        
        assert response.status_code == 201
        data = response.json()
        assert data["donor_message"] == "Keep up the great work!"
    
    def test_anonymous_donation(self, test_donor, test_campaign):
        """Test anonymous donation."""
        response = client.post("/donations/", json={
            "donor_id": test_donor["id"],
            "campaign_id": test_campaign["id"],
            "amount": 100.00,
            "currency": "USD",
            "payment_method": "stripe",
            "stripe_payment_method_id": "pm_test_anon",
            "is_anonymous": True
        })
        
        assert response.status_code == 201
        data = response.json()
        assert data["is_anonymous"] == True


# ============================================================================
# Donation Retrieval Tests
# ============================================================================

class TestDonationRetrieval:
    
    def test_get_donation_by_id(self, test_donor, test_campaign):
        """Test retrieving donation by ID."""
        # Create donation
        create_response = client.post("/donations/", json={
            "donor_id": test_donor["id"],
            "campaign_id": test_campaign["id"],
            "amount": 100.00,
            "currency": "USD",
            "payment_method": "mpesa",
            "phone_number": test_donor["phone_number"]
        })
        donation_id = create_response.json()["id"]
        
        # Get donation
        response = client.get(f"/donations/{donation_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == donation_id
        assert data["donor_id"] == test_donor["id"]
    
    def test_get_nonexistent_donation(self):
        """Test retrieving non-existent donation."""
        response = client.get("/donations/999999")
        
        assert response.status_code == 404
    
    def test_get_donor_donations(self, test_donor, test_campaign):
        """Test retrieving all donations by a donor."""
        # Create multiple donations
        for i in range(3):
            client.post("/donations/", json={
                "donor_id": test_donor["id"],
                "campaign_id": test_campaign["id"],
                "amount": 100.00 * (i + 1),
                "currency": "USD",
                "payment_method": "mpesa",
                "phone_number": test_donor["phone_number"]
            })
        
        # Get donor donations
        response = client.get(f"/donations/donor/{test_donor['id']}")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 3
        # All should be from this donor
        for donation in data:
            assert donation["donor_id"] == test_donor["id"]
    
    def test_get_campaign_donations(self, test_donor, test_campaign):
        """Test retrieving all donations for a campaign."""
        # Create multiple donations
        for i in range(2):
            client.post("/donations/", json={
                "donor_id": test_donor["id"],
                "campaign_id": test_campaign["id"],
                "amount": 50.00,
                "currency": "USD",
                "payment_method": "stripe",
                "stripe_payment_method_id": f"pm_test_{i}"
            })
        
        # Get campaign donations
        response = client.get(f"/donations/campaign/{test_campaign['id']}")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2
        # All should be for this campaign
        for donation in data:
            assert donation["campaign_id"] == test_campaign["id"]
    
    def test_list_donations_with_filters(self):
        """Test listing donations with status and method filters."""
        # Test status filter
        response = client.get("/donations/?status=completed")
        assert response.status_code == 200
        data = response.json()
        for donation in data:
            assert donation["status"] == "completed"
        
        # Test payment method filter
        response = client.get("/donations/?payment_method=mpesa")
        assert response.status_code == 200
        data = response.json()
        for donation in data:
            assert donation["payment_method"] == "mpesa"
    
    def test_donations_pagination(self):
        """Test donation list pagination."""
        response = client.get("/donations/?skip=0&limit=5")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 5


# ============================================================================
# Donation Status Update Tests
# ============================================================================

class TestDonationStatusUpdate:
    
    def test_complete_donation(self, test_donor, test_campaign):
        """Test marking donation as completed."""
        # Create donation
        create_response = client.post("/donations/", json={
            "donor_id": test_donor["id"],
            "campaign_id": test_campaign["id"],
            "amount": 500.00,
            "currency": "USD",
            "payment_method": "mpesa",
            "phone_number": test_donor["phone_number"]
        })
        donation_id = create_response.json()["id"]
        
        # Get initial campaign amount
        campaign_response = client.get(f"/campaigns/{test_campaign['id']}")
        initial_amount = float(campaign_response.json()["raised_amount_usd"])
        
        # Mark as completed
        update_response = client.patch(f"/donations/{donation_id}/status", json={
            "status": "completed",
            "payment_intent_id": "MPESA_TEST_123456"
        })
        
        assert update_response.status_code == 200
        data = update_response.json()
        assert data["status"] == "completed"
        assert data["payment_intent_id"] == "MPESA_TEST_123456"
        
        # Verify campaign amount increased
        campaign_response = client.get(f"/campaigns/{test_campaign['id']}")
        new_amount = float(campaign_response.json()["raised_amount_usd"])
        assert new_amount == initial_amount + 500.00
    
    def test_fail_donation(self, test_donor, test_campaign):
        """Test marking donation as failed."""
        # Create donation
        create_response = client.post("/donations/", json={
            "donor_id": test_donor["id"],
            "campaign_id": test_campaign["id"],
            "amount": 100.00,
            "currency": "USD",
            "payment_method": "stripe",
            "stripe_payment_method_id": "pm_test_fail"
        })
        donation_id = create_response.json()["id"]
        
        # Get initial campaign amount
        campaign_response = client.get(f"/campaigns/{test_campaign['id']}")
        initial_amount = float(campaign_response.json()["raised_amount_usd"])
        
        # Mark as failed
        update_response = client.patch(f"/donations/{donation_id}/status", json={
            "status": "failed"
        })
        
        assert update_response.status_code == 200
        data = update_response.json()
        assert data["status"] == "failed"
        
        # Verify campaign amount didn't change
        campaign_response = client.get(f"/campaigns/{test_campaign['id']}")
        new_amount = float(campaign_response.json()["raised_amount_usd"])
        assert new_amount == initial_amount


# ============================================================================
# Webhook Tests
# ============================================================================

class TestWebhooks:
    
    def test_webhook_health(self):
        """Test webhook health check endpoint."""
        response = client.get("/webhooks/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "webhooks"
    
    def test_mpesa_callback_success(self, test_donor, test_campaign):
        """Test M-Pesa callback with successful payment."""
        # Create donation
        create_response = client.post("/donations/", json={
            "donor_id": test_donor["id"],
            "campaign_id": test_campaign["id"],
            "amount": 100.00,
            "currency": "USD",
            "payment_method": "mpesa",
            "phone_number": test_donor["phone_number"]
        })
        donation_id = create_response.json()["id"]
        checkout_request_id = create_response.json()["payment_intent_id"]
        
        # Simulate M-Pesa callback
        callback_payload = {
            "Body": {
                "stkCallback": {
                    "MerchantRequestID": "mock_merchant_123",
                    "CheckoutRequestID": checkout_request_id,
                    "ResultCode": 0,
                    "ResultDesc": "The service request is processed successfully.",
                    "CallbackMetadata": {
                        "Item": [
                            {"Name": "Amount", "Value": 100.00},
                            {"Name": "MpesaReceiptNumber", "Value": "TEST_RECEIPT_123"},
                            {"Name": "TransactionDate", "Value": 20211221101500},
                            {"Name": "PhoneNumber", "Value": 254712345678}
                        ]
                    }
                }
            }
        }
        
        response = client.post("/webhooks/mpesa", json=callback_payload)
        
        assert response.status_code == 200
        assert response.json()["ResultCode"] == 0
        
        # Verify donation was marked as completed
        donation_response = client.get(f"/donations/{donation_id}")
        assert donation_response.json()["status"] == "completed"
    
    def test_mpesa_callback_failure(self, test_donor, test_campaign):
        """Test M-Pesa callback with failed payment."""
        # Create donation
        create_response = client.post("/donations/", json={
            "donor_id": test_donor["id"],
            "campaign_id": test_campaign["id"],
            "amount": 100.00,
            "currency": "USD",
            "payment_method": "mpesa",
            "phone_number": test_donor["phone_number"]
        })
        donation_id = create_response.json()["id"]
        checkout_request_id = create_response.json()["payment_intent_id"]
        
        # Simulate failed M-Pesa callback
        callback_payload = {
            "Body": {
                "stkCallback": {
                    "MerchantRequestID": "mock_merchant_456",
                    "CheckoutRequestID": checkout_request_id,
                    "ResultCode": 1032,
                    "ResultDesc": "Request cancelled by user"
                }
            }
        }
        
        response = client.post("/webhooks/mpesa", json=callback_payload)
        
        assert response.status_code == 200
        
        # Verify donation was marked as failed
        donation_response = client.get(f"/donations/{donation_id}")
        assert donation_response.json()["status"] == "failed"
