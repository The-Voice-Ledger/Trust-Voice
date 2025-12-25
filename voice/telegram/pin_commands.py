"""
PIN Management Commands

Telegram commands for setting and changing 4-digit PINs.
PINs enable web UI and IVR access for approved users.

Commands:
- /set_pin - Set PIN (if not already set)
- /change_pin - Change existing PIN
"""

import logging
from datetime import datetime
from telegram import Update, ReplyKeyboardRemove
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    filters
)

from database.db import get_db
from database.models import User, UserRole
from services.auth_service import hash_pin, verify_pin, is_weak_pin

logger = logging.getLogger(__name__)

# Conversation states
ENTERING_NEW_PIN, CONFIRMING_NEW_PIN, ENTERING_OLD_PIN = range(3)


async def set_pin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    /set_pin - Set PIN for web/IVR access (if not already set).
    """
    user_id = update.effective_user.id
    
    with get_db() as db:
        user = db.query(User).filter_by(telegram_user_id=str(user_id)).first()
        
        if not user:
            await update.message.reply_text(
                "❌ User not found.\n\n"
                "Please register first using /register"
            )
            return ConversationHandler.END
        
        # Check if PIN already set
        if user.pin_hash:
            await update.message.reply_text(
                "ℹ️ You already have a PIN set.\n\n"
                "To change it, use /change_pin\n"
                "To cancel, send /cancel"
            )
            return ConversationHandler.END
        
        # Check user role - Donors don't need PINs
        # Allow: CAMPAIGN_CREATOR, FIELD_AGENT, SYSTEM_ADMIN
        if user.role == UserRole.DONOR:
            await update.message.reply_text(
                "ℹ️ As a Donor, you don't need a PIN.\n\n"
                "Donors use Telegram only for voice donations.\n"
                "Web access is for Campaign Creators and Field Agents.\n\n"
                "Questions? Send /help"
            )
            return ConversationHandler.END
        
        # Admins can always set PINs (for testing and web access)
        # Campaign Creators and Field Agents need PINs for web access
    
    await update.message.reply_text(
        "🔐 Set Your 4-Digit PIN\n\n"
        "This PIN lets you login to the web interface at:\n"
        "https://trustvoice.app\n\n"
        "**PIN Requirements:**\n"
        "• Exactly 4 digits (0-9)\n"
        "• Avoid weak PINs:\n"
        "  ❌ 1234, 0000, 1111\n"
        "  ❌ Sequential: 2345, 6789\n"
        "  ❌ Repeated: 2222, 7777\n\n"
        "✅ Good examples: 7392, 2859, 4618\n\n"
        "Enter your 4-digit PIN:",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode='Markdown'
    )
    
    return ENTERING_NEW_PIN


async def handle_new_pin_entry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle user entering new PIN."""
    pin = update.message.text.strip()
    
    # Delete PIN message immediately (security)
    try:
        await update.message.delete()
    except Exception as e:
        logger.warning(f"Could not delete PIN message: {e}")
    
    # Validate format
    if not pin.isdigit() or len(pin) != 4:
        await update.effective_user.send_message(
            "❌ Invalid PIN format.\n\n"
            "PIN must be exactly 4 digits (0-9).\n\n"
            "Try again:"
        )
        return ENTERING_NEW_PIN
    
    # Check weak PINs
    is_weak, reason = is_weak_pin(pin)
    if is_weak:
        await update.effective_user.send_message(
            f"⚠️ Weak PIN detected: {reason}\n\n"
            f"For security, please choose a stronger PIN.\n"
            f"Avoid: 1234, 0000, 1111, 1212, etc.\n\n"
            f"Enter a different PIN:"
        )
        return ENTERING_NEW_PIN
    
    # Store PIN temporarily in context
    context.user_data['new_pin'] = pin
    
    await update.effective_user.send_message(
        "✅ PIN accepted.\n\n"
        "Now confirm your PIN by entering it again:"
    )
    
    return CONFIRMING_NEW_PIN


