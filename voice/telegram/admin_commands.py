"""
Admin Commands
Handles admin-only operations for user approval, management, etc.
"""

import logging
from datetime import datetime
from typing import Optional

from telegram import Update
from telegram.ext import ContextTypes

from database.db import SessionLocal
from database.models import User, PendingRegistration, UserRole

logger = logging.getLogger(__name__)


def require_admin(func):
    """Decorator to enforce admin-only access"""
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        telegram_user_id = str(user.id)
        
        db = SessionLocal()
        try:
            admin = db.query(User).filter(
                User.telegram_user_id == telegram_user_id
            ).first()
            
            if not admin or admin.role != "SYSTEM_ADMIN":
                await update.message.reply_text(
                    "❌ Access Denied\n\n"
                    "This command is restricted to system administrators.\n"
                    "Contact support if you believe this is an error."
                )
                logger.warning(f"Unauthorized admin access attempt: {user.username} ({telegram_user_id})")
                return
            
            return await func(update, context)
        finally:
            db.close()
    
    return wrapper


@require_admin
async def admin_requests_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /admin-requests - View all pending registrations
    
    Shows list of users awaiting approval with key details.
    """
    db = SessionLocal()
    try:
        pending_list = db.query(PendingRegistration).filter(
            PendingRegistration.status == "PENDING"
        ).order_by(PendingRegistration.created_at.desc()).all()
        
        if not pending_list:
            await update.message.reply_text(
                "✅ No pending registrations!\n\n"
                "All caught up. 🎉"
            )
            return
        
        # Format message
        message = f"📋 *Pending Registrations* ({len(pending_list)})\n\n"
        
        for idx, pending in enumerate(pending_list, 1):
            hours_ago = int((datetime.utcnow() - pending.created_at).total_seconds() / 3600)
            
            message += f"*{idx}. {pending.requested_role.replace('_', ' ').title()}*\n"
            message += f"   ID: `{pending.id}`\n"
            message += f"   Name: {pending.full_name}\n"
            
            if pending.organization_name:
                message += f"   Org: {pending.organization_name}\n"
            
            message += f"   Location: {pending.location}\n"
            
            if pending.phone_number:
                message += f"   Phone: {pending.phone_number}\n"
            
            # Role-specific details
            if pending.requested_role == "CAMPAIGN_CREATOR" and pending.reason:
                reason_preview = pending.reason[:80] + "..." if len(pending.reason) > 80 else pending.reason
                message += f"   Reason: {reason_preview}\n"
            
            if pending.requested_role == "FIELD_AGENT":
                if pending.verification_experience:
                    exp_preview = pending.verification_experience[:80] + "..." if len(pending.verification_experience) > 80 else pending.verification_experience
                    message += f"   Experience: {exp_preview}\n"
                if pending.coverage_regions:
                    message += f"   Coverage: {pending.coverage_regions}\n"
                if pending.has_gps_phone is not None:
                    gps_status = "✅ Yes" if pending.has_gps_phone else "❌ No"
                    message += f"   GPS Phone: {gps_status}\n"
            
            message += f"   Submitted: {hours_ago}h ago\n"
            message += f"\n"
            message += f"   `/admin_approve {pending.id}`\n"
            message += f"   `/admin_reject {pending.id} <reason>`\n\n"
        
        message += "━━━━━━━━━━━━━━━━━━━━\n"
        message += "💡 Tap a command to approve/reject"
        
        # Split if too long (Telegram 4096 char limit)
        if len(message) > 4000:
            chunks = [message[i:i+4000] for i in range(0, len(message), 4000)]
            for chunk in chunks:
                await update.message.reply_text(chunk, parse_mode="Markdown")
        else:
            await update.message.reply_text(message, parse_mode="Markdown")
        
        logger.info(f"Admin {update.effective_user.username} viewed {len(pending_list)} pending registrations")
        
    except Exception as e:
        logger.error(f"Error listing pending registrations: {e}")
        await update.message.reply_text(
            f"❌ Error retrieving pending registrations.\n\n"
            f"Error: {str(e)}"
        )
    finally:
        db.close()


@require_admin
async def admin_approve_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /admin-approve <id> - Approve pending registration
    
    Moves user from pending_registrations to users table.
    Sends notification to user via Telegram.
    """
    admin = update.effective_user
    admin_telegram_id = str(admin.id)
    
    # Parse arguments
    if not context.args or len(context.args) < 1:
        await update.message.reply_text(
            "❌ Usage: `/admin_approve <id>`\n\n"
            "Example: `/admin_approve 42`\n\n"
            "Use `/admin_requests` to see pending IDs.",
            parse_mode="Markdown"
        )
        return
    
    try:
        pending_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ Invalid ID. Must be a number.")
        return
    
    db = SessionLocal()
    try:
        # Get admin user
        admin_user = db.query(User).filter(
            User.telegram_user_id == admin_telegram_id
        ).first()
        
        if not admin_user:
            await update.message.reply_text("❌ Admin user not found in database.")
            return
        
        # Get pending registration
        pending = db.query(PendingRegistration).filter(
            PendingRegistration.id == pending_id,
            PendingRegistration.status == "PENDING"
        ).first()
        
        if not pending:
            await update.message.reply_text(
                f"❌ Pending registration #{pending_id} not found.\n\n"
                "It may have already been processed.\n"
                "Use `/admin_requests` to see current pending list.",
                parse_mode="Markdown"
            )
            return
        
        # Check if user already exists (edge case: admin testing their own registration)
        existing_user = db.query(User).filter(
            User.telegram_user_id == pending.telegram_user_id
        ).first()
        
        if existing_user:
            # User exists - update their role instead of creating new
            existing_user.role = UserRole[pending.requested_role]
            existing_user.is_approved = True
            existing_user.approved_at = datetime.utcnow()
            existing_user.approved_by_admin_id = admin_user.id
            if pending.phone_number:
                existing_user.phone_number = pending.phone_number
            if pending.pin_hash:
                existing_user.pin_hash = pending.pin_hash
                existing_user.pin_set_at = datetime.utcnow()
            
            logger.info(f"Updated existing user {existing_user.id} role to {pending.requested_role}")
        else:
            # Create new approved user
            new_user = User(
                telegram_user_id=pending.telegram_user_id,
                telegram_username=pending.telegram_username,
                telegram_first_name=pending.telegram_first_name,
                telegram_last_name=pending.telegram_last_name,
                role=UserRole[pending.requested_role],
                is_approved=True,
                approved_at=datetime.utcnow(),
                approved_by_admin_id=admin_user.id,
                phone_number=pending.phone_number,
                pin_hash=pending.pin_hash,
                pin_set_at=datetime.utcnow() if pending.pin_hash else None
            )
            
            db.add(new_user)
            logger.info(f"Created new user for telegram_id {pending.telegram_user_id}")
        
        # Update pending status
        pending.status = "APPROVED"
        pending.reviewed_by_admin_id = admin_user.id
        pending.reviewed_at = datetime.utcnow()
        
        db.commit()
        
        # Send confirmation to admin
        role_name = pending.requested_role.replace("_", " ").title()
        await update.message.reply_text(
            f"✅ *Approved!*\n\n"
            f"User: {pending.full_name}\n"
            f"Role: {role_name}\n"
            f"Org: {pending.organization_name or 'N/A'}\n\n"
            f"User has been notified and can now access the platform.",
            parse_mode="Markdown"
        )
        
        # Send notification to user
        try:
            bot = context.bot
            
            if pending.requested_role == "CAMPAIGN_CREATOR":
                username = pending.telegram_username or "your_username"
                user_message = (
                    "🎉 *Registration Approved!*\n\n"
                    f"Congratulations, {pending.full_name}!\n\n"
                    "Your Campaign Creator account has been approved.\n\n"
                    "*What you can do now:*\n"
                    "📋 Create campaigns for your projects\n"
                    "💰 Receive donations from verified donors\n"
                    "📊 Track donations and impact\n"
                    "🌐 Access web dashboard: https://trustvoice.app\n\n"
                    "*Login Credentials:*\n"
                    f"Username: `{username}`\n"
                    "PIN: Your 4-digit PIN\n\n"
                    "Use /help to see what you can do!"
                )
            elif pending.requested_role == "FIELD_AGENT":
                username = pending.telegram_username or "your_username"
                user_message = (
                    "🎉 *Registration Approved!*\n\n"
                    f"Congratulations, {pending.full_name}!\n\n"
                    "Your Field Agent account has been approved.\n\n"
                    "*What you can do now:*\n"
                    "✅ Verify campaigns on the ground\n"
                    "📸 Submit GPS-tagged photos\n"
                    "📝 Write verification reports\n"
                    "🌐 Access verification tools: https://trustvoice.app\n\n"
                    "*Login Credentials:*\n"
                    f"Username: `{username}`\n"
                    "PIN: Your 4-digit PIN\n\n"
                    "Use /help to see what you can do!"
                )
            else:
                user_message = f"🎉 Your registration has been approved! Use /help to get started."
            
            await bot.send_message(
                chat_id=int(pending.telegram_user_id),
                text=user_message,
                parse_mode="Markdown"
            )
            
            logger.info(f"Admin {admin.username} approved registration #{pending_id} - User {pending.full_name} notified")
            
        except Exception as e:
            logger.error(f"Failed to notify user {pending.telegram_user_id}: {e}")
            await update.message.reply_text(
                f"⚠️ User approved but notification failed.\n"
                f"User ID: {pending.telegram_user_id}\n"
                f"Error: {str(e)}"
            )
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error approving registration #{pending_id}: {e}")
        await update.message.reply_text(
            f"❌ Error approving registration.\n\n"
            f"Error: {str(e)}"
        )
    finally:
        db.close()


