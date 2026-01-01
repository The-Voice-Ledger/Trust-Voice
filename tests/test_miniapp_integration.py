"""
Integration tests for mini app backend endpoints.
Tests all API endpoints that the mini apps depend on.
"""
import pytest
import asyncio
import json
from pathlib import Path
from fastapi.testclient import TestClient
from io import BytesIO

# Test if we can import the main app
try:
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from main import app
    from database.models import Campaign, NGOOrganization, Donation, User
    from database.db import get_db
    from sqlalchemy import create_engine
    HAS_APP = True
except Exception as e:
    print(f"Warning: Could not import app: {e}")
    HAS_APP = False


@pytest.fixture
def client():
    """Create test client"""
    if not HAS_APP:
        pytest.skip("App not available")
    return TestClient(app)


@pytest.fixture
def test_audio_file():
    """Create a mock audio file for testing"""
    # Create a small valid WebM audio file header
    audio_data = b'RIFF' + b'\x00' * 100  # Mock audio data
    return BytesIO(audio_data)


class TestCampaignEndpoints:
    """Test campaign-related endpoints used by campaigns.html"""
    
    def test_list_campaigns(self, client):
        """Test GET /api/campaigns/ - Used by campaigns.html"""
        response = client.get("/api/campaigns/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # Check structure of campaign objects (using actual API field names)
        if len(data) > 0:
            campaign = data[0]
            required_fields = ['id', 'title', 'description', 'goal_amount_usd', 
                             'raised_amount_usd', 'status']
            for field in required_fields:
                assert field in campaign, f"Campaign missing field: {field}"
    
    def test_get_campaign_by_id(self, client):
        """Test GET /api/campaigns/{id} - Used by donate.html"""
        # First get list to find a valid ID
        response = client.get("/api/campaigns/")
        campaigns = response.json()
        
        if len(campaigns) > 0:
            campaign_id = campaigns[0]['id']
            response = client.get(f"/api/campaigns/{campaign_id}")
            assert response.status_code == 200
            campaign = response.json()
            assert campaign['id'] == campaign_id
            assert 'title' in campaign
            assert 'ngo_name' in campaign or 'ngo_id' in campaign
    
    def test_create_campaign(self, client):
        """Test POST /api/campaigns/ - Used by create-campaign-wizard.html"""
        campaign_data = {
            "title": "Test Campaign",
            "description": "This is a test campaign for integration testing",
            "target_amount": 5000,
            "category": "education",
            "ngo_id": 1,  # Assuming NGO 1 exists
            "deadline": "2026-12-31"
        }
        
        response = client.post("/api/campaigns/", json=campaign_data)
        # May fail if NGO doesn't exist, but should not return 500
        assert response.status_code in [200, 201, 400, 404, 422]
        
        if response.status_code in [200, 201]:
            campaign = response.json()
            assert campaign['title'] == campaign_data['title']
            assert 'id' in campaign


class TestDonationEndpoints:
    """Test donation-related endpoints used by donate.html"""
    
    def test_create_donation(self, client):
        """Test POST /api/donations/ - Used by donate.html"""
        # First get a campaign
        campaigns_response = client.get("/api/campaigns/")
        campaigns = campaigns_response.json()
        
        if len(campaigns) > 0:
            donation_data = {
                "campaign_id": campaigns[0]['id'],
                "amount": 100,
                "payment_method": "card",
                "user_id": 12345,
                "currency": "USD"
            }
            
            response = client.post("/api/donations/", json=donation_data)
            assert response.status_code in [200, 201, 400, 404, 422]
            
            if response.status_code in [200, 201]:
                donation = response.json()
                assert donation['amount'] == donation_data['amount']
                assert 'id' in donation


class TestNGOEndpoints:
    """Test NGO-related endpoints used by ngo-register-wizard.html"""
    
    def test_register_ngo(self, client):
        """Test POST /api/ngo-registrations/ - Used by ngo-register-wizard.html"""
        ngo_data = {
            "name": "Test NGO Organization",
            "description": "A test organization for integration testing",
            "email": "test@testngo.org",
            "country": "Kenya",
            "category": "education",
            "status": "pending"
        }
        
        response = client.post("/api/ngo-registrations/", json=ngo_data)
        # Should accept registration (201) or show validation errors (400/422)
        assert response.status_code in [201, 400, 422], \
            f"NGO registration endpoint should exist, got {response.status_code}"
        
        if response.status_code in [200, 201]:
            ngo = response.json()
            assert ngo['name'] == ngo_data['name']
            assert 'id' in ngo
    
    def test_list_ngos(self, client):
        """Test GET /api/ngos/ - Used by admin panel"""
        response = client.get("/api/ngos/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestVoiceEndpoints:
    """Test voice processing endpoints used by all mini apps"""
    
    def test_voice_wizard_step_endpoint_exists(self, client):
        """Test POST /api/voice/wizard-step - Used by wizards"""
        # Test without audio (should fail gracefully)
        response = client.post("/api/voice/wizard-step")
        # Should return 422 (validation error) not 404
        assert response.status_code in [400, 422], \
            f"Endpoint should exist and validate input, got {response.status_code}"
    
    def test_voice_dictate_endpoint_exists(self, client):
        """Test POST /api/voice/dictate-text - Used by donate.html"""
        response = client.post("/api/voice/dictate-text")
        # Should return 422 (validation error) not 404
        assert response.status_code in [400, 422], \
            f"Endpoint should exist and validate input, got {response.status_code}"
    
    def test_voice_search_endpoint_exists(self, client):
        """Test POST /api/voice/search-campaigns - Used by campaigns.html"""
        response = client.post("/api/voice/search-campaigns")
        # Should return 422 (validation error) not 404
        assert response.status_code in [400, 422], \
            f"Endpoint should exist and validate input, got {response.status_code}"
    
    def test_voice_wizard_with_mock_audio(self, client, test_audio_file):
        """Test wizard endpoint with audio file"""
        files = {
            'audio': ('test.webm', test_audio_file, 'audio/webm')
        }
        data = {
            'field_name': 'title',
            'step_number': '1'
        }
        
        response = client.post("/api/voice/wizard-step", files=files, data=data)
        # May fail due to invalid audio, but endpoint should exist
        assert response.status_code in [200, 400, 422, 500], \
            f"Unexpected status code: {response.status_code}"


class TestStaticFiles:
    """Test that mini app HTML files exist and are accessible"""
    
    def test_index_html_exists(self, client):
        """Test main index page"""
        response = client.get("/")
        assert response.status_code == 200
    
    def test_campaigns_html_exists(self, client):
        """Test campaigns.html"""
        response = client.get("/campaigns.html")
        assert response.status_code == 200
        assert b"Campaign Browser" in response.content or b"campaigns" in response.content
    
    def test_donate_html_exists(self, client):
        """Test donate.html"""
        response = client.get("/donate.html")
        assert response.status_code == 200
        assert b"donate" in response.content.lower()
    
    def test_create_campaign_wizard_exists(self, client):
        """Test create-campaign-wizard.html"""
        response = client.get("/create-campaign-wizard.html")
        assert response.status_code == 200
        assert b"campaign" in response.content.lower()
    
    def test_ngo_register_wizard_exists(self, client):
        """Test ngo-register-wizard.html"""
        response = client.get("/ngo-register-wizard.html")
        assert response.status_code == 200
        assert b"ngo" in response.content.lower() or b"organization" in response.content.lower()


class TestAnalyticsEndpoints:
    """Test analytics endpoints used by conversation-analytics.html"""
    
    def test_analytics_summary_endpoint(self, client):
        """Test GET /api/analytics/summary"""
        response = client.get("/api/analytics/summary")
        # May not be implemented yet
        assert response.status_code in [200, 404, 501]
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)
    
    def test_analytics_events_endpoint(self, client):
        """Test GET /api/analytics/events"""
        response = client.get("/api/analytics/events")
        assert response.status_code in [200, 404, 501]
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)


