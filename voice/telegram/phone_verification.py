"""
Phone Verification for IVR Access

Telegram command to verify phone number using native contact sharing.
Enables future IVR (Interactive Voice Response) access for feature phones.

Commands:
- /verify_phone - Initiate phone verification
- Contact share handler - Process shared contact
"""

import logging
from datetime import datetime
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes

from database.db import get_db
from database.models import User

logger = logging.getLogger(__name__)


async def verify_phone_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    /verify_phone - Verify phone number for IVR access.
    
    Uses Telegram's native contact sharing (secure, no SMS costs).
    Telegram provides verified phone in E.164 format.
    """
    user_id = update.effective_user.id
    
    with get_db() as db:
        user = db.query(User).filter_by(telegram_user_id=str(user_id)).first()
        
        if not user:
            await update.message.reply_text(
                "❌ User not found.\n\n"
                "Please register first using /register"
            )
            return
        
        # Check if already verified
        if user.phone_verified_at:
            await update.message.reply_text(
                f"✅ Phone already verified: {user.phone_number}\n\n"
                f"🎉 You can access TrustVoice via:\n"
                f"• Telegram (voice & text) ✅\n"
                f"• Web UI ✅\n"
                f"• IVR phone system (coming soon) 🔜\n\n"
                f"Questions? Send /help"
            )
            return
    
    # Native Telegram contact sharing button
    keyboard = [
        [KeyboardButton("📞 Share My Phone Number", request_contact=True)]
    ]
    reply_markup = ReplyKeyboardMarkup(
        keyboard,
        one_time_keyboard=True,
        resize_keyboard=True
    )
    
    await update.message.reply_text(
        "📞 Verify Your Phone Number\n\n"
        "**Why verify?**\n"
        "• Call TrustVoice toll-free IVR (future)\n"
        "• Donate via USSD for feature phones\n"
        "• No smartphone required\n"
        "• Secure - verified by Telegram\n\n"
        "**How it works:**\n"
        "1. Tap the button below\n"
        "2. Telegram confirms it's your number\n"
        "3. Done! ✅\n\n"
        "Click the button to continue:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


async def handle_contact_share(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle contact sharing from Telegram.
    
    Telegram provides verified phone number in E.164 format (+254712...).
    Validates contact is from user themselves (anti-fraud).
    """
    contact = update.message.contact
    user_id = update.effective_user.id
    
    if not contact:
        logger.warning(f"Contact share handler called without contact data")
        return
    
    phone_number = contact.phone_number
    
    # Critical security check: Contact must be from user themselves
    if contact.user_id != user_id:
        await update.message.reply_text(
            "⚠️ Security Check Failed\n\n"
            "Please share YOUR OWN contact, not someone else's.\n\n"
            "Send /verify_phone to try again.",
            reply_markup=ReplyKeyboardRemove()
        )
        return
    
    # Ensure phone number is in E.164 format
    if not phone_number.startswith('+'):
        phone_number = '+' + phone_number
    
    with get_db() as db:
        user = db.query(User).filter_by(telegram_user_id=str(user_id)).first()
        
        if not user:
            await update.message.reply_text(
                "❌ User not found. Please register first using /register",
                reply_markup=ReplyKeyboardRemove()
            )
            return
        
        # Check if phone already used by another user
        existing_user = db.query(User).filter(
            User.phone_number == phone_number,
            User.id != user.id
        ).first()
        
        if existing_user:
            await update.message.reply_text(
                "❌ Phone Number Already Registered\n\n"
                "This phone number is already linked to another TrustVoice account.\n\n"
                "Each phone can only be verified once.\n"
                "Contact support if you believe this is an error.",
                reply_markup=ReplyKeyboardRemove()
            )
            return
        
        # Store verified phone number
        user.phone_number = phone_number
        user.phone_verified_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"Phone verified for user {user_id}: {phone_number}")
        
        # Success message with access summary
        role_access = ""
        if user.role.value == "CAMPAIGN_CREATOR":
            role_access = (
                "\n**Your Access:**\n"
                "• Create campaigns via web\n"
                "• Track donations\n"
                "• Request payouts\n"
                "• Voice donations via Telegram\n"
                "• IVR donations (coming soon)"
            )
        elif user.role.value == "FIELD_AGENT":
            role_access = (
                "\n**Your Access:**\n"
                "• Verify campaigns via web\n"
                "• Submit GPS verification\n"
                "• Impact reports\n"
                "• Voice reports via Telegram\n"
                "• IVR reports (coming soon)"
            )
        else:  # DONOR
            role_access = (
                "\n**Your Access:**\n"
                "• Voice donations via Telegram\n"
                "• Track donation history\n"
                "• Blockchain receipts\n"
                "• IVR donations (coming soon)"
            )
        
        await update.message.reply_text(
            f"✅ Phone Verified Successfully!\n\n"
            f"📱 Number: {phone_number}\n"
            f"🕐 Verified: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}\n"
            f"{role_access}\n\n"
            f"🎉 You're all set! Future IVR access will use this number.\n\n"
            f"Questions? Send /help",
            reply_markup=ReplyKeyboardRemove(),
            parse_mode='Markdown'
        )


async def unverify_phone_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    /unverify_phone - Remove phone verification (for testing/admin use).
    
    Allows user to verify a different phone number.
    """
    user_id = update.effective_user.id
    
    with get_db() as db:
        user = db.query(User).filter_by(telegram_user_id=str(user_id)).first()
        
        if not user:
            await update.message.reply_text("❌ User not found.")
            return
        
        if not user.phone_verified_at:
            await update.message.reply_text(
                "ℹ️ No phone number verified.\n\n"
                "Use /verify_phone to verify your phone."
            )
            return
        
        old_phone = user.phone_number
        user.phone_number = None
        user.phone_verified_at = None
        db.commit()
        
        logger.info(f"Phone unverified for user {user_id}: {old_phone}")
        
        await update.message.reply_text(
            f"✅ Phone verification removed.\n\n"
            f"Previous number: {old_phone}\n\n"
            f"You can verify a different number using /verify_phone"
        )
