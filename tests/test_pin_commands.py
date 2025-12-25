"""
Test PIN Commands

Tests for /set_pin and /change_pin Telegram commands.
"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, AsyncMock, patch
from telegram import Update, User as TelegramUser, Message, Chat
from telegram.ext import ContextTypes

from voice.telegram.pin_commands import (
    set_pin_command,
    change_pin_command,
    handle_new_pin_entry,
    handle_pin_confirmation,
    handle_old_pin_entry,
    ENTERING_NEW_PIN,
    CONFIRMING_NEW_PIN,
    ENTERING_OLD_PIN
)
from database.models import User, UserRole
from services.auth_service import hash_pin, verify_pin


class TestSetPinCommand:
    """Test /set_pin command"""
    
    @pytest.mark.asyncio
    async def test_set_pin_user_not_found(self, mock_db_session):
        """Test set_pin when user doesn't exist"""
        # Mock update and context
        update = MagicMock(spec=Update)
        update.effective_user.id = 999999
        update.message = AsyncMock(spec=Message)
        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        
        # Mock database to return no user
        mock_db_session.query.return_value.filter_by.return_value.first.return_value = None
        
        # Execute
        result = await set_pin_command(update, context)
        
        # Verify
        update.message.reply_text.assert_called_once()
        assert "User not found" in update.message.reply_text.call_args[0][0]
        assert result == -1  # ConversationHandler.END
    
    @pytest.mark.asyncio
    async def test_set_pin_already_set(self, mock_db_session):
        """Test set_pin when PIN already exists"""
        # Mock user with existing PIN
        user = User(
            id=1,
            telegram_user_id="123456",
            role=UserRole.CAMPAIGN_CREATOR,
            pin_hash="existing_hash",
            email="test@test.com"
        )
        
        update = MagicMock(spec=Update)
        update.effective_user.id = 123456
        update.message = AsyncMock(spec=Message)
        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        
        mock_db_session.query.return_value.filter_by.return_value.first.return_value = user
        
        # Execute
        result = await set_pin_command(update, context)
        
        # Verify
        update.message.reply_text.assert_called_once()
        assert "already have a PIN" in update.message.reply_text.call_args[0][0]
        assert "/change_pin" in update.message.reply_text.call_args[0][0]
        assert result == -1  # ConversationHandler.END
    
    @pytest.mark.asyncio
    async def test_set_pin_donor_role(self, mock_db_session):
        """Test set_pin for Donor role (should be rejected)"""
        # Mock donor user
        user = User(
            id=1,
            telegram_user_id="123456",
            role=UserRole.DONOR,
            email="donor@test.com"
        )
        
        update = MagicMock(spec=Update)
        update.effective_user.id = 123456
        update.message = AsyncMock(spec=Message)
        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        
        mock_db_session.query.return_value.filter_by.return_value.first.return_value = user
        
        # Execute
        result = await set_pin_command(update, context)
        
        # Verify
        update.message.reply_text.assert_called_once()
        assert "don't need a PIN" in update.message.reply_text.call_args[0][0]
        assert result == -1  # ConversationHandler.END
    
    @pytest.mark.asyncio
    async def test_set_pin_success_prompt(self, mock_db_session):
        """Test set_pin shows PIN entry prompt for eligible user"""
        # Mock campaign creator without PIN
        user = User(
            id=1,
            telegram_user_id="123456",
            role=UserRole.CAMPAIGN_CREATOR,
            email="creator@test.com"
        )
        
        update = MagicMock(spec=Update)
        update.effective_user.id = 123456
        update.message = AsyncMock(spec=Message)
        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        
        mock_db_session.query.return_value.filter_by.return_value.first.return_value = user
        
        # Execute
        result = await set_pin_command(update, context)
        
        # Verify
        update.message.reply_text.assert_called_once()
        assert "Set Your 4-Digit PIN" in update.message.reply_text.call_args[0][0]
        assert result == ENTERING_NEW_PIN


