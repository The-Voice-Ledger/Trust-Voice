"""
Telegram Webhook Handler for Production Deployment
Replaces polling for Railway/production environments
"""
from fastapi import APIRouter, Request, HTTPException, Response
from telegram import Update
import json
import logging
import os

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks/telegram", tags=["telegram-webhooks"])

# Import bot application (will be initialized when bot.py loads)
application = None

def set_bot_application(app):
    """Set the bot application instance from bot.py"""
    global application
    application = app
    logger.info("Telegram bot application registered with webhook handler")


@router.post("")
async def telegram_webhook(request: Request):
    """
    Handle incoming Telegram webhook updates.
    
    In production (Railway), Telegram sends POST requests here instead of polling.
    This endpoint processes updates asynchronously.
    
    URL: https://your-app.railway.app/webhooks/telegram
    """
    try:
        # Validate webhook secret token (prevents forged updates)
        expected_secret = os.getenv("TELEGRAM_WEBHOOK_SECRET")
        if expected_secret:
            received_secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
            if received_secret != expected_secret:
                logger.warning("Telegram webhook: invalid secret token")
                raise HTTPException(status_code=403, detail="Invalid secret token")
        
        # Get the update data
        data = await request.json()
        update_id = data.get('update_id', 'unknown')
        
        logger.info(f"📨 Received Telegram webhook update: {update_id}")
        
        if application is None:
            logger.error("❌ Bot application not initialized!")
            raise HTTPException(status_code=503, detail="Bot not ready")
        
        # Create Update object from JSON
        update = Update.de_json(data, application.bot)
        
        # Process the update asynchronously
        await application.process_update(update)
        
        logger.info(f"✅ Processed update: {update_id}")
        
        # Telegram expects 200 OK response
        return {"ok": True}
        
    except json.JSONDecodeError as e:
        logger.error(f"❌ Invalid JSON from Telegram: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Telegram webhook error: {e}", exc_info=True)
        # Still return 200 to avoid Telegram retries flooding us
        return {"ok": False, "error": "Internal processing error"}


@router.get("")
async def telegram_webhook_info():
    """
    Get webhook status information.
    Useful for debugging webhook configuration.
    """
    if application is None:
        return {
            "status": "not_initialized",
            "message": "Bot application not ready"
        }
    
    app_env = os.getenv("APP_ENV", "development")
    webhook_url = os.getenv("TELEGRAM_WEBHOOK_URL", "")
    
    return {
        "status": "ready",
        "environment": app_env,
        "mode": "webhook" if app_env == "production" else "polling",
        "webhook_configured": bool(webhook_url)
    }


@router.post("/set")
async def set_webhook(request: Request):
    """
    Manually trigger webhook setup.
    Only works in production environment. Requires admin secret.
    
    Call this after deployment to configure Telegram webhook:
    POST /webhooks/telegram/set
    Header: X-Admin-Secret: <ADMIN_API_SECRET>
    """
    # Require admin secret for webhook management
    admin_secret = os.getenv("ADMIN_API_SECRET")
    if admin_secret:
        provided_secret = request.headers.get("X-Admin-Secret", "")
        if provided_secret != admin_secret:
            raise HTTPException(status_code=403, detail="Unauthorized")
    
    app_env = os.getenv("APP_ENV", "development")
    
    if app_env != "production":
        raise HTTPException(
            status_code=400, 
            detail="Webhook setup only available in production"
        )
    
    webhook_url = os.getenv("TELEGRAM_WEBHOOK_URL")
    if not webhook_url:
        raise HTTPException(
            status_code=400,
            detail="TELEGRAM_WEBHOOK_URL not configured"
        )
    
    if application is None:
        raise HTTPException(status_code=503, detail="Bot not ready")
    
    try:
        # Set the webhook
        await application.bot.set_webhook(
            url=webhook_url,
            allowed_updates=["message", "callback_query"],
            drop_pending_updates=True
        )
        
        logger.info(f"✅ Webhook set to: {webhook_url}")
        
        return {
            "success": True,
            "webhook_url": webhook_url,
            "message": "Webhook configured successfully"
        }
    except Exception as e:
        logger.error(f"❌ Failed to set webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/unset")
async def unset_webhook():
    """
    Remove webhook configuration.
    Useful when switching back to polling mode.
    """
    if application is None:
        raise HTTPException(status_code=503, detail="Bot not ready")
    
    try:
        await application.bot.delete_webhook(drop_pending_updates=True)
        logger.info("✅ Webhook removed")
        
        return {
            "success": True,
            "message": "Webhook removed successfully"
        }
    except Exception as e:
        logger.error(f"❌ Failed to remove webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))
