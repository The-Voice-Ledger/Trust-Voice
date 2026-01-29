"""
TrustVoice Telegram Bot
Voice-first donation platform bot

Features:
- Voice message processing (primary)
- Text message fallback
- Multi-language support (English, Amharic)
- Conversation tracking
- User registration with language selection
"""

import os
import logging
from typing import Optional
from pathlib import Path

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)

# Import our voice pipeline and Celery tasks
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from voice.pipeline import format_response_for_user
from voice.nlu.context import ConversationContext
from voice.tasks.voice_tasks import process_voice_message_task
from database.db import SessionLocal
from database.models import User
from voice.command_router import route_command
from voice.context import get_context, update_context, store_search_results, set_current_campaign
# Import handlers to register them with command router
import voice.handlers
from voice.telegram.register_handler import (
    register_command,
    handle_role_selection,
    handle_language_selection,
    handle_full_name,
    handle_org_name,
    handle_location,
    handle_phone,
    handle_reason,
    handle_verification_exp,
    handle_coverage_regions,
    handle_gps_phone,
    handle_pin_entry,
    handle_pin_confirm,
    cancel_registration,
    SELECTING_ROLE,
    SELECTING_LANGUAGE,
    ENTERING_FULL_NAME,
    ENTERING_ORG_NAME,
    ENTERING_LOCATION,
    ENTERING_PHONE,
    ENTERING_REASON,
    ENTERING_VERIFICATION_EXP,
    ENTERING_COVERAGE_REGIONS,
    ENTERING_GPS_PHONE,
    ENTERING_PIN,
    CONFIRMING_PIN
)
from voice.telegram.admin_commands import (
    admin_requests_command,
    admin_approve_command,
    admin_reject_command
)
from voice.telegram.pin_commands import (
    get_set_pin_handler,
    get_change_pin_handler
)
from voice.telegram.phone_verification import (
    verify_phone_command,
    handle_contact_share,
    unverify_phone_command
)
from voice.telegram.field_agent_handlers import (
    handle_photo_message,
    handle_location_message,
    cancel_verification_command,
    my_verifications_command,
    pending_campaigns_command
)

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Environment variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
AUDIO_TEMP_DIR = Path(__file__).parent.parent.parent / "uploads" / "audio"
AUDIO_TEMP_DIR.mkdir(parents=True, exist_ok=True)

# Conversation states
SELECTING_LANGUAGE = 1

# In-memory user store (TODO: Replace with database)
users_db = {}


async def send_voice_reply(
    update: Update,
    text: str,
    language: Optional[str] = None,
    parse_mode: Optional[str] = "HTML"
):
    """
    Send both text and voice reply for accessibility (non-blocking).
    
    Uses dual delivery pattern:
    - Text sent immediately (0ms latency)
    - Voice generated in background (~2-3s)
    
    Args:
        update: Telegram update object
        text: Message text to send
        language: Language code for TTS (None = use user preference, "en" = English, "am" = Amharic)
        parse_mode: Telegram parse mode (HTML, Markdown, or None)
    """
    from voice.telegram.voice_responses import send_voice_reply_from_update
    
    await send_voice_reply_from_update(
        update=update,
        text=text,
        language=language,
        parse_mode=parse_mode,
        send_voice=True
    )


def get_user_language(telegram_user_id: str) -> str:
    """Get user's preferred language from database"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(
            User.telegram_user_id == telegram_user_id
        ).first()
        
        if user and user.preferred_language:
            return user.preferred_language
        
        # Fallback to in-memory cache or default
        cached = users_db.get(telegram_user_id, {})
        return cached.get("language", "en")
    finally:
        db.close()


def set_user_language(telegram_user_id: str, language: str):
    """Set user's preferred language in database and cache"""
    # Update in-memory cache
    if telegram_user_id not in users_db:
        users_db[telegram_user_id] = {}
    users_db[telegram_user_id]["language"] = language
    
    # Update database if user exists
    db = SessionLocal()
    try:
        user = db.query(User).filter(
            User.telegram_user_id == telegram_user_id
        ).first()
        
        if user:
            user.preferred_language = language
            db.commit()
            logger.info(f"User {telegram_user_id} language updated in DB: {language}")
        else:
            logger.info(f"User {telegram_user_id} language set in cache: {language}")
    finally:
        db.close()