class TestPinValidation:
    """Test PIN validation during entry"""
    
    @pytest.mark.asyncio
    async def test_reject_weak_pin_1234(self):
        """Test rejection of weak PIN 1234"""
        update = MagicMock(spec=Update)
        update.message = AsyncMock(spec=Message)
        update.message.text = "1234"
        update.effective_user = MagicMock()
        update.effective_user.send_message = AsyncMock()
        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        context.user_data = {}
        
        # Execute
        result = await handle_new_pin_entry(update, context)
        
        # Verify
        update.effective_user.send_message.assert_called_once()
        assert "Weak PIN detected" in update.effective_user.send_message.call_args[0][0]
        assert result == ENTERING_NEW_PIN
    
    @pytest.mark.asyncio
    async def test_reject_weak_pin_0000(self):
        """Test rejection of weak PIN 0000"""
        update = MagicMock(spec=Update)
        update.message = AsyncMock(spec=Message)
        update.message.text = "0000"
        update.effective_user = MagicMock()
        update.effective_user.send_message = AsyncMock()
        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        context.user_data = {}
        
        # Execute
        result = await handle_new_pin_entry(update, context)
        
        # Verify
        update.effective_user.send_message.assert_called_once()
        assert "Weak PIN detected" in update.effective_user.send_message.call_args[0][0]
        assert result == ENTERING_NEW_PIN
    
    @pytest.mark.asyncio
    async def test_reject_non_digit_pin(self):
        """Test rejection of non-digit PIN"""
        update = MagicMock(spec=Update)
        update.message = AsyncMock(spec=Message)
        update.message.text = "abcd"
        update.effective_user = MagicMock()
        update.effective_user.send_message = AsyncMock()
        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        context.user_data = {}
        
        # Execute
        result = await handle_new_pin_entry(update, context)
        
        # Verify
        update.effective_user.send_message.assert_called_once()
        assert "Invalid PIN format" in update.effective_user.send_message.call_args[0][0]
        assert result == ENTERING_NEW_PIN
    
    @pytest.mark.asyncio
    async def test_reject_wrong_length_pin(self):
        """Test rejection of wrong length PIN"""
        update = MagicMock(spec=Update)
        update.message = AsyncMock(spec=Message)
        update.message.text = "123"  # Only 3 digits
        update.effective_user = MagicMock()
        update.effective_user.send_message = AsyncMock()
        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        context.user_data = {}
        
        # Execute
        result = await handle_new_pin_entry(update, context)
        
        # Verify
        update.effective_user.send_message.assert_called_once()
        assert "Invalid PIN format" in update.effective_user.send_message.call_args[0][0]
        assert result == ENTERING_NEW_PIN
    
    @pytest.mark.asyncio
    async def test_accept_valid_pin(self):
        """Test acceptance of valid PIN"""
        update = MagicMock(spec=Update)
        update.message = AsyncMock(spec=Message)
        update.message.text = "7392"  # Non-sequential, non-repeated
        update.effective_user = MagicMock()
        update.effective_user.send_message = AsyncMock()
        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        context.user_data = {}
        
        # Execute
        result = await handle_new_pin_entry(update, context)
        
        # Verify
        update.effective_user.send_message.assert_called_once()
        assert "PIN accepted" in update.effective_user.send_message.call_args[0][0]
        assert "confirm" in update.effective_user.send_message.call_args[0][0].lower()
        assert context.user_data['new_pin'] == "7392"
        assert result == CONFIRMING_NEW_PIN


class TestPinConfirmation:
    """Test PIN confirmation"""
    
    @pytest.mark.asyncio
    async def test_pin_mismatch(self):
        """Test PIN confirmation mismatch"""
        update = MagicMock(spec=Update)
        update.message = AsyncMock(spec=Message)
        update.message.text = "9999"
        update.effective_user = MagicMock()
        update.effective_user.send_message = AsyncMock()
        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        context.user_data = {'new_pin': '5678'}
        
        # Execute
        result = await handle_pin_confirmation(update, context)
        
        # Verify
        update.effective_user.send_message.assert_called_once()
        assert "don't match" in update.effective_user.send_message.call_args[0][0]
        assert 'new_pin' not in context.user_data  # Should clear stored PIN
        assert result == ENTERING_NEW_PIN
    
    @pytest.mark.asyncio
    async def test_pin_confirmation_success(self, mock_db_session):
        """Test successful PIN confirmation and storage"""
        # Mock user
        user = User(
            id=1,
            telegram_user_id="123456",
            role=UserRole.CAMPAIGN_CREATOR,
            telegram_username="testuser",
            email="test@test.com"
        )
        
        update = MagicMock(spec=Update)
        update.message = AsyncMock(spec=Message)
        update.message.text = "5678"
        update.effective_user = MagicMock()
        update.effective_user.id = 123456
        update.effective_user.send_message = AsyncMock()
        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        context.user_data = {'new_pin': '5678'}
        
        mock_db_session.query.return_value.filter_by.return_value.first.return_value = user
        
        # Execute
        result = await handle_pin_confirmation(update, context)
        
        # Verify
        assert user.pin_hash is not None
        assert verify_pin("5678", user.pin_hash)
        assert user.pin_set_at is not None
        mock_db_session.commit.assert_called_once()
        
        update.effective_user.send_message.assert_called_once()
        assert "PIN set successfully" in update.effective_user.send_message.call_args[0][0]
        assert "testuser" in update.effective_user.send_message.call_args[0][0]
        assert result == -1  # ConversationHandler.END


