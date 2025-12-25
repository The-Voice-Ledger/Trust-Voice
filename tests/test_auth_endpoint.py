"""
Test Web Login Endpoint

Tests for POST /auth/login and GET /auth/me endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app
from database.models import Base, User, UserRole
from database.db import get_db
from services.auth_service import hash_pin

# Test database setup
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test_auth.db"
engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(scope="function")
def setup_database():
    """Create tables before each test, drop after"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_user(setup_database):
    """Create a test user with PIN"""
    db = TestingSessionLocal()
    user = User(
        telegram_user_id="123456",
        telegram_username="testuser",
        email="test@example.com",
        role=UserRole.CAMPAIGN_CREATOR,
        pin_hash=hash_pin("7392"),
        pin_set_at=datetime.utcnow(),
        is_approved=True,
        approved_at=datetime.utcnow()
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    return user


@pytest.fixture
def unapproved_user(setup_database):
    """Create an unapproved test user"""
    db = TestingSessionLocal()
    user = User(
        telegram_user_id="789012",
        telegram_username="pending_user",
        email="pending@example.com",
        role=UserRole.CAMPAIGN_CREATOR,
        pin_hash=hash_pin("7392"),
        pin_set_at=datetime.utcnow(),
        is_approved=False
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    return user


@pytest.fixture
def user_without_pin(setup_database):
    """Create a user without PIN set"""
    db = TestingSessionLocal()
    user = User(
        telegram_user_id="345678",
        telegram_username="no_pin_user",
        email="nopin@example.com",
        role=UserRole.CAMPAIGN_CREATOR,
        is_approved=True,
        approved_at=datetime.utcnow()
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    return user


class TestLoginEndpoint:
    """Test POST /auth/login"""
    
    def test_login_success_with_username(self, test_user):
        """Test successful login with telegram username"""
        response = client.post(
            "/auth/login",
            json={"username": "testuser", "pin": "7392"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] == 900  # 15 minutes
        assert data["user"]["telegram_username"] == "testuser"
        assert data["user"]["role"] == "CAMPAIGN_CREATOR"
        assert data["user"]["is_approved"] is True
    
    def test_login_success_with_email(self, test_user):
        """Test successful login with email"""
        response = client.post(
            "/auth/login",
            json={"username": "test@example.com", "pin": "7392"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["email"] == "test@example.com"
    
    def test_login_invalid_username(self, setup_database):
        """Test login with non-existent username"""
        response = client.post(
            "/auth/login",
            json={"username": "nonexistent", "pin": "7392"}
        )
        
        assert response.status_code == 401
        assert "Invalid username or PIN" in response.json()["detail"]
    
    def test_login_invalid_pin(self, test_user):
        """Test login with wrong PIN"""
        response = client.post(
            "/auth/login",
            json={"username": "testuser", "pin": "9999"}
        )
        
        assert response.status_code == 401
        assert "Invalid PIN" in response.json()["detail"]
        assert "attempts remaining" in response.json()["detail"]
    
    def test_login_pin_not_set(self, user_without_pin):
        """Test login when user hasn't set PIN"""
        response = client.post(
            "/auth/login",
            json={"username": "no_pin_user", "pin": "7392"}
        )
        
        assert response.status_code == 401
        assert "PIN not set" in response.json()["detail"]
        assert "/set_pin" in response.json()["detail"]
    
    def test_login_not_approved(self, unapproved_user):
        """Test login for unapproved user"""
        response = client.post(
            "/auth/login",
            json={"username": "pending_user", "pin": "7392"}
        )
        
        assert response.status_code == 403
        assert "pending admin approval" in response.json()["detail"].lower()
    
    def test_login_account_lockout(self, test_user):
        """Test account lockout after 5 failed attempts"""
        # Make 5 failed login attempts
        for i in range(5):
            response = client.post(
                "/auth/login",
                json={"username": "testuser", "pin": "9999"}
            )
            
            if i < 4:
                assert response.status_code == 401
            else:
                # 5th attempt should lock account
                assert response.status_code == 423
                assert "locked" in response.json()["detail"].lower()
        
        # Try with correct PIN - should still be locked
        response = client.post(
            "/auth/login",
            json={"username": "testuser", "pin": "7392"}
        )
        assert response.status_code == 423
        assert "locked" in response.json()["detail"].lower()
    
    def test_login_reset_attempts_on_success(self, setup_database):
        """Test that failed attempts reset on successful login"""
        # Create user
        db = TestingSessionLocal()
        user = User(
            telegram_user_id="reset_test",
            telegram_username="reset_user",
            email="reset@example.com",
            role=UserRole.CAMPAIGN_CREATOR,
            pin_hash=hash_pin("7392"),
            pin_set_at=datetime.utcnow(),
            is_approved=True,
            approved_at=datetime.utcnow(),
            failed_login_attempts=3  # Pre-existing failed attempts
        )
        db.add(user)
        db.commit()
        db.close()
        
        # Successful login should reset attempts
        response = client.post(
            "/auth/login",
            json={"username": "reset_user", "pin": "7392"}
        )
        
        assert response.status_code == 200
        
        # Check that attempts were reset in database
        db = TestingSessionLocal()
        user = db.query(User).filter(User.telegram_username == "reset_user").first()
        assert user.failed_login_attempts == 0
        assert user.last_login_at is not None
        db.close()


class TestMeEndpoint:
    """Test GET /auth/me"""
    
    def test_get_me_success(self, test_user):
        """Test getting current user info with valid token"""
        # First login to get token
        login_response = client.post(
            "/auth/login",
            json={"username": "testuser", "pin": "7392"}
        )
        token = login_response.json()["access_token"]
        
        # Get user info
        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["telegram_username"] == "testuser"
        assert data["email"] == "test@example.com"
        assert data["role"] == "CAMPAIGN_CREATOR"
        assert data["is_approved"] is True
        assert data["phone_verified"] is False
    
    def test_get_me_no_token(self, setup_database):
        """Test /me without token"""
        response = client.get("/auth/me")
        assert response.status_code == 403  # FastAPI returns 403 for missing auth
    
    def test_get_me_invalid_token(self, setup_database):
        """Test /me with invalid token"""
        response = client.get(
            "/auth/me",
            headers={"Authorization": "Bearer invalid_token_here"}
        )
        assert response.status_code == 401
        assert "Invalid or expired token" in response.json()["detail"]


class TestLogoutEndpoint:
    """Test POST /auth/logout"""
    
    def test_logout(self, setup_database):
        """Test logout endpoint (client-side token discard)"""
        response = client.post("/auth/logout")
        
        assert response.status_code == 200
        assert "Logged out" in response.json()["message"]
        assert response.json()["action"] == "client_side_logout"


class TestTokenExpiry:
    """Test JWT token expiration"""
    
    def test_token_contains_expiry(self, test_user):
        """Test that token includes expiration time"""
        from services.auth_service import decode_access_token
        
        # Login to get token
        login_response = client.post(
            "/auth/login",
            json={"username": "testuser", "pin": "7392"}
        )
        token = login_response.json()["access_token"]
        
        # Decode and check expiry
        payload = decode_access_token(token)
        assert "exp" in payload
        
        # Expiry should be in the future
        exp_time = datetime.fromtimestamp(payload["exp"])
        now = datetime.utcnow()
        
        assert exp_time > now, "Token should not be expired"
        
        # Token should have reasonable expiry (between 10 minutes and 25 hours)
        time_diff_seconds = (exp_time - now).total_seconds()
        assert 600 < time_diff_seconds < 90000, f"Token expiry {time_diff_seconds}s is outside reasonable range"
