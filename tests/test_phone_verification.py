"""
Test Phone Verification

Tests for /verify_phone command and contact sharing.
"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, AsyncMock, patch
from telegram import Update, Contact, Message, User as TelegramUser
from telegram.ext import ContextTypes

from voice.telegram.phone_verification import (
    verify_phone_command,
    handle_contact_share,
    unverify_phone_command
)
from database.models import User, UserRole


class TestVerifyPhoneCommand:
    """Test /verify_phone command"""
    
    @pytest.mark.asyncio
    async def test_verify_phone_user_not_found(self, mock_db_session):
        """Test verify_phone when user doesn't exist"""
        update = MagicMock(spec=Update)
        update.effective_user.id = 999999
        update.message = AsyncMock(spec=Message)
        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        
        mock_db_session.query.return_value.filter_by.return_value.first.return_value = None
        
        await verify_phone_command(update, context)
        
        update.message.reply_text.assert_called_once()
        assert "not found" in update.message.reply_text.call_args[0][0].lower()
        assert "/register" in update.message.reply_text.call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_verify_phone_already_verified(self, mock_db_session):
        """Test verify_phone when phone already verified"""
        user = User(
            id=1,
            telegram_user_id="123456",
            role=UserRole.CAMPAIGN_CREATOR,
            phone_number="+254712345678",
            phone_verified_at=datetime.utcnow(),
            email="test@test.com"
        )
        
        update = MagicMock(spec=Update)
        update.effective_user.id = 123456
        update.message = AsyncMock(spec=Message)
        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        
        mock_db_session.query.return_value.filter_by.return_value.first.return_value = user
        
        await verify_phone_command(update, context)
        
        update.message.reply_text.assert_called_once()
        assert "already verified" in update.message.reply_text.call_args[0][0].lower()
        assert "+254712345678" in update.message.reply_text.call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_verify_phone_show_button(self, mock_db_session):
        """Test verify_phone shows contact share button"""
        user = User(
            id=1,
            telegram_user_id="123456",
            role=UserRole.CAMPAIGN_CREATOR,
            email="test@test.com"
        )
        
        update = MagicMock(spec=Update)
        update.effective_user.id = 123456
        update.message = AsyncMock(spec=Message)
        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        
        mock_db_session.query.return_value.filter_by.return_value.first.return_value = user
        
        await verify_phone_command(update, context)
        
        update.message.reply_text.assert_called_once()
        call_kwargs = update.message.reply_text.call_args[1]
        
        assert "Verify Your Phone" in update.message.reply_text.call_args[0][0]
        assert "reply_markup" in call_kwargs
        # Verify keyboard has contact request button
        keyboard = call_kwargs["reply_markup"].keyboard
        assert len(keyboard) == 1
        assert keyboard[0][0].request_contact is True


