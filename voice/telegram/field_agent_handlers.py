"""
Field Agent Telegram Bot Handlers

Handles photo and location messages for field verification workflow.
Integrates with field_agent API router for photo storage and verification submission.
"""

import logging
import httpx
from typing import Optional
from telegram import Update
from telegram.ext import ContextTypes

from database.db import SessionLocal
from database.models import User
from voice.routers.field_agent import VerificationSession, PhotoStorage

logger = logging.getLogger(__name__)

# Internal API base URL (for bot to call our own API)
API_BASE_URL = "http://localhost:8000/api/field-agent"


async def handle_photo_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle photo messages from field agents.
    
    Photos are stored with metadata and added to the agent's verification session.
    Agent can send multiple photos before submitting the verification.
    """
    user = update.effective_user
    telegram_user_id = str(user.id)
    
    # Check if user is registered field agent
    db = SessionLocal()
    try:
        db_user = db.query(User).filter(
            User.telegram_user_id == telegram_user_id
        ).first()
        
        if not db_user:
            await update.message.reply_text(
                "❌ Please register first using /start"
            )
            return
        
        if db_user.role != "FIELD_AGENT":
            await update.message.reply_text(
                "❌ Only field agents can submit verification photos.\n"
                f"Your current role: {db_user.role}\n\n"
                "To become a field agent, please contact an administrator."
            )
            return
        
        # Get the largest photo size (best quality)
        photo = update.message.photo[-1]
        file_id = photo.file_id
        file_size = photo.file_size
        
        logger.info(f"Photo received from field agent {telegram_user_id}: {file_id} ({file_size} bytes)")
        
        # Store photo metadata using PhotoStorage
        photo_id = PhotoStorage.save_photo_metadata(
            telegram_user_id=telegram_user_id,
            file_id=file_id,
            file_size=file_size
        )
        
        # Update verification session
        session = VerificationSession(telegram_user_id)
        session_data = session.get() or {}
        photo_ids = session_data.get("photo_ids", [])
        photo_ids.append(photo_id)
        session.update({"photo_ids": photo_ids})
        
        # Send confirmation
        photo_count = len(photo_ids)
        
        message = (
            f"✅ Photo {photo_count} received!\n\n"
            f"📸 Total photos: {photo_count}\n\n"
        )
        
        if photo_count < 3:
            message += "💡 You can send more photos (up to 3 recommended for higher trust score).\n\n"
        
        message += (
            "When you're ready to submit your verification:\n"
            "1. Send your GPS location 📍\n"
            "2. Say or type: 'Submit field report for [campaign name]'\n\n"
            "Or type /cancel_verification to start over."
        )
        
        await update.message.reply_text(message)
        
        logger.info(f"Photo {photo_count} stored for agent {telegram_user_id}")
        
    except Exception as e:
        logger.error(f"Error handling photo: {str(e)}")
        await update.message.reply_text(
            f"❌ Failed to process photo: {str(e)}\n\n"
            "Please try again or contact support."
        )
    finally:
        db.close()


async def handle_location_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle location messages from field agents.
    
    Location is stored in the agent's verification session.
    GPS coordinates are used for trust score calculation.
    """
    user = update.effective_user
    telegram_user_id = str(user.id)
    
    # Check if user is registered field agent
    db = SessionLocal()
    try:
        db_user = db.query(User).filter(
            User.telegram_user_id == telegram_user_id
        ).first()
        
        if not db_user:
            await update.message.reply_text(
                "❌ Please register first using /start"
            )
            return
        
        if db_user.role != "FIELD_AGENT":
            await update.message.reply_text(
                "❌ Only field agents can submit verification locations.\n"
                f"Your current role: {db_user.role}"
            )
            return
        
        # Get GPS coordinates
        location = update.message.location
        gps_latitude = location.latitude
        gps_longitude = location.longitude
        
        logger.info(f"Location received from field agent {telegram_user_id}: ({gps_latitude}, {gps_longitude})")
        
        # Update verification session
        session = VerificationSession(telegram_user_id)
        session.update({
            "gps_latitude": gps_latitude,
            "gps_longitude": gps_longitude
        })
        
        # Get session data to show progress
        session_data = session.get() or {}
        photo_count = len(session_data.get("photo_ids", []))
        
        # Send confirmation with next steps
        message = (
            f"✅ Location received!\n\n"
            f"📍 GPS: {gps_latitude:.6f}, {gps_longitude:.6f}\n"
            f"📸 Photos: {photo_count}\n\n"
        )
        
        if photo_count == 0:
            message += (
                "⚠️ No photos yet. Send photos first for higher trust score.\n\n"
                "Send photos, then say:\n"
                "'Submit field report for [campaign name]'"
            )
        else:
            message += (
                "Ready to submit! Say or type:\n"
                "'Submit field report for [campaign name]'\n\n"
                "Example:\n"
                "'Submit field report for Mwanza Water Project'\n\n"
                "Or type /cancel_verification to start over."
            )
        
        await update.message.reply_text(message)
        
        logger.info(f"Location stored for agent {telegram_user_id}")
        
    except Exception as e:
        logger.error(f"Error handling location: {str(e)}")
        await update.message.reply_text(
            f"❌ Failed to process location: {str(e)}\n\n"
            "Please try again or contact support."
        )
    finally:
        db.close()