class TestChangePinCommand:
    """Test /change_pin command"""
    
    @pytest.mark.asyncio
    async def test_change_pin_no_existing_pin(self, mock_db_session):
        """Test change_pin when no PIN is set"""
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
        
        # Execute
        result = await change_pin_command(update, context)
        
        # Verify
        update.message.reply_text.assert_called_once()
        assert "don't have a PIN" in update.message.reply_text.call_args[0][0]
        assert "/set_pin" in update.message.reply_text.call_args[0][0]
        assert result == -1  # ConversationHandler.END
    
    @pytest.mark.asyncio
    async def test_change_pin_prompt(self, mock_db_session):
        """Test change_pin shows old PIN prompt"""
        user = User(
            id=1,
            telegram_user_id="123456",
            role=UserRole.CAMPAIGN_CREATOR,
            pin_hash=hash_pin("5678"),
            email="test@test.com"
        )
        
        update = MagicMock(spec=Update)
        update.effective_user.id = 123456
        update.message = AsyncMock(spec=Message)
        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        
        mock_db_session.query.return_value.filter_by.return_value.first.return_value = user
        
        # Execute
        result = await change_pin_command(update, context)
        
        # Verify
        update.message.reply_text.assert_called_once()
        assert "current PIN" in update.message.reply_text.call_args[0][0]
        assert result == ENTERING_OLD_PIN
    
    @pytest.mark.asyncio
    async def test_old_pin_verification_wrong(self, mock_db_session):
        """Test old PIN verification with wrong PIN"""
        user = User(
            id=1,
            telegram_user_id="123456",
            role=UserRole.CAMPAIGN_CREATOR,
            pin_hash=hash_pin("5678"),
            email="test@test.com"
        )
        
        update = MagicMock(spec=Update)
        update.message = AsyncMock(spec=Message)
        update.message.text = "9999"  # Wrong PIN
        update.effective_user = MagicMock()
        update.effective_user.id = 123456
        update.effective_user.send_message = AsyncMock()
        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        
        mock_db_session.query.return_value.filter_by.return_value.first.return_value = user
        
        # Execute
        result = await handle_old_pin_entry(update, context)
        
        # Verify
        update.effective_user.send_message.assert_called_once()
        assert "Incorrect PIN" in update.effective_user.send_message.call_args[0][0]
        assert result == ENTERING_OLD_PIN
    
    @pytest.mark.asyncio
    async def test_old_pin_verification_correct(self, mock_db_session):
        """Test old PIN verification with correct PIN"""
        user = User(
            id=1,
            telegram_user_id="123456",
            role=UserRole.CAMPAIGN_CREATOR,
            pin_hash=hash_pin("5678"),
            email="test@test.com"
        )
        
        update = MagicMock(spec=Update)
        update.message = AsyncMock(spec=Message)
        update.message.text = "5678"  # Correct PIN
        update.effective_user = MagicMock()
        update.effective_user.id = 123456
        update.effective_user.send_message = AsyncMock()
        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        
        mock_db_session.query.return_value.filter_by.return_value.first.return_value = user
        
        # Execute
        result = await handle_old_pin_entry(update, context)
        
        # Verify
        update.effective_user.send_message.assert_called_once()
        assert "verified" in update.effective_user.send_message.call_args[0][0].lower()
        assert "new" in update.effective_user.send_message.call_args[0][0].lower()
        assert result == ENTERING_NEW_PIN


# Fixtures
@pytest.fixture
def mock_db_session():
    """Mock database session"""
    with patch('voice.telegram.pin_commands.get_db') as mock_get_db:
        mock_session = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_session
        yield mock_session
