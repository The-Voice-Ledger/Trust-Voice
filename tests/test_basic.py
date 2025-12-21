"""
Simple direct tests without pytest (avoiding web3 plugin conflict).
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from main import app
from database.models import Donor, Campaign, Donation
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Test client
client = TestClient(app)

def test_health_endpoint():
    """Test health endpoint."""
    print("Testing /health endpoint...")
    response = client.get("/health")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data["status"] == "healthy", f"Expected healthy status"
    assert data["service"] == "TrustVoice API"
    print("✅ Health endpoint test passed")

def test_root_endpoint():
    """Test root endpoint."""
    print("Testing / endpoint...")
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "TrustVoice" in data["message"]
    print("✅ Root endpoint test passed")

def test_models_exist():
    """Test that models can be imported."""
    print("Testing database models...")
    
    # Test Donor model
    assert hasattr(Donor, 'id')
    assert hasattr(Donor, 'phone_number')
    assert hasattr(Donor, 'preferred_language')
    print("  ✓ Donor model OK")
    
    # Test Campaign model
    assert hasattr(Campaign, 'title')
    assert hasattr(Campaign, 'goal_amount_usd')
    print("  ✓ Campaign model OK")
    
    # Test Donation model
    assert hasattr(Donation, 'amount_usd')
    assert hasattr(Donation, 'status')
    print("  ✓ Donation model OK")
    
    print("✅ All models test passed")

def test_environment_variables():
    """Test environment variables are loaded."""
    print("Testing environment variables...")
    
    assert os.getenv("DATABASE_URL") is not None, "DATABASE_URL not set"
    assert "postgresql" in os.getenv("DATABASE_URL"), "DATABASE_URL should contain postgresql"
    assert os.getenv("APP_ENV") == "development", "APP_ENV should be development"
    assert os.getenv("OPENAI_API_KEY") is not None, "OPENAI_API_KEY not set"
    assert os.getenv("STRIPE_SECRET_KEY") is not None, "STRIPE_SECRET_KEY not set"
    
    print("✅ Environment variables test passed")

def test_database_connection():
    """Test database connection."""
    print("Testing database connection...")
    from database.db import engine, DATABASE_URL
    
    assert DATABASE_URL is not None
    assert "neon" in DATABASE_URL
    assert engine is not None
    
    print("✅ Database connection test passed")

if __name__ == "__main__":
    print("\n" + "="*50)
    print("   TrustVoice Lab 1 Test Suite")
    print("="*50 + "\n")
    
    tests = [
        test_health_endpoint,
        test_root_endpoint,
        test_models_exist,
        test_environment_variables,
        test_database_connection
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"❌ {test.__name__} failed: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ {test.__name__} error: {e}")
            failed += 1
    
    print("\n" + "="*50)
    print(f"Results: {passed} passed, {failed} failed")
    print("="*50 + "\n")
    
    sys.exit(0 if failed == 0 else 1)
