"""
Registration Handler
Handles new user registration with role-based flows

Flows:
1. Donor: Instant registration (no approval)
2. Campaign Creator: Multi-step form → Admin approval
3. Field Agent: Multi-step form → Admin approval
"""

import logging
from datetime import datetime
from typing import Optional

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    ConversationHandler,
    CallbackQueryHandler,
    ContextTypes
)

from database.db import SessionLocal
from database.models import User, PendingRegistration, UserRole
from services.auth_service import hash_pin, is_weak_pin
from voice.telegram.session_manager import RegistrationSession

logger = logging.getLogger(__name__)

# Conversation states
SELECTING_ROLE = 1
SELECTING_LANGUAGE = 2
ENTERING_FULL_NAME = 3
ENTERING_ORG_NAME = 4
ENTERING_LOCATION = 5
ENTERING_PHONE = 6
ENTERING_REASON = 7
# Campaign Creator specific
ENTERING_VERIFICATION_EXP = 8
# Field Agent specific
ENTERING_COVERAGE_REGIONS = 9
ENTERING_GPS_PHONE = 10
# PIN setup
ENTERING_PIN = 11
CONFIRMING_PIN = 12


async def register_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /register command - Start registration flow"""
    user = update.effective_user
    telegram_user_id = str(user.id)
    
    logger.info(f"User {user.first_name} ({telegram_user_id}) started registration")
    
    # Check if already registered
    db = SessionLocal()
    try:
        existing_user = db.query(User).filter(
            User.telegram_user_id == telegram_user_id
        ).first()
        
        if existing_user:
            await update.message.reply_text(
                "✅ You are already registered!\n\n"
                "Use /help to see what you can do."
            )
            return ConversationHandler.END
        
        # Check if pending registration exists
        pending = db.query(PendingRegistration).filter(
            PendingRegistration.telegram_user_id == telegram_user_id,
            PendingRegistration.status == "PENDING"
        ).first()
        
        if pending:
            await update.message.reply_text(
                "⏳ Your registration is pending admin approval.\n\n"
                f"Role requested: {pending.requested_role}\n"
                "We'll notify you once approved!"
            )
            return ConversationHandler.END
    finally:
        db.close()
    
    # Start new registration - Role selection
    message = (
        f"Welcome {user.first_name}! 🎤\n\n"
        "TrustVoice connects donors with verified campaigns.\n\n"
        "Please select your role:"
    )
    
    keyboard = [
        [InlineKeyboardButton("🎁 Donor - I want to donate", callback_data="role:DONOR")],
        [InlineKeyboardButton("📢 Campaign Creator - I need funding", callback_data="role:CAMPAIGN_CREATOR")],
        [InlineKeyboardButton("✅ Field Agent - I verify campaigns", callback_data="role:FIELD_AGENT")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(message, reply_markup=reply_markup)
    
    # Initialize session
    session = RegistrationSession(telegram_user_id)
    session.set({
        "telegram_username": user.username,
        "telegram_first_name": user.first_name,
        "telegram_last_name": user.last_name,
        "step": "role_selection"
    })
    
    return SELECTING_ROLE


async def handle_role_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle role selection from inline button"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    telegram_user_id = str(user.id)
    role_data = query.data.split(":")[1]
    
    session = RegistrationSession(telegram_user_id)
    session.update({"requested_role": role_data})
    
    # Ask for language preference for all roles
    message = "🌍 Select your preferred language for voice interactions:"
    keyboard = [
        [InlineKeyboardButton("🇬🇧 English", callback_data="lang:en")],
        [InlineKeyboardButton("🇰🇪 Swahili (Kiswahili)", callback_data="lang:sw")],
        [InlineKeyboardButton("🇪🇹 Amharic (አማርኛ)", callback_data="lang:am")],
        [InlineKeyboardButton("🇫🇷 French (Français)", callback_data="lang:fr")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(message, reply_markup=reply_markup)
    return SELECTING_LANGUAGE


async def handle_language_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle language preference selection"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    telegram_user_id = str(user.id)
    language_code = query.data.split(":")[1]
    
    session = RegistrationSession(telegram_user_id)
    session.update({"preferred_language": language_code})
    data = session.get()
    role_data = data.get("requested_role")
    
    # Parse role
    if role_data == "DONOR":
        # DONOR: Instant registration with language preference
        db = SessionLocal()
        try:
            new_user = User(
                telegram_user_id=telegram_user_id,
                telegram_username=user.username,
                telegram_first_name=user.first_name,
                telegram_last_name=user.last_name,
                role=UserRole.DONOR,
                preferred_language=language_code,
                is_approved=True,
                approved_at=datetime.utcnow()
            )
            db.add(new_user)
            db.commit()
            
            logger.info(f"Donor registered: {telegram_user_id} (lang: {language_code})")
            
            language_names = {"en": "English", "sw": "Swahili", "am": "Amharic", "fr": "French"}
            await query.edit_message_text(
                f"✅ Registration complete! Language: {language_names.get(language_code, language_code)}\n\n"
                "As a donor, you can:\n"
                "🎤 Browse campaigns via voice\n"
                "💰 Make donations\n"
                "📊 Track your impact\n\n"
                "Try: \"Show me water projects in Ethiopia\""
            )
            
            session.delete()
            return ConversationHandler.END
            
        except Exception as e:
            logger.error(f"Donor registration failed: {e}")
            await query.edit_message_text(
                "❌ Registration failed. Please try again with /register"
            )
            session.delete()
            return ConversationHandler.END
        finally:
            db.close()
    
    elif role_data == "CAMPAIGN_CREATOR":
        # CAMPAIGN_CREATOR: Multi-step form
        await query.edit_message_text(
            "📢 Campaign Creator Registration\n\n"
            "Your account requires admin approval.\n"
            "We'll ask a few questions to verify your identity.\n\n"
            "Step 1 of 7: What is your full name?"
        )
        
        return ENTERING_FULL_NAME
    
    elif role_data == "FIELD_AGENT":
        # FIELD_AGENT: Multi-step form
        
        await query.edit_message_text(
            "✅ Field Agent Registration\n\n"
            "Your account requires admin approval.\n"
            "We'll ask a few questions to verify your credentials.\n\n"
            "Step 1 of 7: What is your full name?"
        )
        
        return ENTERING_FULL_NAME
    
    else:
        await query.edit_message_text("Invalid selection. Please use /register to try again.")
        return ConversationHandler.END


# Multi-step form handlers
async def handle_full_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 2: Full name"""
    user = update.effective_user
    telegram_user_id = str(user.id)
    
    session = RegistrationSession(telegram_user_id)
    session.update({"full_name": update.message.text})
    
    await update.message.reply_text("Step 2 of 7: What is your organization name?")
    return ENTERING_ORG_NAME