def is_user_registered(telegram_user_id: str) -> bool:
    """Check if user has completed registration"""
    # Check in-memory cache first
    if telegram_user_id in users_db and "language" in users_db[telegram_user_id]:
        return True
    
    # Check database
    db = SessionLocal()
    try:
        user = db.query(User).filter(
            User.telegram_user_id == telegram_user_id
        ).first()
        
        if user and user.is_approved:
            # Load user into cache
            set_user_language(telegram_user_id, user.preferred_language or "en")
            return True
        
        return False
    finally:
        db.close()


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command - Check registration and show main menu"""
    user = update.effective_user
    telegram_user_id = str(user.id)
    
    logger.info(f"User {user.first_name} ({telegram_user_id}) started bot")
    
    # Check database for existing user
    db = SessionLocal()
    try:
        existing_user = db.query(User).filter(
            User.telegram_user_id == telegram_user_id
        ).first()
        
        if existing_user:
            # Load user's language preference into memory
            if existing_user.preferred_language:
                set_user_language(telegram_user_id, existing_user.preferred_language)
            
            # Registered user - Show main menu
            if existing_user.is_approved:
                # Build role-specific menu
                role_info = ""
                commands = "📋 Available commands:\n"
                
                if existing_user.role == "CAMPAIGN_CREATOR":
                    role_info = f"Role: Campaign Creator\n\n"
                    commands += "/set_pin - Set web login PIN\n"
                    commands += "/change_pin - Change your PIN\n"
                    commands += "/verify_phone - Verify phone for IVR\n"
                elif existing_user.role == "FIELD_AGENT":
                    role_info = f"Role: Field Agent\n\n"
                    commands += "/set_pin - Set web login PIN\n"
                    commands += "/change_pin - Change your PIN\n"
                    commands += "/verify_phone - Verify phone for IVR\n"
                elif existing_user.role == "DONOR":
                    role_info = f"Role: Donor\n\n"
                    commands += "/verify_phone - Verify phone for IVR\n"
                elif existing_user.role == "SYSTEM_ADMIN":
                    role_info = f"Role: System Admin\n\n"
                    commands += "/admin_requests - View pending registrations\n"
                    commands += "/admin_approve <id> - Approve user\n"
                    commands += "/admin_reject <id> <reason> - Reject user\n"
                
                commands += "/language - Change language\n"
                commands += "/help - Full help"
                
                message = (
                    f"Welcome back, {user.first_name}! 🎤\n\n"
                    f"{role_info}"
                    "What would you like to do?\n"
                    "🎤 Send a voice message\n"
                    "💬 Send a text message\n\n"
                    f"{commands}"
                )
                await send_voice_reply(
                    update=update,
                    text=message,
                    language=existing_user.preferred_language,
                    parse_mode=None
                )
                return
            else:
                # Pending approval
                await send_voice_reply(
                    update=update,
                    text=(
                        "⏳ Your account is pending approval.\n\n"
                        "You'll receive a notification here when approved!\n\n"
                        "Meanwhile:\n"
                        "/language - Change language\n"
                        "/help - Learn more about TrustVoice"
                    ),
                    language=existing_user.preferred_language
                )
                return
        
        # New user - Redirect to registration
        message = (
            f"Welcome to TrustVoice, {user.first_name}! 🎤\n\n"
            "I'm your voice-first donation platform.\n\n"
            "To get started, please register using:\n"
            "/register"
        )
        
        await send_voice_reply(
            update=update,
            text=message,
            language=None
        )
        
    finally:
        db.close()


async def language_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle language selection from inline button"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    telegram_user_id = str(user.id)
    language = query.data.split(":")[1]
    
    # Set language based on callback data
    if language == "en":
        language = "en"
        confirmation = (
            "✅ Language set to English!\n\n"
            "You can now:\n"
            "🎤 Send voice messages - I'll understand your requests\n"
            "💬 Send text messages - I'll help you find campaigns\n"
            "📋 Use /help to see what I can do\n\n"
            "Try saying: \"Show me water projects in Tanzania\""
        )
    elif language == "am":
        language = "am"
        confirmation = (
            "✅ ቋንቋ ወደ አማርኛ ተቀይሯል!\n\n"
            "አሁን ይችላሉ:\n"
            "🎤 የድምፅ መልእክቶችን ይላኩ - ጥያቄዎን እገነዘባለሁ\n"
            "💬 የጽሁፍ መልዕክቶችን ይላኩ - ዘመቻዎችን እረዳለሁ\n"
            "📋 /help ተጠቀም ምን ማድረግ እንደምችል ለማየት\n\n"
            "ይሞክሩ: \"በታንዛኒያ የውሃ ፕሮጀክቶችን አሳየኝ\""
        )
    else:
        await query.edit_message_text("Invalid selection. Please use /language to try again.")
        return ConversationHandler.END
    
    # Save language preference
    set_user_language(telegram_user_id, language)
    
    await query.edit_message_text(confirmation)
    
    return ConversationHandler.END


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    telegram_user_id = str(update.effective_user.id)
    language = get_user_language(telegram_user_id)
    
    if language == "am":
        help_text = (
            "📋 <b>የTrustVoice እገዛ</b>\n\n"
            "እኔ ምን ማድረግ እችላለሁ:\n"
            "🔍 ዘመቻዎችን መፈለግ\n"
            "💰 መዋጮዎችን ማድረግ\n"
            "📊 የእርስዎን ተፅእኖ መከታተል\n"
            "📈 የእርስዎን የዋጮ ታሪክ ማየት\n\n"
            "ምሳሌዎች:\n"
            "🎤 \"በታንዛኒያ የውሃ ፕሮጀክቶችን አሳየኝ\"\n"
            "🎤 \"50 ዶላር ለውሃ ፕሮጀክት መዋጮ አድርግ\"\n"
            "🎤 \"የእኔን የዋጮ ታሪክ አሳየኝ\"\n\n"
            "ትዕዛዞች:\n"
            "/start - መመዝገብ ወይም ምናሌ ማየት\n"
            "/register - ምዝገባ ጀምር\n"
            "/campaigns - ንቁ ዘመቻዎችን ማየት\n"
            "/donations - የእርስዎን የዋጮ ታሪክ ማየት\n"
            "/my_campaigns - የእርስዎን ዘመቻዎች ማየት\n"
            "/set_pin - ለድረገፅ መግቢያ ፒን አቀናብር\n"
            "/change_pin - ፒንዎን ይለውጡ\n"
            "/verify_phone - ስልክ ለIVR አረጋግጥ\n"
            "/language - ቋንቋ ቀይር\n"
            "/help - ይህን እገዛ አሳይ"
        )
    else:
        help_text = (
            "📋 <b>TrustVoice Help</b>\n\n"
            "What I can do:\n"
            "🔍 Find campaigns to support\n"
            "💰 Make donations\n"
            "📊 Track your impact\n"
            "📈 View donation history\n\n"
            "Examples:\n"
            "🎤 \"Show me water projects in Tanzania\"\n"
            "🎤 \"Donate $50 to the water project\"\n"
            "🎤 \"What's my donation history?\"\n\n"
            "Commands:\n"
            "/start - Register or view menu\n"
            "/register - Start registration\n"
            "/campaigns - Browse active campaigns\n"
            "/donations - View your donation history\n"
            "/my_campaigns - View your campaigns (creators only)\n"
            "/set_pin - Set PIN for web access\n"
            "/change_pin - Change your PIN\n"
            "/verify_phone - Verify phone for IVR\n"
            "/language - Change language\n"
            "/help - Show this help"
        )
    
    await update.message.reply_text(help_text, parse_mode="HTML")


async def language_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /language command - Change language"""
    keyboard = [
        [InlineKeyboardButton("🇬🇧 English", callback_data="lang:en")],
        [InlineKeyboardButton("🇪🇹 አማርኛ (Amharic)", callback_data="lang:am")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "Select your preferred language:",
        reply_markup=reply_markup
    )
    
    return SELECTING_LANGUAGE


async def campaigns_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /campaigns command - List active campaigns"""
    from database.db import SessionLocal
    from database.models import Campaign
    
    db = SessionLocal()
    try:
        campaigns = db.query(Campaign).filter(
            Campaign.status == "active"
        ).order_by(Campaign.created_at.desc()).limit(10).all()
        
        if not campaigns:
            await update.message.reply_text(
                "📋 No active campaigns found.\n\n"
                "Check back soon or use voice commands to search!"
            )
            return
        
        message = "📋 <b>Active Campaigns</b>\n\n"
        
        for idx, campaign in enumerate(campaigns, 1):
            raised = campaign.raised_amount_usd or 0
            goal = campaign.goal_amount_usd or 1
            progress = (raised / goal * 100)
            location = campaign.location_region or campaign.location_country or 'N/A'
            
            # Progress bar
            bar_filled = int(progress / 10)
            bar = "█" * bar_filled + "░" * (10 - bar_filled)
            
            message += (
                f"<b>{idx}. {campaign.title}</b>\n"
                f"   {bar} {progress:.1f}%\n"
                f"   💰 ${raised:,.0f} / ${goal:,.0f}\n"
                f"   📍 {location}\n"
                f"   /campaign_{campaign.id}\n\n"
            )
        
        message += "💬 Use voice or text to donate!"
        
        await update.message.reply_text(message, parse_mode="HTML")
        
    finally:
        db.close()

# ============================================================================
# LAB 6: Unified Voice Command Router
# ============================================================================
# All voice intents now route through Lab 6 command router
# Old handle_voice_intent function removed - single source of truth


async def donations_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /donations command - View user's donation history"""
    user = update.effective_user
    telegram_user_id = str(user.id)
    
    from database.db import SessionLocal
    from database.models import Donor, Donation
    
    db = SessionLocal()
    try:
        # Find donor by telegram_user_id
        donor = db.query(Donor).filter(
            Donor.telegram_user_id == telegram_user_id
        ).first()
        
        if not donor:
            await update.message.reply_text(
                "💰 You haven't made any donations yet.\n\n"
                "Use /campaigns to see active campaigns!"
            )
            return
        
        # Get donations
        donations = db.query(Donation).filter(
            Donation.donor_id == donor.id
        ).order_by(Donation.created_at.desc()).limit(10).all()
        
        if not donations:
            await update.message.reply_text(
                "💰 You haven't made any donations yet.\n\n"
                "Use /campaigns to see active campaigns!"
            )
            return
        
        total_donated = sum(d.amount for d in donations)
        
        message = f"💰 <b>Your Donation History</b>\n\n"
        message += f"Total Donated: ${total_donated:,.2f}\n"
        message += f"Donations: {len(donations)}\n\n"
        
        for idx, donation in enumerate(donations[:5], 1):
            status_emoji = {
                "pending": "⏳",
                "completed": "✅",
                "failed": "❌",
                "refunded": "↩️"
            }.get(donation.status, "❓")
            
            message += (
                f"{idx}. {status_emoji} ${donation.amount:.2f} {donation.currency}\n"
                f"   Campaign: {donation.campaign.title if donation.campaign else 'N/A'}\n"
                f"   Date: {donation.created_at.strftime('%Y-%m-%d')}\n"
                f"   Status: {donation.status.title()}\n\n"
            )
        
        if len(donations) > 5:
            message += f"... and {len(donations) - 5} more\n\n"
        
        message += "🙏 Thank you for your support!"
        
        await update.message.reply_text(message, parse_mode="HTML")
        
    finally:
        db.close()


async def my_campaigns_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /my_campaigns command - View user's created campaigns"""
    user = update.effective_user
    telegram_user_id = str(user.id)
    
    from database.db import SessionLocal
    from database.models import User, Campaign
    
    db = SessionLocal()
    try:
        # Find user
        db_user = db.query(User).filter(
            User.telegram_user_id == telegram_user_id
        ).first()
        
        if not db_user:
            await update.message.reply_text(
                "⚠️ Please register first: /start"
            )
            return
        
        # Check if user is campaign creator
        if db_user.role not in ["CAMPAIGN_CREATOR", "SYSTEM_ADMIN"]:
            await update.message.reply_text(
                "⚠️ This command is for Campaign Creators only.\n\n"
                "To create campaigns, register as a Campaign Creator: /register"
            )
            return
        
        # Get campaigns
        campaigns = db.query(Campaign).filter(
            Campaign.ngo_id == db_user.ngo_id
        ).order_by(Campaign.created_at.desc()).all()
        
        if not campaigns:
            await update.message.reply_text(
                "📋 You haven't created any campaigns yet.\n\n"
                "Use voice commands to create your first campaign!"
            )
            return
        
        message = f"📋 <b>Your Campaigns</b>\n\n"
        
        for idx, campaign in enumerate(campaigns[:10], 1):
            raised = campaign.raised_amount_usd or 0
            goal = campaign.goal_amount_usd or 1
            progress = (raised / goal * 100)
            status = "🟢 Active" if campaign.status == "active" else "🔴 Inactive"
            
            # Count donors for this campaign
            from database.models import Donation
            donor_count = db.query(Donation.donor_id).filter(
                Donation.campaign_id == campaign.id,
                Donation.status == "completed"
            ).distinct().count()
            
            message += (
                f"<b>{idx}. {campaign.title}</b>\n"
                f"   Status: {status}\n"
                f"   Goal: ${goal:,.0f}\n"
                f"   Raised: ${raised:,.0f} ({progress:.1f}%)\n"
                f"   Donors: {donor_count}\n\n"
            )
        
        if len(campaigns) > 10:
            message += f"... and {len(campaigns) - 10} more\n"
        
        await update.message.reply_text(message, parse_mode="HTML")
        
    finally:
        db.close()


async def handle_voice_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle voice messages - Main voice processing"""
    user = update.effective_user
    telegram_user_id = str(user.id)
    
    # Check registration
    if not is_user_registered(telegram_user_id):
        await update.message.reply_text(
            "Please register first by sending /start"
        )
        return
    
    language = get_user_language(telegram_user_id)
    
    logger.info(f"Processing voice message from {user.first_name} ({telegram_user_id})")
    
    # Send "processing" message
    if language == "am":
        processing_text = "🎤 የድምፅ መልእክትዎን እየሰራሁ ነው... ትንሽ ይጠብቁ።"
    else:
        processing_text = "🎤 Processing your voice message... Please wait."
    
    processing_msg = await update.message.reply_text(processing_text)
    
    try:
        # Download voice message
        voice = update.message.voice
        file = await context.bot.get_file(voice.file_id)
        
        # Download audio file to memory (not disk - worker is in separate container)
        from io import BytesIO
        audio_buffer = BytesIO()
        await file.download_to_memory(audio_buffer)
        audio_data = audio_buffer.getvalue()
        
        logger.info(f"Voice message downloaded: {len(audio_data)} bytes")
        
        # Store audio in Redis temporarily (TTL 5 minutes)
        from voice.session_manager import redis_client
        import base64
        audio_key = f"audio:{telegram_user_id}:{voice.file_unique_id}"
        audio_b64 = base64.b64encode(audio_data).decode()
        redis_client.setex(audio_key, 300, audio_b64)
        logger.info(f"Stored audio in Redis: {audio_key} ({len(audio_b64)} chars, TTL=300s)")
        
        # Verify storage immediately
        verify_data = redis_client.get(audio_key)
        if not verify_data:
            raise Exception(f"Failed to store audio in Redis - verification failed for key: {audio_key}")
        logger.info(f"✓ Redis storage verified: {len(verify_data)} chars retrieved")
        
        # Queue voice processing task in Celery
        task = process_voice_message_task.delay(
            audio_key=audio_key,
            user_id=telegram_user_id,
            language=language
        )
        
        logger.info(f"Celery task queued: {task.id}")
        
        # Wait for result (async polling)
        import asyncio
        max_wait = 30  # 30 seconds timeout
        wait_interval = 1  # Check every 1 second
        elapsed = 0
        
        while not task.ready() and elapsed < max_wait:
            await asyncio.sleep(wait_interval)
            elapsed += wait_interval
        
        if not task.ready():
            await processing_msg.delete()
            timeout_msg = "⏱️ Processing is taking longer than expected. We'll notify you when ready."
            if language == "am":
                timeout_msg = "⏱️ ማስኬዱ ከተጠበቀው በላይ ጊዜ እየወሰደ ነው። ዝግጁ ሲሆን እናሳውቅዎታለን።"
            await update.message.reply_text(timeout_msg)
            return
        
        # Get result
        result = task.get()
        
        # Delete processing message
        await processing_msg.delete()
        
        if result["success"]:
            # Get intent and entities from NLU
            intent = result.get("intent")
            entities = result.get("entities", {})
            transcript = result["stages"]["asr"]["transcript"]
            
            # ==================================================================
            # LAB 6: Unified Command Router (All Users)
            # ==================================================================
            # Route ALL users through Lab 6 (registered & guests)
            db = SessionLocal()
            try:
                user = db.query(User).filter(User.telegram_user_id == telegram_user_id).first()
                
                # Use UUID for registered users, telegram_user_id for guests
                user_id = str(user.id) if user else telegram_user_id
                
                # Check if we're waiting for clarification from previous message
                from voice.session_manager import SessionManager, ConversationState
                session = SessionManager.get_session(user_id)
                
                # If waiting for clarification, use pending intent and merge entities
                if session and session.get("state") == ConversationState.WAITING_FOR_CLARIFICATION:
                    pending_data = session.get("data", {})
                    original_intent = pending_data.get("pending_intent")
                    original_entities = pending_data.get("pending_entities", {})
                    missing_entities = pending_data.get("missing_entities", [])
                    
                    logger.info(f"Continuing clarification flow - original intent: {original_intent}, missing: {missing_entities}")
                    
                    # Try to extract the missing entity from current transcript
                    for missing_field in missing_entities:
                        if missing_field == "title":
                            original_entities["title"] = transcript
                        elif missing_field == "goal_amount" or missing_field == "amount":
                            import re
                            numbers = re.findall(r'\d+', transcript)
                            if numbers:
                                original_entities[missing_field] = float(numbers[0])
                        elif missing_field == "category":
                            transcript_lower = transcript.lower()
                            if "water" in transcript_lower:
                                original_entities["category"] = "water"
                            elif "education" in transcript_lower or "school" in transcript_lower:
                                original_entities["category"] = "education"
                            elif "health" in transcript_lower or "medical" in transcript_lower:
                                original_entities["category"] = "health"
                            else:
                                original_entities["category"] = transcript
                    
                    # Use original intent with updated entities
                    intent = original_intent
                    entities = original_entities
                    
                    # Clear session
                    SessionManager.end_session(user_id)
                    logger.info(f"Merged clarification - Intent: {intent}, Entities: {entities}")
                
                # Get conversation context and add transcript
                context = get_context(user_id)
                context["transcript"] = transcript  # Add transcript for handlers to use
                
                # Route command through Lab 6 router
                router_result = await route_command(
                    intent=intent,
                    entities=entities,
                    user_id=user_id,
                    db=db,
                    conversation_context=context
                )
                
                # Update context if search results returned
                if router_result.get("success") and "campaigns" in router_result.get("data", {}):
                    campaign_ids = router_result["data"]["campaigns"]
                    if campaign_ids:
                        store_search_results(user_id, campaign_ids)
                
                # Update current campaign if returned
                if "campaign_id" in router_result.get("data", {}):
                    set_current_campaign(user_id, router_result["data"]["campaign_id"])
                
                # Handle clarification flow - store incomplete intent
                if router_result.get("needs_clarification"):
                    from voice.session_manager import SessionManager
                    SessionManager.start_session(
                        user_id=user_id,
                        state=ConversationState.WAITING_FOR_CLARIFICATION,
                        data={
                            "pending_intent": intent,
                            "pending_entities": entities,
                            "missing_entities": router_result.get("missing_entities", []),
                            "original_transcript": transcript
                        }
                    )
                    logger.info(f"Started clarification flow for {intent}, waiting for: {router_result.get('missing_entities')}")
                
                # Use Lab 6 response
                response = router_result.get("message", "I didn't understand that. Try saying 'help'.")
                    
            finally:
                db.close()
            
            # ==================================================================
            # End Lab 6 Integration
            # ==================================================================
            
            # Add transcript for transparency
            full_response = f"💬 You said: \"{transcript}\"\n\n{response}"
            
            # Send with dual delivery (text + voice)
            await send_voice_reply(
                update=update,
                text=full_response,
                language=language,
                parse_mode="HTML"
            )
            
            logger.info(f"✅ Voice processed: {intent}")
        else:
            error_msg = "Sorry, I couldn't process your voice message. Please try again."
            if language == "am":
                error_msg = "ይቅርታ፣ የድምፅ መልእክትዎን ማስኬድ አልቻልኩም። እባክዎ እንደገና ይሞክሩ።"
            
            await update.message.reply_text(f"❌ {error_msg}\n\nError: {result.get('error')}")
            logger.error(f"Voice processing failed: {result.get('error')}")
            
    except Exception as e:
        await processing_msg.delete()
        await update.message.reply_text(f"❌ Error: {str(e)}")
        logger.error(f"Voice handling error: {str(e)}")


async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle text messages (general conversation).
    Support natural language commands like "start", "register", "I want to register"
    """
    user = update.effective_user
    telegram_user_id = str(user.id)
    text = update.message.text.lower().strip()
    
    # Natural language command detection
    if any(word in text for word in ["start", "begin", "hello", "hi", "hey"]):
        return await start_command(update, context)
    
    if any(word in text for word in ["register", "sign up", "signup", "join", "i want to register"]):
        return await register_command(update, context)
    
    # Check registration
    if not is_user_registered(telegram_user_id):
        await update.message.reply_text(
            "Please register first using /register or just say 'I want to register'"
        )
        return
    
    language = get_user_language(telegram_user_id)
    
    logger.info(f"Text message from {user.first_name}: {text}")
    
    # ====================================================================
    # LAB 8: Multi-turn conversation check
    # ====================================================================
    # Check if user is in active conversation (e.g., donation flow, search)
    from voice.session_manager import SessionManager, is_in_conversation, get_conversation_state, ConversationState
    from voice.workflows.donation_flow import route_donation_message
    from voice.workflows.search_flow import route_search_message
    from voice.conversation.analytics import ConversationAnalytics
    from database.models import User as DBUser
    
    if is_in_conversation(telegram_user_id):
        # Route to appropriate conversation handler
        db = SessionLocal()
        try:
            state = get_conversation_state(telegram_user_id)
            
            if state == ConversationState.DONATING.value:
                result = await route_donation_message(telegram_user_id, update.message.text, db)
                await update.message.reply_text(result["message"])
                return
            
            elif state == ConversationState.SEARCHING_CAMPAIGNS.value:
                result = await route_search_message(telegram_user_id, update.message.text, db)
                await update.message.reply_text(result["message"])
                return
        
        except Exception as e:
            logger.error(f"Conversation routing error: {e}")
            
            # LAB 9 Part 4: Track errors
            try:
                db_user = db.query(DBUser).filter(DBUser.telegram_user_id == telegram_user_id).first()
                session_data = SessionManager.get_session(telegram_user_id)
                session_id = session_data.get("data", {}).get("session_id") if session_data else None
                
                if db_user and session_id:
                    ConversationAnalytics.track_event(
                        db=db,
                        user_id=db_user.id,
                        session_id=session_id,
                        event_type="error_occurred",
                        conversation_state=state,
                        current_step="error",
                        metadata={
                            "error_type": type(e).__name__,
                            "error_message": str(e)
                        }
                    )
            except Exception as track_error:
                logger.error(f"Failed to track error: {track_error}")
            
            # Fall through to normal NLU
        finally:
            db.close()
    # ====================================================================
    # End Lab 8
    # ====================================================================
    
    # Import NLU directly for text
    from voice.nlu.nlu_infer import extract_intent_and_entities
    from voice.nlu.context import ConversationContext
    
    # Get context
    user_context = ConversationContext.get_context(telegram_user_id)
    
    # Extract intent
    nlu_result = extract_intent_and_entities(text, language, user_context)
    
    # Update context
    ConversationContext.update_context(
        telegram_user_id,
        intent=nlu_result["intent"],
        entities=nlu_result["entities"]
    )
    
    # Route through Lab 6 command router (same logic for voice and text)
    intent = nlu_result["intent"]
    entities = nlu_result["entities"]
    
    # Get database session and user
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_user_id == telegram_user_id).first()
        user_id = str(user.id) if user else telegram_user_id
        
        # Get conversation context and add transcript
        from voice.context.conversation_manager import get_context
        context_data = get_context(user_id)
        context_data["transcript"] = text  # Add transcript for handlers to use
        
        # Route through Lab 6
        router_result = await route_command(
            intent=intent,
            entities=entities,
            user_id=user_id,
            db=db,
            conversation_context=context_data
        )
        
        response = router_result.get("message", "I didn't understand that. Try saying 'help'.")
    finally:
        db.close()
    
    # Send with dual delivery (text + voice) - same as voice messages
    await send_voice_reply(
        update=update,
        text=response,
        language=language,
        parse_mode="HTML"
    )


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors"""
    logger.error(f"Update {update} caused error: {context.error}")


async def initialize_bot_for_webhooks():
    """
    Initialize the Telegram bot for webhook mode (production).
    Called by main.py during FastAPI startup.
    """
    if not TELEGRAM_BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN environment variable not set")
    
    webhook_url = os.getenv("TELEGRAM_WEBHOOK_URL", "")
    if not webhook_url:
        raise ValueError("TELEGRAM_WEBHOOK_URL not set for webhook mode")
    
    logger.info("🚀 Initializing Telegram bot for WEBHOOK mode")
    logger.info(f"   Webhook URL: {webhook_url}")
    
    # Pre-load Amharic model if local fallback is enabled
    if os.getenv("USE_LOCAL_AMHARIC_FALLBACK", "true").lower() == "true":
        try:
            from voice.asr.asr_infer import load_amharic_model
            logger.info("Pre-loading Amharic model at startup...")
            load_amharic_model()
            logger.info("✓ Amharic model loaded successfully")
        except Exception as e:
            logger.warning(f"Could not pre-load Amharic model: {e}")
    
    # Create application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Registration conversation handler
    registration_handler = ConversationHandler(
        entry_points=[CommandHandler("register", register_command)],
        states={
            SELECTING_ROLE: [CallbackQueryHandler(handle_role_selection, pattern="^role:")],
            SELECTING_LANGUAGE: [CallbackQueryHandler(handle_language_selection, pattern="^lang:")],
            ENTERING_FULL_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_full_name)],
            ENTERING_ORG_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_org_name)],
            ENTERING_LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_location)],
            ENTERING_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_phone)],
            ENTERING_REASON: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_reason)],
            ENTERING_VERIFICATION_EXP: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_verification_exp)],
            ENTERING_COVERAGE_REGIONS: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_coverage_regions)],
            ENTERING_GPS_PHONE: [CallbackQueryHandler(handle_gps_phone, pattern="^gps:")],
            ENTERING_PIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_pin_entry)],
            CONFIRMING_PIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_pin_confirm)]
        },
        fallbacks=[CommandHandler("cancel", cancel_registration)],
        per_message=False
    )
    
    # Language change conversation handler
    language_change_handler = ConversationHandler(
        entry_points=[CommandHandler("language", language_command)],
        states={
            SELECTING_LANGUAGE: [CallbackQueryHandler(language_selection, pattern="^lang:")]
        },
        fallbacks=[CommandHandler("language", language_command)]
    )
    
    # Add all handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(registration_handler)
    application.add_handler(language_change_handler)
    application.add_handler(CommandHandler("help", help_command))
    
    # Campaign and donation commands
    application.add_handler(CommandHandler("campaigns", campaigns_command))
    application.add_handler(CommandHandler("donations", donations_command))
    application.add_handler(CommandHandler("my_campaigns", my_campaigns_command))
    
    # PIN commands
    application.add_handler(get_set_pin_handler())
    application.add_handler(get_change_pin_handler())
    
    # Phone verification
    application.add_handler(CommandHandler("verify_phone", verify_phone_command))
    application.add_handler(CommandHandler("unverify_phone", unverify_phone_command))
    application.add_handler(MessageHandler(filters.CONTACT, handle_contact_share))
    
    # Admin commands
    application.add_handler(CommandHandler("admin_requests", admin_requests_command))
    application.add_handler(CommandHandler("admin_approve", admin_approve_command))
    application.add_handler(CommandHandler("admin_reject", admin_reject_command))
    
    # Field agent commands and handlers
    application.add_handler(CommandHandler("my_verifications", my_verifications_command))
    application.add_handler(CommandHandler("pending_campaigns", pending_campaigns_command))
    application.add_handler(CommandHandler("cancel_verification", cancel_verification_command))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo_message))
    application.add_handler(MessageHandler(filters.LOCATION, handle_location_message))
    
    # Voice and text handlers (must be last - catch-all)
    application.add_handler(MessageHandler(filters.VOICE, handle_voice_message))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
    application.add_error_handler(error_handler)
    
    # Register bot application with webhook handler
    try:
        from voice.telegram.webhook import set_bot_application
        set_bot_application(application)
        logger.info("✅ Bot application registered with webhook handler")
    except ImportError as e:
        logger.error(f"❌ Failed to import webhook handler: {e}")
        raise
    
    # Set webhook with Telegram
    await application.bot.set_webhook(
        url=webhook_url,
        allowed_updates=["message", "callback_query"],
        drop_pending_updates=True
    )
    logger.info(f"✅ Webhook configured: {webhook_url}")
    
    # Initialize the application
    await application.initialize()
    logger.info("✅ Bot initialized and ready for webhooks")
    
    return application


def main():
    """Start the bot"""
    
    if not TELEGRAM_BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN environment variable not set")
    
    # Pre-load Amharic model if local fallback is enabled (Issue #8 fix)
    # This prevents 3-5 minute bot freeze on first Amharic voice message
    if os.getenv("USE_LOCAL_AMHARIC_FALLBACK", "true").lower() == "true":
        try:
            from voice.asr.asr_infer import load_amharic_model
            logger.info("Pre-loading Amharic model at startup...")
            load_amharic_model()
            logger.info("✓ Amharic model loaded successfully")
        except Exception as e:
            logger.warning(f"Could not pre-load Amharic model: {e}")
    
    # Create application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Registration conversation handler (new Phase 4D - TEXT ONLY)
    registration_handler = ConversationHandler(
        entry_points=[CommandHandler("register", register_command)],
        states={
            SELECTING_ROLE: [CallbackQueryHandler(handle_role_selection, pattern="^role:")],
            SELECTING_LANGUAGE: [CallbackQueryHandler(handle_language_selection, pattern="^lang:")],
            ENTERING_FULL_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_full_name)],
            ENTERING_ORG_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_org_name)],
            ENTERING_LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_location)],
            ENTERING_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_phone)],
            ENTERING_REASON: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_reason)],
            ENTERING_VERIFICATION_EXP: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_verification_exp)],
            ENTERING_COVERAGE_REGIONS: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_coverage_regions)],
            ENTERING_GPS_PHONE: [CallbackQueryHandler(handle_gps_phone, pattern="^gps:")],
            ENTERING_PIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_pin_entry)],
            CONFIRMING_PIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_pin_confirm)]
        },
        fallbacks=[CommandHandler("cancel", cancel_registration)],
        per_message=False
    )
    
    # Language change conversation handler (updated for inline buttons)
    language_change_handler = ConversationHandler(
        entry_points=[CommandHandler("language", language_command)],
        states={
            SELECTING_LANGUAGE: [CallbackQueryHandler(language_selection, pattern="^lang:")]
        },
        fallbacks=[CommandHandler("language", language_command)]
    )
    
    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(registration_handler)
    application.add_handler(language_change_handler)
    application.add_handler(CommandHandler("help", help_command))
    
    # Campaign and donation commands
    application.add_handler(CommandHandler("campaigns", campaigns_command))
    application.add_handler(CommandHandler("donations", donations_command))
    application.add_handler(CommandHandler("my_campaigns", my_campaigns_command))
    
    # PIN commands
    application.add_handler(get_set_pin_handler())
    application.add_handler(get_change_pin_handler())
    
    # Phone verification
    application.add_handler(CommandHandler("verify_phone", verify_phone_command))
    application.add_handler(CommandHandler("unverify_phone", unverify_phone_command))
    application.add_handler(MessageHandler(filters.CONTACT, handle_contact_share))
    
    # Admin commands
    application.add_handler(CommandHandler("admin_requests", admin_requests_command))
    application.add_handler(CommandHandler("admin_approve", admin_approve_command))
    application.add_handler(CommandHandler("admin_reject", admin_reject_command))
    
    # Voice and text handlers
    application.add_handler(MessageHandler(filters.VOICE, handle_voice_message))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
    application.add_error_handler(error_handler)
    
    # Check environment for webhook vs polling mode
    app_env = os.getenv("APP_ENV", "development")
    webhook_url = os.getenv("TELEGRAM_WEBHOOK_URL", "")
    
    if app_env == "production" and webhook_url:
        # Production: Use webhooks (Railway/production environment)
        logger.info("🚀 Bot configured for WEBHOOK mode (production)")
        logger.info(f"   Webhook URL: {webhook_url}")
        logger.info("   Waiting for webhook requests from Telegram...")
        
        # Register bot application with webhook handler
        try:
            from voice.telegram.webhook import set_bot_application
            set_bot_application(application)
            logger.info("✅ Bot application registered with webhook handler")
        except ImportError:
            logger.error("❌ Failed to import webhook handler")
        
        # Initialize webhook (this will be set by Railway)
        import asyncio
        asyncio.get_event_loop().run_until_complete(
            application.bot.set_webhook(
                url=webhook_url,
                allowed_updates=["message", "callback_query"],
                drop_pending_updates=True
            )
        )
        logger.info(f"✅ Webhook configured: {webhook_url}")
        
        # Initialize the application but don't run polling
        asyncio.get_event_loop().run_until_complete(application.initialize())
        logger.info("✅ Bot initialized and ready for webhooks")
        
    else:
        # Development: Use polling
        logger.info("🤖 Bot starting in POLLING mode (development)")
        logger.info("   Press Ctrl+C to stop")
        application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