async def handle_pin_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle PIN confirmation."""
    confirmation_pin = update.message.text.strip()
    
    # Delete confirmation message immediately (security)
    try:
        await update.message.delete()
    except Exception as e:
        logger.warning(f"Could not delete confirmation message: {e}")
    
    new_pin = context.user_data.get('new_pin')
    
    if not new_pin:
        await update.effective_user.send_message(
            "❌ Session expired. Please start over with /set_pin"
        )
        return ConversationHandler.END
    
    # Check if PINs match
    if confirmation_pin != new_pin:
        await update.effective_user.send_message(
            "❌ PINs don't match.\n\n"
            "Let's try again. Enter your PIN:"
        )
        # Clear stored PIN
        context.user_data.pop('new_pin', None)
        return ENTERING_NEW_PIN
    
    # PINs match - save to database
    user_id = update.effective_user.id
    
    try:
        with get_db() as db:
            user = db.query(User).filter_by(telegram_user_id=str(user_id)).first()
            
            if not user:
                await update.effective_user.send_message("❌ User not found.")
                return ConversationHandler.END
            
            # Hash and store PIN
            user.pin_hash = hash_pin(new_pin)
            user.pin_set_at = datetime.utcnow()
            db.commit()
            
            username = user.telegram_username or user.email or "your_username"
            
            await update.effective_user.send_message(
                "✅ PIN set successfully!\n\n"
                "🌐 You can now login to the web interface:\n\n"
                "**Web Login:**\n"
                f"Username: `{username}`\n"
                "PIN: [The 4 digits you just set]\n\n"
                "🔒 Keep your PIN secure. Don't share it.\n"
                "To change it later, use /change_pin",
                parse_mode='Markdown'
            )
            
            # Clear temporary data
            context.user_data.pop('new_pin', None)
            
            logger.info(f"PIN set successfully for user {user_id}")
            
    except Exception as e:
        logger.error(f"Error setting PIN: {e}")
        await update.effective_user.send_message(
            "❌ Error setting PIN. Please try again later."
        )
    
    return ConversationHandler.END


async def change_pin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    /change_pin - Change existing PIN.
    """
    user_id = update.effective_user.id
    
    with get_db() as db:
        user = db.query(User).filter_by(telegram_user_id=str(user_id)).first()
        
        if not user:
            await update.message.reply_text(
                "❌ User not found.\n\n"
                "Please register first using /register"
            )
            return ConversationHandler.END
        
        # Check if PIN is set
        if not user.pin_hash:
            await update.message.reply_text(
                "ℹ️ You don't have a PIN set yet.\n\n"
                "Use /set_pin to create one.\n"
                "To cancel, send /cancel"
            )
            return ConversationHandler.END
    
    await update.message.reply_text(
        "🔐 Change Your PIN\n\n"
        "First, verify your current PIN.\n\n"
        "Enter your current PIN:",
        reply_markup=ReplyKeyboardRemove()
    )
    
    return ENTERING_OLD_PIN


async def handle_old_pin_entry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle user entering old PIN for verification."""
    old_pin = update.message.text.strip()
    
    # Delete PIN message immediately (security)
    try:
        await update.message.delete()
    except Exception as e:
        logger.warning(f"Could not delete old PIN message: {e}")
    
    # Validate format
    if not old_pin.isdigit() or len(old_pin) != 4:
        await update.effective_user.send_message(
            "❌ Invalid PIN format.\n\n"
            "PIN must be exactly 4 digits.\n\n"
            "Try again:"
        )
        return ENTERING_OLD_PIN
    
    # Verify old PIN
    user_id = update.effective_user.id
    
    with get_db() as db:
        user = db.query(User).filter_by(telegram_user_id=str(user_id)).first()
        
        if not user or not user.pin_hash:
            await update.effective_user.send_message(
                "❌ User not found or PIN not set."
            )
            return ConversationHandler.END
        
        # Check if PIN is correct
        if not verify_pin(old_pin, user.pin_hash):
            await update.effective_user.send_message(
                "❌ Incorrect PIN.\n\n"
                "Please try again or send /cancel to abort."
            )
            return ENTERING_OLD_PIN
    
    # Old PIN verified - proceed to new PIN
    await update.effective_user.send_message(
        "✅ Current PIN verified.\n\n"
        "Now enter your new 4-digit PIN:"
    )
    
    return ENTERING_NEW_PIN


async def cancel_pin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel PIN setup/change."""
    # Clear any stored data
    context.user_data.pop('new_pin', None)
    
    await update.message.reply_text(
        "❌ PIN setup cancelled.\n\n"
        "No changes were made.\n"
        "Send /help to see available commands.",
        reply_markup=ReplyKeyboardRemove()
    )
    
    return ConversationHandler.END


# ============================================================================
# Conversation Handlers Export
# ============================================================================

def get_set_pin_handler():
    """Return ConversationHandler for /set_pin command."""
    return ConversationHandler(
        entry_points=[CommandHandler('set_pin', set_pin_command)],
        states={
            ENTERING_NEW_PIN: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_new_pin_entry)
            ],
            CONFIRMING_NEW_PIN: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_pin_confirmation)
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel_pin_command)],
        per_message=False
    )


def get_change_pin_handler():
    """Return ConversationHandler for /change_pin command."""
    return ConversationHandler(
        entry_points=[CommandHandler('change_pin', change_pin_command)],
        states={
            ENTERING_OLD_PIN: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_old_pin_entry)
            ],
            ENTERING_NEW_PIN: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_new_pin_entry)
            ],
            CONFIRMING_NEW_PIN: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_pin_confirmation)
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel_pin_command)],
        per_message=False
    )
