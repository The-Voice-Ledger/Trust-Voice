"""
TrustVoice FastAPI Application

Entry point for the voice-first donation platform.
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

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
