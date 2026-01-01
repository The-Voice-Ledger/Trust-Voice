"""
TrustVoice FastAPI Application

Entry point for the voice-first donation platform.
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import logging

# Load environment variables FIRST (before any imports that need them)
load_dotenv()

# Import routers
from voice.routers import campaigns, donors, ngos, donations, webhooks, payouts, admin, auth, registrations, ngo_registrations, miniapp_voice, analytics

# Import Telegram webhook router for production deployment
try:
    from voice.telegram.webhook import router as telegram_webhook_router
    TELEGRAM_WEBHOOK_AVAILABLE = True
except ImportError:
    TELEGRAM_WEBHOOK_AVAILABLE = False
    logger.warning("Telegram webhook router not available")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="TrustVoice API",
    description="Voice-first donation platform with blockchain receipts",
    version="1.0.0"
)

# CORS configuration (allow web dashboard to call API)
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# Register Routers
# ============================================

app.include_router(campaigns.router, prefix="/api")
app.include_router(donors.router, prefix="/api")
app.include_router(ngos.router, prefix="/api")
app.include_router(ngo_registrations.router, prefix="/api")
app.include_router(donations.router, prefix="/api")
app.include_router(payouts.router, prefix="/api")
app.include_router(webhooks.router)  # Keep webhooks at root (external callbacks)
app.include_router(admin.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(registrations.router, prefix="/api")
app.include_router(miniapp_voice.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")

# Register Telegram webhook router if available (for production deployment)
if TELEGRAM_WEBHOOK_AVAILABLE:
    app.include_router(telegram_webhook_router)
    logger.info("✅ Telegram webhook router registered")

# ============================================
# Mount Frontend Static Files
# ============================================

# Serve frontend mini apps at root path
app.mount("/", StaticFiles(directory="frontend-miniapps", html=True), name="frontend-miniapps")


# ============================================
# Health Check Endpoint
# ============================================

@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring.
    
    Returns server status and basic info.
    Used by:
    - Monitoring services (UptimeRobot, Pingdom)
    - Load balancers
    - Deployment systems (Railway, Render)
    """
    return {
        "status": "healthy",
        "service": "TrustVoice API",
        "version": "1.0.0",
        "environment": os.getenv("APP_ENV", "development")
    }


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Welcome to TrustVoice API",
        "documentation": "/docs",
        "health": "/health"
    }


# ============================================
# TODO: Include routers (Lab 2+)
# ============================================
# from voice.routers import ivr, telegram, whatsapp
# from payments.routers import stripe_router, paypal_router
#
# app.include_router(ivr.router, prefix="/voice/ivr", tags=["IVR"])
# app.include_router(telegram.router, prefix="/voice/telegram", tags=["Telegram"])
# app.include_router(whatsapp.router, prefix="/voice/whatsapp", tags=["WhatsApp"])
# app.include_router(stripe_router, prefix="/payments/stripe", tags=["Stripe"])


# ============================================
# Startup/Shutdown Events
# ============================================

@app.on_event("startup")
async def startup_event():
    """Run on application startup."""
    logger.info("TrustVoice API starting up...")
    logger.info(f"Environment: {os.getenv('APP_ENV')}")
    logger.info(f"Database: {os.getenv('DATABASE_URL', 'Not configured')[:50]}...")
    
    # TODO: Initialize database connection pool
    # TODO: Connect to Redis
    # TODO: Warm up AI models


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown."""
    logger.info("TrustVoice API shutting down...")
    # TODO: Close database connections
    # TODO: Close Redis connection
    # TODO: Cleanup resources


# ============================================
# Run Server (Development Only)
# ============================================

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("APP_PORT", 8000))
    host = os.getenv("APP_HOST", "0.0.0.0")
    
    logger.info(f"Starting server on {host}:{port}")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,  # Auto-reload on code changes (dev only!)
        log_level="info"
    )