async def handle_org_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 3: Organization name"""
    user = update.effective_user
    telegram_user_id = str(user.id)
    
    session = RegistrationSession(telegram_user_id)
    session.update({"organization_name": update.message.text})
    
    await update.message.reply_text("Step 3 of 7: What is your location (city, country)?")
    return ENTERING_LOCATION


async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 4: Location"""
    user = update.effective_user
    telegram_user_id = str(user.id)
    
    session = RegistrationSession(telegram_user_id)
    session.update({"location": update.message.text})
    
    await update.message.reply_text(
        "Step 4 of 7: What is your phone number?\n"
        "(Optional - for identity verification, type 'skip' if none)"
    )
    return ENTERING_PHONE


async def handle_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 5: Phone number"""
    user = update.effective_user
    telegram_user_id = str(user.id)
    
    session = RegistrationSession(telegram_user_id)
    data = session.get()
    
    phone = update.message.text
    if phone.lower() in ["skip", "no", "none"]:
        phone = None
    
    session.update({"phone_number": phone})
    
    # Branch based on role
    requested_role = data.get("requested_role")
    
    if requested_role == "CAMPAIGN_CREATOR":
        await update.message.reply_text(
            "Step 5 of 7: Why do you need funding? Describe your campaign.\n"
            "(Be specific about the problem you're solving)"
        )
        return ENTERING_REASON
    
    elif requested_role == "FIELD_AGENT":
        await update.message.reply_text(
            "Step 5 of 7: Do you have experience verifying campaigns or projects?\n"
            "Describe your relevant experience."
        )
        return ENTERING_VERIFICATION_EXP
    
    return ConversationHandler.END


# Campaign Creator specific
async def handle_reason(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 6: Reason for campaign"""
    user = update.effective_user
    telegram_user_id = str(user.id)
    
    session = RegistrationSession(telegram_user_id)
    session.update({"reason": update.message.text})
    
    await update.message.reply_text(
        "Step 6 of 7: Do you have experience with campaign verification?\n"
        "(Have you worked with NGOs, donors, or verification systems?)"
    )
    return ENTERING_VERIFICATION_EXP