async def cancel_verification_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Cancel in-progress verification and clear session.
    """
    user = update.effective_user
    telegram_user_id = str(user.id)
    
    try:
        # Clear verification session
        session = VerificationSession(telegram_user_id)
        session.delete()
        
        await update.message.reply_text(
            "✅ Verification cancelled. Your photos and location have been cleared.\n\n"
            "Start a new verification by sending photos and location."
        )
        
        logger.info(f"Verification cancelled for agent {telegram_user_id}")
        
    except Exception as e:
        logger.error(f"Error cancelling verification: {str(e)}")
        await update.message.reply_text(
            f"❌ Failed to cancel verification: {str(e)}"
        )


async def my_verifications_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Show field agent's verification history and earnings.
    """
    user = update.effective_user
    telegram_user_id = str(user.id)
    
    db = SessionLocal()
    try:
        db_user = db.query(User).filter(
            User.telegram_user_id == telegram_user_id
        ).first()
        
        if not db_user:
            await update.message.reply_text(
                "❌ Please register first using /start"
            )
            return
        
        if db_user.role != "FIELD_AGENT":
            await update.message.reply_text(
                "❌ This command is only for field agents.\n"
                f"Your current role: {db_user.role}"
            )
            return
        
        # Get verification history from API
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{API_BASE_URL}/verifications/history",
                params={"telegram_user_id": telegram_user_id}
            )
            
            if response.status_code != 200:
                await update.message.reply_text(
                    "❌ Failed to retrieve your verification history.\n"
                    "Please try again later."
                )
                return
            
            verifications = response.json()
        
        if not verifications:
            await update.message.reply_text(
                "📋 You haven't submitted any verifications yet.\n\n"
                "To submit a field report:\n"
                "1. Send photos of the campaign site 📸\n"
                "2. Send your GPS location 📍\n"
                "3. Say: 'Submit field report for [campaign name]'"
            )
            return
        
        # Calculate earnings
        total_earnings = sum(
            v.get("agent_payout_amount_usd", 0) or 0
            for v in verifications
            if v.get("agent_payout_status") == "completed"
        )
        
        pending_earnings = sum(
            v.get("agent_payout_amount_usd", 0) or 0
            for v in verifications
            if v.get("agent_payout_status") in ["initiated", None] and v.get("status") == "approved"
        )
        
        # Format message
        message = (
            f"📊 <b>Your Field Agent Dashboard</b>\n\n"
            f"💰 <b>Earnings Summary:</b>\n"
            f"  • Total Earned: ${total_earnings:.2f} USD\n"
            f"  • Pending: ${pending_earnings:.2f} USD\n"
            f"  • Verifications: {len(verifications)}\n\n"
            f"📋 <b>Recent Verifications:</b>\n\n"
        )
        
        # Show last 5 verifications
        for i, v in enumerate(verifications[:5], 1):
            status_emoji = {
                "approved": "✅",
                "pending": "⏳",
                "rejected": "❌"
            }.get(v.get("status"), "❓")
            
            payout_emoji = {
                "completed": "💰",
                "initiated": "⏳",
                "failed": "❌"
            }.get(v.get("agent_payout_status"), "")
            
            message += (
                f"{i}. {status_emoji} <b>{v.get('campaign_title', 'Unknown')}</b>\n"
                f"   Trust Score: {v.get('trust_score', 0)}/100\n"
                f"   Photos: {v.get('photos_count', 0)}\n"
                f"   Status: {v.get('status', 'unknown').title()}\n"
            )
            
            if v.get("agent_payout_amount_usd"):
                message += f"   Payout: ${v['agent_payout_amount_usd']:.2f} {payout_emoji}\n"
            
            message += "\n"
        
        if len(verifications) > 5:
            message += f"<i>... and {len(verifications) - 5} more</i>\n"
        
        await update.message.reply_text(message, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Error showing verifications: {str(e)}")
        await update.message.reply_text(
            f"❌ Failed to retrieve verifications: {str(e)}"
        )
    finally:
        db.close()


async def pending_campaigns_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Show campaigns that need field verification.
    """
    user = update.effective_user
    telegram_user_id = str(user.id)
    
    db = SessionLocal()
    try:
        db_user = db.query(User).filter(
            User.telegram_user_id == telegram_user_id
        ).first()
        
        if not db_user:
            await update.message.reply_text(
                "❌ Please register first using /start"
            )
            return
        
        if db_user.role != "FIELD_AGENT":
            await update.message.reply_text(
                "❌ This command is only for field agents.\n"
                f"Your current role: {db_user.role}"
            )
            return
        
        # Get pending campaigns from API
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{API_BASE_URL}/campaigns/pending",
                params={"telegram_user_id": telegram_user_id}
            )
            
            if response.status_code != 200:
                await update.message.reply_text(
                    "❌ Failed to retrieve pending campaigns.\n"
                    "Please try again later."
                )
                return
            
            campaigns = response.json()
        
        if not campaigns:
            await update.message.reply_text(
                "🎉 No pending campaigns!\n\n"
                "All active campaigns have been verified by you.\n"
                "Check back later for new campaigns."
            )
            return
        
        # Format message
        message = (
            f"📋 <b>Campaigns Needing Verification</b>\n\n"
            f"Found {len(campaigns)} campaign(s) you can verify:\n\n"
        )
        
        # Show first 5 campaigns
        for i, campaign in enumerate(campaigns[:5], 1):
            gps_info = ""
            if campaign.get("gps_latitude") and campaign.get("gps_longitude"):
                gps_info = f"\n   📍 GPS: {campaign['gps_latitude']:.4f}, {campaign['gps_longitude']:.4f}"
            
            message += (
                f"{i}. <b>{campaign['title']}</b>\n"
                f"   by {campaign['ngo_name']}\n"
                f"   Goal: ${campaign['target_amount_usd']:.2f} USD\n"
                f"   Raised: ${campaign['current_amount_usd']:.2f} USD{gps_info}\n\n"
            )
        
        if len(campaigns) > 5:
            message += f"<i>... and {len(campaigns) - 5} more</i>\n\n"
        
        message += (
            "To verify a campaign:\n"
            "1. Visit the campaign site\n"
            "2. Take photos 📸\n"
            "3. Send photos via Telegram\n"
            "4. Share your GPS location 📍\n"
            "5. Say: 'Submit field report for [campaign name]'"
        )
        
        await update.message.reply_text(message, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Error showing pending campaigns: {str(e)}")
        await update.message.reply_text(
            f"❌ Failed to retrieve campaigns: {str(e)}"
        )
    finally:
        db.close()