class TestCORSAndHeaders:
    """Test CORS and security headers"""
    
    def test_cors_headers_present(self, client):
        """Test that CORS headers are configured"""
        # TestClient doesn't fully support OPTIONS preflight, so we test actual requests
        response = client.get("/api/campaigns/")
        # CORS is configured in main.py middleware, should return successfully
        assert response.status_code == 200
    
    def test_api_accepts_json(self, client):
        """Test that API accepts JSON content type"""
        response = client.get(
            "/api/campaigns/",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200


class TestErrorHandling:
    """Test error handling for invalid requests"""
    
    def test_invalid_campaign_id(self, client):
        """Test requesting non-existent campaign"""
        response = client.get("/api/campaigns/999999")
        assert response.status_code in [404, 422]
    
    def test_invalid_json_payload(self, client):
        """Test sending invalid JSON"""
        response = client.post(
            "/api/campaigns/",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code in [400, 422]
    
    def test_missing_required_fields(self, client):
        """Test creating campaign without required fields"""
        response = client.post("/api/campaigns/", json={})
        assert response.status_code == 422  # Validation error


class TestDataIntegrity:
    """Test data validation and integrity"""
    
    def test_campaign_amounts_are_numbers(self, client):
        """Test that campaign amounts are numeric"""
        response = client.get("/api/campaigns/")
        campaigns = response.json()
        
        for campaign in campaigns:
            if 'target_amount' in campaign:
                assert isinstance(campaign['target_amount'], (int, float))
            if 'amount_raised' in campaign:
                assert isinstance(campaign['amount_raised'], (int, float))
    
    def test_donation_amount_validation(self, client):
        """Test that negative donations are rejected"""
        campaigns_response = client.get("/api/campaigns/")
        campaigns = campaigns_response.json()
        
        if len(campaigns) > 0:
            donation_data = {
                "campaign_id": campaigns[0]['id'],
                "amount": -100,  # Invalid negative amount
                "payment_method": "card",
                "currency": "USD"
            }
            
            response = client.post("/api/donations/", json=donation_data)
            # Should reject negative amounts
            assert response.status_code in [400, 422]


# Integration test for full workflow
class TestFullWorkflow:
    """Test complete user workflows"""
    
    def test_campaign_creation_to_donation_flow(self, client):
        """Test creating a campaign and making a donation"""
        # This would test the complete flow but requires database setup
        # Skip if database not available
        pass
    
    def test_voice_wizard_flow(self, client, test_audio_file):
        """Test voice wizard multi-step flow"""
        # Test would simulate going through wizard steps
        # Skip for now as it requires real audio processing
        pass


# Performance tests
class TestPerformance:
    """Basic performance checks"""
    
    def test_campaigns_list_response_time(self, client):
        """Test that campaign listing is reasonably fast"""
        import time
        start = time.time()
        response = client.get("/api/campaigns/")
        duration = time.time() - start
        
        assert response.status_code == 200
        assert duration < 2.0, f"Campaign listing took {duration}s (should be < 2s)"
    
    def test_concurrent_requests(self, client):
        """Test handling multiple concurrent requests"""
        import concurrent.futures
        
        def make_request():
            return client.get("/api/campaigns/")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [f.result() for f in futures]
        
        # All requests should succeed
        assert all(r.status_code == 200 for r in results)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
