"""
Integration tests for Lab 2 endpoints
Tests campaign, donor, and NGO management APIs
"""
import pytest
import random
import string
from fastapi.testclient import TestClient

from main import app

# Use the actual PostgreSQL database for tests
client = TestClient(app)


def random_string(length=8):
    """Generate random string for unique test data"""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))


def random_phone(country_code, digits=9):
    """Generate valid random phone number"""
    return f"+{country_code}{''.join(random.choices(string.digits, k=digits))}"


# ==========================================
# NGO Management Tests
# ==========================================

class TestNGOEndpoints:
    """Test NGO CRUD operations"""
    
    def test_create_ngo(self):
        """Test creating a new NGO"""
        unique_name = f"Test NGO {random_string()}"
        response = client.post(
            "/ngos/",
            json={
                "name": unique_name,
                "description": "Providing clean water to rural communities",
                "website_url": "https://waterforallkenya.org",
                "contact_email": "contact@waterforallkenya.org",
                "blockchain_wallet_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f01234"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == unique_name
        assert data["description"] == "Providing clean water to rural communities"
        assert "id" in data
        assert "created_at" in data
    
    def test_create_ngo_duplicate_name(self):
        """Test creating NGO with duplicate name returns 409"""
        unique_name = f"Duplicate Test NGO {random_string()}"
        ngo_data = {
            "name": unique_name,
            "description": "Building schools in rural Ethiopia"
        }
        # First creation should succeed
        response1 = client.post("/ngos/", json=ngo_data)
        assert response1.status_code == 201
        
        # Second creation should fail
        response2 = client.post("/ngos/", json=ngo_data)
        assert response2.status_code == 409
        assert "already exists" in response2.json()["detail"]
    
    def test_list_ngos(self):
        """Test listing all NGOs"""
        response = client.get("/ngos/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2  # We created at least 2 NGOs
    
    def test_get_ngo_by_id(self):
        """Test retrieving specific NGO"""
        # Create NGO first
        ngo_name = f"Health Test {random_string()}"
        create_response = client.post(
            "/ngos/",
            json={"name": ngo_name, "description": "Healthcare services"}
        )
        ngo_id = create_response.json()["id"]
        
        # Get NGO
        response = client.get(f"/ngos/{ngo_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == ngo_id
        assert data["name"] == ngo_name
    
    def test_get_ngo_not_found(self):
        """Test getting non-existent NGO returns 404"""
        response = client.get("/ngos/99999")
        assert response.status_code == 404
    
    def test_update_ngo(self):
        """Test updating NGO details"""
        # Create NGO first
        original_name = f"Original Name {random_string()}"
        create_response = client.post(
            "/ngos/",
            json={"name": original_name, "description": "Original description"}
        )
        ngo_id = create_response.json()["id"]
        
        # Update NGO
        response = client.patch(
            f"/ngos/{ngo_id}",
            json={"description": "Updated description", "website_url": "https://updated.org"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "Updated description"
        assert data["website_url"] == "https://updated.org"
        assert data["name"] == original_name  # Should not change


# ==========================================
# Campaign Management Tests
# ==========================================

class TestCampaignEndpoints:
    """Test Campaign CRUD operations"""
    
    def test_create_campaign(self):
        """Test creating a new campaign"""
        # Create NGO first
        ngo_response = client.post(
            "/ngos/",
            json={"name": f"Test NGO for Campaign {random_string()}", "description": "Test"}
        )
        ngo_id = ngo_response.json()["id"]
        
        # Create campaign
        response = client.post(
            "/campaigns/",
            json={
                "ngo_id": ngo_id,
                "title": "Clean Water Project",
                "description": "Build 10 wells in rural areas",
                "goal_amount_usd": 50000.0,
                "location_gps": "-1.286389,36.817223"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Clean Water Project"
        assert data["goal_amount_usd"] == 50000.0
        assert data["raised_amount_usd"] == 0.0
        assert data["status"] == "active"
    
    def test_create_campaign_invalid_ngo(self):
        """Test creating campaign with non-existent NGO returns 404"""
        response = client.post(
            "/campaigns/",
            json={
                "ngo_id": 99999,
                "title": "Invalid Campaign",
                "description": "Should fail",
                "goal_amount_usd": 10000.0
            }
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_list_campaigns(self):
        """Test listing all campaigns"""
        response = client.get("/campaigns/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_list_campaigns_by_status(self):
        """Test filtering campaigns by status"""
        response = client.get("/campaigns/?status=active")
        assert response.status_code == 200
        data = response.json()
        assert all(campaign["status"] == "active" for campaign in data)
    
    def test_list_campaigns_invalid_status(self):
        """Test invalid status filter returns 400"""
        response = client.get("/campaigns/?status=invalid")
        assert response.status_code == 400
    
    def test_get_campaign_by_id(self):
        """Test retrieving specific campaign"""
        # Create NGO and campaign
        ngo_response = client.post("/ngos/", json={"name": f"NGO for Get Test {random_string()}", "description": "Test"})
        ngo_id = ngo_response.json()["id"]
        
        create_response = client.post(
            "/campaigns/",
            json={
                "ngo_id": ngo_id,
                "title": "Test Campaign",
                "description": "Test",
                "goal_amount_usd": 10000.0
            }
        )
        campaign_id = create_response.json()["id"]
        
        # Get campaign
        response = client.get(f"/campaigns/{campaign_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == campaign_id
        assert data["title"] == "Test Campaign"
    
    def test_update_campaign(self):
        """Test updating campaign details"""
        # Create NGO and campaign
        ngo_response = client.post("/ngos/", json={"name": f"NGO for Update Test {random_string()}", "description": "Test"})
        ngo_id = ngo_response.json()["id"]
        
        create_response = client.post(
            "/campaigns/",
            json={
                "ngo_id": ngo_id,
                "title": "Original Title",
                "description": "Original description",
                "goal_amount_usd": 10000.0
            }
        )
        campaign_id = create_response.json()["id"]
        
        # Update campaign
        response = client.patch(
            f"/campaigns/{campaign_id}",
            json={"title": "Updated Title", "status": "paused"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["status"] == "paused"
    
    def test_delete_campaign(self):
        """Test soft delete (status=completed)"""
        # Create NGO and campaign
        ngo_response = client.post("/ngos/", json={"name": f"NGO for Delete Test {random_string()}", "description": "Test"})
        ngo_id = ngo_response.json()["id"]
        
        create_response = client.post(
            "/campaigns/",
            json={
                "ngo_id": ngo_id,
                "title": "Campaign to Delete",
                "description": "Test",
                "goal_amount_usd": 10000.0
            }
        )
        campaign_id = create_response.json()["id"]
        
        # Delete campaign
        response = client.delete(f"/campaigns/{campaign_id}")
        assert response.status_code == 204
        
        # Verify it's marked as completed
        get_response = client.get(f"/campaigns/{campaign_id}")
        assert get_response.json()["status"] == "completed"


# ==========================================
# Donor Management Tests
# ==========================================

class TestDonorEndpoints:
    """Test Donor registration and management"""
    
    def test_create_donor_with_phone(self):
        """Test registering donor with phone number"""
        phone = random_phone("254", 9)
        response = client.post(
            "/donors/",
            json={
                "phone_number": phone,
                "preferred_language": "en"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["phone_number"] == phone
        assert data["preferred_language"] == "en"
        assert data["total_donated_usd"] == 0.0
    
    def test_create_donor_with_telegram(self):
        """Test registering donor with Telegram ID"""
        telegram_id = f"telegram_{random_string()}"
        response = client.post(
            "/donors/",
            json={
                "telegram_user_id": telegram_id,
                "preferred_language": "am"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["telegram_user_id"] == telegram_id
        assert data["preferred_language"] == "am"
    
    def test_create_donor_no_contact_method(self):
        """Test creating donor without contact method returns 400"""
        response = client.post(
            "/donors/",
            json={"preferred_language": "en"}
        )
        assert response.status_code == 400
        assert "contact method" in response.json()["detail"]
    
    def test_create_donor_duplicate_phone(self):
        """Test duplicate phone number returns 409"""
        donor_data = {
            "phone_number": random_phone("255", 9),
            "preferred_language": "sw"
        }
        # First creation should succeed
        response1 = client.post("/donors/", json=donor_data)
        assert response1.status_code == 201
        
        # Second creation should fail
        response2 = client.post("/donors/", json=donor_data)
        assert response2.status_code == 409
        assert "already exists" in response2.json()["detail"]
    
    def test_get_donor_by_id(self):
        """Test retrieving donor by ID"""
        # Create donor
        create_response = client.post(
            "/donors/",
            json={"phone_number": random_phone("251", 9), "preferred_language": "am"}
        )
        donor_id = create_response.json()["id"]
        
        # Get donor
        response = client.get(f"/donors/{donor_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == donor_id
    
    def test_get_donor_by_phone(self):
        """Test retrieving donor by phone number"""
        phone = random_phone("49", 11)
        # Create donor
        client.post("/donors/", json={"phone_number": phone, "preferred_language": "de"})
        
        # Get by phone
        response = client.get(f"/donors/phone/{phone}")
        assert response.status_code == 200
        data = response.json()
        assert data["phone_number"] == phone
    
    def test_get_donor_by_telegram(self):
        """Test retrieving donor by Telegram ID"""
        telegram_id = f"telegram_{random_string()}"
        # Create donor
        client.post("/donors/", json={"telegram_user_id": telegram_id, "preferred_language": "en"})
        
        # Get by Telegram
        response = client.get(f"/donors/telegram/{telegram_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["telegram_user_id"] == telegram_id
    
    def test_update_donor(self):
        """Test updating donor profile"""
        # Create donor
        phone = random_phone("33", 9)
        create_response = client.post(
            "/donors/",
            json={"phone_number": phone, "preferred_language": "fr"}
        )
        donor_id = create_response.json()["id"]
        
        # Update donor (use same phone as whatsapp since donor owns it)
        response = client.patch(
            f"/donors/{donor_id}",
            json={"preferred_language": "en", "whatsapp_number": phone}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["preferred_language"] == "en"
        assert data["whatsapp_number"] == phone


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