class TestContactShare:
    """Test contact sharing handler"""
    
    @pytest.mark.asyncio
    async def test_contact_share_wrong_user(self):
        """Test contact share from wrong user (security)"""
        contact = MagicMock(spec=Contact)
        contact.user_id = 999999  # Different from sender
        contact.phone_number = "+254712345678"
        
        update = MagicMock(spec=Update)
        update.message = AsyncMock(spec=Message)
        update.message.contact = contact
        update.effective_user.id = 123456
        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        
        await handle_contact_share(update, context)
        
        update.message.reply_text.assert_called_once()
        assert "YOUR OWN contact" in update.message.reply_text.call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_contact_share_duplicate_phone(self, mock_db_session):
        """Test contact share with phone already used"""
        # Existing user with phone
        existing_user = User(
            id=2,
            telegram_user_id="999999",
            phone_number="+254712345678",
            phone_verified_at=datetime.utcnow(),
            email="existing@test.com"
        )
        
        # Current user trying to verify same phone
        current_user = User(
            id=1,
            telegram_user_id="123456",
            email="current@test.com"
        )
        
        contact = MagicMock(spec=Contact)
        contact.user_id = 123456
        contact.phone_number = "+254712345678"
        
        update = MagicMock(spec=Update)
        update.message = AsyncMock(spec=Message)
        update.message.contact = contact
        update.effective_user.id = 123456
        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        
        # Mock database queries
        mock_db_session.query.return_value.filter_by.return_value.first.return_value = current_user
        mock_db_session.query.return_value.filter.return_value.first.return_value = existing_user
        
        await handle_contact_share(update, context)
        
        update.message.reply_text.assert_called_once()
        assert "already linked" in update.message.reply_text.call_args[0][0].lower()
    
    @pytest.mark.asyncio
    async def test_contact_share_success(self, mock_db_session):
        """Test successful contact share"""
        user = User(
            id=1,
            telegram_user_id="123456",
            role=UserRole.CAMPAIGN_CREATOR,
            telegram_username="testuser",
            email="test@test.com"
        )
        
        contact = MagicMock(spec=Contact)
        contact.user_id = 123456
        contact.phone_number = "+254712345678"
        
        update = MagicMock(spec=Update)
        update.message = AsyncMock(spec=Message)
        update.message.contact = contact
        update.effective_user.id = 123456
        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        
        # Mock database queries
        mock_db_session.query.return_value.filter_by.return_value.first.return_value = user
        mock_db_session.query.return_value.filter.return_value.first.return_value = None  # No duplicate
        
        await handle_contact_share(update, context)
        
        # Verify phone stored
        assert user.phone_number == "+254712345678"
        assert user.phone_verified_at is not None
        mock_db_session.commit.assert_called_once()
        
        # Verify success message
        update.message.reply_text.assert_called_once()
        assert "Verified Successfully" in update.message.reply_text.call_args[0][0]
        assert "+254712345678" in update.message.reply_text.call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_contact_share_adds_plus_prefix(self, mock_db_session):
        """Test phone number gets + prefix if missing"""
        user = User(
            id=1,
            telegram_user_id="123456",
            role=UserRole.DONOR,
            email="test@test.com"
        )
        
        contact = MagicMock(spec=Contact)
        contact.user_id = 123456
        contact.phone_number = "254712345678"  # Missing +
        
        update = MagicMock(spec=Update)
        update.message = AsyncMock(spec=Message)
        update.message.contact = contact
        update.effective_user.id = 123456
        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        
        mock_db_session.query.return_value.filter_by.return_value.first.return_value = user
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        await handle_contact_share(update, context)
        
        # Should add + prefix
        assert user.phone_number == "+254712345678"


class TestUnverifyPhone:
    """Test /unverify_phone command"""
    
    @pytest.mark.asyncio
    async def test_unverify_phone_success(self, mock_db_session):
        """Test successful phone unverification"""
        user = User(
            id=1,
            telegram_user_id="123456",
            phone_number="+254712345678",
            phone_verified_at=datetime.utcnow(),
            email="test@test.com"
        )
        
        update = MagicMock(spec=Update)
        update.effective_user.id = 123456
        update.message = AsyncMock(spec=Message)
        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        
        mock_db_session.query.return_value.filter_by.return_value.first.return_value = user
        
        await unverify_phone_command(update, context)
        
        # Verify phone removed
        assert user.phone_number is None
        assert user.phone_verified_at is None
        mock_db_session.commit.assert_called_once()
        
        update.message.reply_text.assert_called_once()
        assert "removed" in update.message.reply_text.call_args[0][0].lower()
        assert "+254712345678" in update.message.reply_text.call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_unverify_phone_not_verified(self, mock_db_session):
        """Test unverify when phone not verified"""
        user = User(
            id=1,
            telegram_user_id="123456",
            email="test@test.com"
        )
        
        update = MagicMock(spec=Update)
        update.effective_user.id = 123456
        update.message = AsyncMock(spec=Message)
        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        
        mock_db_session.query.return_value.filter_by.return_value.first.return_value = user
        
        await unverify_phone_command(update, context)
        
        update.message.reply_text.assert_called_once()
        assert "No phone number verified" in update.message.reply_text.call_args[0][0]


# Fixtures
@pytest.fixture
def mock_db_session():
    """Mock database session"""
    with patch('voice.telegram.phone_verification.get_db') as mock_get_db:
        mock_session = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_session
        yield mock_session