@require_admin
async def admin_reject_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /admin-reject <id> <reason> - Reject pending registration
    
    Updates status to REJECTED and notifies user with reason.
    """
    admin = update.effective_user
    admin_telegram_id = str(admin.id)
    
    # Parse arguments
    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "❌ Usage: `/admin_reject <id> <reason>`\n\n"
            "Example: `/admin_reject 42 Insufficient verification details`\n\n"
            "Use `/admin_requests` to see pending IDs.",
            parse_mode="Markdown"
        )
        return
    
    try:
        pending_id = int(context.args[0])
        reason = " ".join(context.args[1:])
    except ValueError:
        await update.message.reply_text("❌ Invalid ID. Must be a number.")
        return
    
    if not reason or len(reason) < 10:
        await update.message.reply_text(
            "❌ Please provide a detailed rejection reason (at least 10 characters).\n\n"
            "This helps users understand what to improve."
        )
        return
    
    db = SessionLocal()
    try:
        # Get admin user
        admin_user = db.query(User).filter(
            User.telegram_user_id == admin_telegram_id
        ).first()
        
        if not admin_user:
            await update.message.reply_text("❌ Admin user not found in database.")
            return
        
        # Get pending registration
        pending = db.query(PendingRegistration).filter(
            PendingRegistration.id == pending_id,
            PendingRegistration.status == "PENDING"
        ).first()
        
        if not pending:
            await update.message.reply_text(
                f"❌ Pending registration #{pending_id} not found.\n\n"
                "It may have already been processed.\n"
                "Use `/admin_requests` to see current pending list.",
                parse_mode="Markdown"
            )
            return
        
        # Update pending status
        pending.status = "REJECTED"
        pending.rejection_reason = reason
        pending.reviewed_by_admin_id = admin_user.id
        pending.reviewed_at = datetime.utcnow()
        
        db.commit()
        
        # Send confirmation to admin
        role_name = pending.requested_role.replace("_", " ").title()
        await update.message.reply_text(
            f"✅ *Rejected*\n\n"
            f"User: {pending.full_name}\n"
            f"Role: {role_name}\n"
            f"Reason: {reason}\n\n"
            f"User has been notified.",
            parse_mode="Markdown"
        )
        
        # Send notification to user
        try:
            bot = context.bot
            
            user_message = (
                f"❌ *Registration Not Approved*\n\n"
                f"Hi {pending.full_name},\n\n"
                f"Unfortunately, we cannot approve your {role_name} registration at this time.\n\n"
                f"*Reason:*\n{reason}\n\n"
                f"*What you can do:*\n"
                f"• Review the feedback above\n"
                f"• Improve your application details\n"
                f"• Register again: /register\n\n"
                f"If you have questions, please reply to this message."
            )
            
            await bot.send_message(
                chat_id=int(pending.telegram_user_id),
                text=user_message,
                parse_mode="Markdown"
            )
            
            logger.info(f"Admin {admin.username} rejected registration #{pending_id} - User {pending.full_name} notified")
            
        except Exception as e:
            logger.error(f"Failed to notify user {pending.telegram_user_id}: {e}")
            await update.message.reply_text(
                f"⚠️ Registration rejected but notification failed.\n"
                f"User ID: {pending.telegram_user_id}\n"
                f"Error: {str(e)}"
            )
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error rejecting registration #{pending_id}: {e}")
        await update.message.reply_text(
            f"❌ Error rejecting registration.\n\n"
            f"Error: {str(e)}"
        )
    finally:
        db.close()
