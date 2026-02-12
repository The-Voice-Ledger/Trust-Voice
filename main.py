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

# Configure logging (must be before any logger usage)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import routers
from voice.routers import campaigns, donors, ngos, donations, webhooks, payouts, admin, auth, registrations, ngo_registrations, miniapp_voice, analytics, field_agent
from voice.routers.websocket import router as websocket_router

# Import Telegram webhook router for production deployment
try:
    from voice.telegram.webhook import router as telegram_webhook_router
    TELEGRAM_WEBHOOK_AVAILABLE = True
except ImportError:
    TELEGRAM_WEBHOOK_AVAILABLE = False
    logger.warning("Telegram webhook router not available")

# Create FastAPI app
app = FastAPI(
    title="TrustVoice API",
    description="Voice-first donation platform with blockchain receipts",
    version="1.0.0"
)

# CORS configuration (allow web dashboard and SPA frontend to call API)
DEFAULT_ORIGINS = "http://localhost:3000,http://localhost:5173,http://localhost:8000,http://localhost:8001"
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", DEFAULT_ORIGINS).split(",")
ALLOWED_ORIGINS = [o.strip() for o in ALLOWED_ORIGINS if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "X-Requested-With"],
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
app.include_router(field_agent.router, prefix="/api")
app.include_router(miniapp_voice.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
app.include_router(websocket_router)  # WebSocket routes at root (/ws/donations, /ws/campaign/{id})

# Register Telegram webhook router if available (for production deployment)
if TELEGRAM_WEBHOOK_AVAILABLE:
    app.include_router(telegram_webhook_router)
    logger.info("✅ Telegram webhook router registered")

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


@app.get("/health/redis")
async def redis_health_check():
    """
    Redis connection health check.
    
    Tests Redis connectivity and reports:
    - Connection status
    - Redis server info
    - REDIS_URL configuration
    """
    from voice.session_manager import redis_client
    
    try:
        # Test PING
        ping_result = redis_client.ping()
        
        # Get Redis server info
        info = redis_client.info()
        
        return {
            "status": "healthy",
            "redis": {
                "connected": ping_result,
                "redis_url_configured": bool(os.getenv('REDIS_URL')),
                "server_version": info.get('redis_version'),
                "used_memory_human": info.get('used_memory_human'),
                "connected_clients": info.get('connected_clients'),
                "uptime_in_days": info.get('uptime_in_days')
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "redis": {
                "connected": False,
                "error": str(e),
                "redis_url_configured": bool(os.getenv('REDIS_URL'))
            }
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
    
    # Log DB connection (masked)
    db_url = os.getenv('DATABASE_URL', 'Not configured')
    if '@' in db_url:
        # Mask credentials: postgresql://user:pass@host -> postgresql://***@host
        parts = db_url.split('@')
        logger.info(f"Database: ***@{parts[-1][:40]}...")
    else:
        logger.info(f"Database: {db_url[:30]}...")
    
    # Initialize Telegram bot if in production
    app_env = os.getenv("APP_ENV", "development")
    telegram_webhook_url = os.getenv("TELEGRAM_WEBHOOK_URL", "")
    
    if app_env == "production" and telegram_webhook_url:
        logger.info("🤖 Initializing Telegram bot in webhook mode...")
        try:
            from voice.telegram.bot import initialize_bot_for_webhooks
            await initialize_bot_for_webhooks()
            logger.info("✅ Telegram bot initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Telegram bot: {e}")
    
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
# Mount Frontend Static Files (MUST BE LAST)
# ============================================
# Static file mounts act as catch-all routes, so they must come after
# all API endpoints to avoid intercepting API requests

# Serve admin dashboard at /admin (must come before root mount)
app.mount("/admin", StaticFiles(directory="frontend", html=True), name="admin-frontend")

# Serve web frontend SPA at /app (must come before root catch-all)
import pathlib
from fastapi.responses import FileResponse

_web_frontend_dist = pathlib.Path("web-frontend/dist")
if _web_frontend_dist.exists():
    # Mount static assets first (JS, CSS, images)
    app.mount("/app/assets", StaticFiles(directory=str(_web_frontend_dist / "assets")), name="web-assets")

    # SPA catch-all: any /app/* route that isn't a static file serves index.html
    # This allows React Router to handle client-side routing on refresh/direct nav
    @app.get("/app/{full_path:path}")
    async def serve_spa(full_path: str):
        # Check if the requested path is an actual file in dist
        file_path = _web_frontend_dist / full_path
        if file_path.is_file():
            return FileResponse(str(file_path))
        # Otherwise serve index.html for client-side routing
        return FileResponse(str(_web_frontend_dist / "index.html"))

    @app.get("/app")
    async def serve_spa_root():
        return FileResponse(str(_web_frontend_dist / "index.html"))

    logger.info("✅ Web frontend SPA mounted at /app with client-side routing support")
else:
    logger.info("ℹ️  Web frontend not built yet — /app not mounted (run: cd web-frontend && npm run build)")

# Serve public miniapps at root path
app.mount("/", StaticFiles(directory="frontend-miniapps", html=True), name="frontend-miniapps")


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
