"""
Basic tests for TrustVoice API endpoints.

Tests:
- Health check endpoint
- Database connection
- Model creation
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

# Import app
from main import app

# Test client
client = TestClient(app)


class TestHealthEndpoints:
    """Test basic health and info endpoints."""
    
    def test_root_endpoint(self):
        """Test root endpoint returns welcome message."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "TrustVoice" in data["message"]
    
    def test_health_check(self):
        """Test health endpoint returns healthy status."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "TrustVoice API"
        assert data["version"] == "1.0.0"
        assert "environment" in data


class TestDatabaseModels:
    """Test database model creation."""
    
    def test_donor_model_creation(self):
        """Test Donor model can be imported and has correct fields."""
        from database.models import Donor
        
        # Check key fields exist
        assert hasattr(Donor, 'id')
        assert hasattr(Donor, 'phone_number')
        assert hasattr(Donor, 'telegram_user_id')
        assert hasattr(Donor, 'preferred_language')
        assert hasattr(Donor, 'total_donated_usd')
    
    def test_campaign_model_creation(self):
        """Test Campaign model can be imported and has correct fields."""
        from database.models import Campaign
        
        assert hasattr(Campaign, 'id')
        assert hasattr(Campaign, 'ngo_id')
        assert hasattr(Campaign, 'title')
        assert hasattr(Campaign, 'goal_amount_usd')
        assert hasattr(Campaign, 'raised_amount_usd')
        assert hasattr(Campaign, 'status')
    
    def test_donation_model_creation(self):
        """Test Donation model can be imported and has correct fields."""
        from database.models import Donation
        
        assert hasattr(Donation, 'id')
        assert hasattr(Donation, 'donor_id')
        assert hasattr(Donation, 'campaign_id')
        assert hasattr(Donation, 'amount_usd')
        assert hasattr(Donation, 'payment_method')
        assert hasattr(Donation, 'status')


class TestDatabaseConnection:
    """Test database connection (requires DATABASE_URL)."""
    
    def test_database_url_exists(self):
        """Test that DATABASE_URL is configured."""
        from database.db import DATABASE_URL
        assert DATABASE_URL is not None
        assert "postgresql" in DATABASE_URL
    
    def test_engine_creation(self):
        """Test that database engine can be created."""
        from database.db import engine
        assert engine is not None


class TestEnvironmentVariables:
    """Test environment configuration."""
    
    def test_required_env_vars(self):
        """Test that critical environment variables are set."""
        from dotenv import load_dotenv
        load_dotenv()
        
        # These should exist (even if placeholder values)
        assert os.getenv("DATABASE_URL") is not None
        assert os.getenv("APP_ENV") is not None
        assert os.getenv("APP_PORT") is not None


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