# Field Agent specific
async def handle_verification_exp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 6: Verification experience"""
    user = update.effective_user
    telegram_user_id = str(user.id)
    
    session = RegistrationSession(telegram_user_id)
    data = session.get()
    session.update({"verification_experience": update.message.text})
    
    requested_role = data.get("requested_role")
    
    if requested_role == "FIELD_AGENT":
        await update.message.reply_text(
            "Step 7 of 8: Which regions can you cover for verification?\n"
            "(List cities/regions where you can visit campaigns)"
        )
        return ENTERING_COVERAGE_REGIONS
    else:
        # Campaign Creator - go to PIN
        await update.message.reply_text(
            "Step 7 of 7: Set a 4-digit PIN for web access\n\n"
            "This PIN will let you access the web dashboard.\n"
            "❌ Don't use: 0000, 1234, 1111, etc.\n\n"
            "Enter your 4-digit PIN:"
        )
        return ENTERING_PIN


async def handle_coverage_regions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 7: Coverage regions (Field Agent only)"""
    user = update.effective_user
    telegram_user_id = str(user.id)
    
    session = RegistrationSession(telegram_user_id)
    session.update({"coverage_regions": update.message.text})
    
    keyboard = [
        [InlineKeyboardButton("✅ Yes, I have GPS", callback_data="gps:yes")],
        [InlineKeyboardButton("❌ No, I don't have GPS", callback_data="gps:no")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "Step 8 of 9: Do you have a smartphone with GPS?\n"
        "(GPS is required for location verification)",
        reply_markup=reply_markup
    )
    return ENTERING_GPS_PHONE


async def handle_gps_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 8: GPS phone (Field Agent only) - Handle inline button"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    telegram_user_id = str(user.id)
    
    session = RegistrationSession(telegram_user_id)
    
    has_gps = query.data.split(":")[1] == "yes"
    session.update({"has_gps_phone": has_gps})
    
    await query.message.reply_text(
        "Step 9 of 9: Set a 4-digit PIN for verification tools\n\n"
        "This PIN will let you access verification features.\n"
        "❌ Don't use: 0000, 1234, 1111, etc.\n\n"
        "Enter your 4-digit PIN:"
    )
    return ENTERING_PIN


# PIN setup
async def handle_pin_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle PIN entry"""
    user = update.effective_user
    telegram_user_id = str(user.id)
    pin = update.message.text.strip()
    
    # Delete message for security
    try:
        await update.message.delete()
    except:
        pass
    
    # Validate PIN
    if not pin.isdigit() or len(pin) != 4:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="❌ PIN must be exactly 4 digits. Try again:"
        )
        return ENTERING_PIN
    
    is_weak, reason = is_weak_pin(pin)
    if is_weak:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"❌ PIN is too weak ({reason}). Try again:"
        )
        return ENTERING_PIN
    
    # Store PIN temporarily
    session = RegistrationSession(telegram_user_id)
    session.update({"temp_pin": pin})
    
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Confirm your PIN (enter again):"
    )
    return CONFIRMING_PIN


async def handle_pin_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle PIN confirmation"""
    user = update.effective_user
    telegram_user_id = str(user.id)
    pin_confirm = update.message.text.strip()
    
    # Delete message for security
    try:
        await update.message.delete()
    except:
        pass
    
    session = RegistrationSession(telegram_user_id)
    data = session.get()
    
    if not data:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="❌ Session expired. Please start over with /register"
        )
        return ConversationHandler.END
    
    temp_pin = data.get("temp_pin")
    
    if pin_confirm != temp_pin:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="❌ PINs don't match. Let's start PIN setup again.\n\nEnter your 4-digit PIN:"
        )
        session.update({"temp_pin": None})
        return ENTERING_PIN
    
    # Hash PIN
    pin_hash = hash_pin(temp_pin)
    
    # Save to pending_registrations
    db = SessionLocal()
    try:
        pending = PendingRegistration(
            telegram_user_id=telegram_user_id,
            telegram_username=data.get("telegram_username"),
            telegram_first_name=data.get("telegram_first_name"),
            telegram_last_name=data.get("telegram_last_name"),
            requested_role=data.get("requested_role"),
            full_name=data.get("full_name"),
            organization_name=data.get("organization_name"),
            location=data.get("location"),
            phone_number=data.get("phone_number"),
            reason=data.get("reason"),
            verification_experience=data.get("verification_experience"),
            coverage_regions=data.get("coverage_regions"),
            has_gps_phone=data.get("has_gps_phone"),
            preferred_language=data.get("preferred_language", "en"),
            pin_hash=pin_hash,
            status="PENDING"
        )
        db.add(pending)
        db.commit()
        
        logger.info(f"Pending registration created: {telegram_user_id} ({data.get('requested_role')})")
        
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=(
                "✅ Registration submitted!\n\n"
                f"Role: {data.get('requested_role')}\n"
                "Status: Pending admin approval\n\n"
                "We'll notify you once your account is approved.\n"
                "This usually takes 24-48 hours."
            )
        )
        
        # TODO: Notify admins about new pending registration
        
        session.delete()
        return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"Failed to save pending registration: {e}")
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="❌ Registration failed. Please try again with /register"
        )
        session.delete()
        return ConversationHandler.END
    finally:
        db.close()


async def cancel_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel registration"""
    user = update.effective_user
    telegram_user_id = str(user.id)
    
    session = RegistrationSession(telegram_user_id)
    session.delete()
    
    await update.message.reply_text(
        "Registration cancelled.\n\nYou can start again with /register"
    )
    return ConversationHandler.END
