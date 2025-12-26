#!/usr/bin/env python3
"""
Pre-Demo Verification Script
Quick checks to ensure everything is ready for the demo.

Run: source venv/bin/activate && python tests/pre_demo_check.py
"""

import os
import sys
import subprocess
import redis
from pathlib import Path
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

# Color codes
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
BOLD = '\033[1m'
RESET = '\033[0m'

checks_passed = 0
checks_failed = 0
warnings = []


def check_item(name: str, status: bool, details: str = "", critical: bool = True):
    """Print check result"""
    global checks_passed, checks_failed
    
    if status:
        print(f"{GREEN}✅ {name}{RESET}")
        if details:
            print(f"   {details}")
        checks_passed += 1
    else:
        emoji = "❌" if critical else "⚠️"
        color = RED if critical else YELLOW
        print(f"{color}{emoji} {name}{RESET}")
        if details:
            print(f"   {details}")
        if critical:
            checks_failed += 1
        else:
            warnings.append(name)


def check_env_vars():
    """Check required environment variables"""
    print(f"\n{BOLD}1. Environment Variables{RESET}")
    
    required = {
        "DATABASE_URL": True,
        "REDIS_URL": True,
        "TELEGRAM_BOT_TOKEN": True,
        "OPENAI_API_KEY": False,
        "ADDISAI_STT_URL": False,
        "ADDISAI_TTS_URL": False,
    }
    
    for var, critical in required.items():
        value = os.getenv(var)
        check_item(
            f"{var}",
            bool(value),
            f"Value: {value[:30]}..." if value else "Not set",
            critical
        )


def check_redis():
    """Check Redis connection"""
    print(f"\n{BOLD}2. Redis Connection{RESET}")
    
    try:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        r = redis.from_url(redis_url)
        r.ping()
        
        # Test read/write
        r.set("demo_check", "ok", ex=5)
        value = r.get("demo_check")
        
        check_item(
            "Redis operational",
            value == b"ok",
            f"Connected to {redis_url}"
        )
    except Exception as e:
        check_item("Redis operational", False, str(e))


def check_celery():
    """Check Celery workers"""
    print(f"\n{BOLD}3. Celery Workers{RESET}")
    
    try:
        # Add current directory to Python path
        import sys
        if str(Path.cwd()) not in sys.path:
            sys.path.insert(0, str(Path.cwd()))
        
        from voice.tasks.celery_app import app
        inspector = app.control.inspect()
        workers = inspector.active()
        
        if workers:
            worker_list = list(workers.keys())
            check_item(
                "Celery workers running",
                True,
                f"Active workers: {', '.join(worker_list)}"
            )
        else:
            check_item(
                "Celery workers running",
                False,
                "No workers found. Start with: cd /Users/manu/Trust-Voice && source venv/bin/activate && celery -A voice.tasks.celery_app worker --loglevel=info"
            )
    except ImportError as e:
        # Try alternative check using ps
        import subprocess
        try:
            result = subprocess.run(
                ['ps', 'aux'],
                capture_output=True,
                text=True
            )
            celery_running = 'celery' in result.stdout and 'voice.tasks.celery_app' in result.stdout
            
            if celery_running:
                check_item(
                    "Celery workers running",
                    True,
                    "Detected via process list (import check failed)"
                )
            else:
                check_item(
                    "Celery workers running",
                    False,
                    f"Import error: {str(e)}"
                )
        except Exception as fallback_e:
            check_item("Celery workers running", False, f"Import error: {str(e)}")
    except Exception as e:
        check_item("Celery workers running", False, str(e))


def check_database():
    """Check database connection and schema"""
    print(f"\n{BOLD}4. Database{RESET}")
    
    try:
        db_url = os.getenv("DATABASE_URL")
        engine = create_engine(db_url)
        
        with engine.connect() as conn:
            # Test connection
            conn.execute(text("SELECT 1"))
            check_item("Database connection", True, "Connected successfully")
            
            # Check tables
            result = conn.execute(text(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
            ))
            tables = [row[0] for row in result.fetchall()]
            
            required_tables = ['users', 'campaigns', 'donations', 'impact_verifications', 'ngo_organizations']
            missing = [t for t in required_tables if t not in tables]
            
            check_item(
                "Required tables exist",
                len(missing) == 0,
                f"Missing: {missing}" if missing else f"Found {len(tables)} tables"
            )
            
            # Check for test data
            result = conn.execute(text("SELECT COUNT(*) FROM campaigns WHERE status='active'"))
            active_campaigns = result.fetchone()[0]
            
            check_item(
                "Test campaigns available",
                active_campaigns > 0,
                f"Found {active_campaigns} active campaigns",
                critical=False
            )
            
    except Exception as e:
        check_item("Database connection", False, str(e))


def check_audio_tools():
    """Check ffmpeg/ffprobe availability"""
    print(f"\n{BOLD}5. Audio Tools{RESET}")
    
    # Check ffmpeg
    try:
        result = subprocess.run(
            ['ffmpeg', '-version'],
            capture_output=True,
            timeout=5,
            stdin=subprocess.DEVNULL
        )
        version = result.stdout.decode().split('\n')[0] if result.returncode == 0 else "Not found"
        check_item("ffmpeg installed", result.returncode == 0, version)
    except Exception as e:
        check_item("ffmpeg installed", False, "Install with: brew install ffmpeg")
    
    # Check ffprobe
    try:
        result = subprocess.run(
            ['ffprobe', '-version'],
            capture_output=True,
            timeout=5,
            stdin=subprocess.DEVNULL
        )
        check_item("ffprobe installed", result.returncode == 0)
    except Exception as e:
        check_item("ffprobe installed", False, "Comes with ffmpeg")


def check_directories():
    """Check required directories exist"""
    print(f"\n{BOLD}6. Directory Structure{RESET}")
    
    dirs = [
        "voice/downloads",
        "voice/tts_cache",
        "logs",
        "documentation/testing/test_voice_messages"
    ]
    
    for dir_path in dirs:
        path = Path(dir_path)
        exists = path.exists()
        check_item(
            f"Directory: {dir_path}",
            exists,
            f"Created" if exists else "Will be created automatically",
            critical=False
        )
        
        if not exists and dir_path in ["voice/downloads", "voice/tts_cache"]:
            try:
                path.mkdir(parents=True, exist_ok=True)
                print(f"   {GREEN}Created directory{RESET}")
            except Exception as e:
                print(f"   {YELLOW}Note: {e}{RESET}")


def check_test_files():
    """Check test voice files exist"""
    print(f"\n{BOLD}7. Test Voice Files{RESET}")
    
    test_dir = Path("documentation/testing/test_voice_messages")
    
    if not test_dir.exists():
        check_item("Test voice directory", False, "Directory not found", critical=False)
        return
    
    voice_files = list(test_dir.glob("*.mp3")) + list(test_dir.glob("*.wav"))
    
    check_item(
        "Test voice files",
        len(voice_files) > 0,
        f"Found {len(voice_files)} voice files",
        critical=False
    )


def check_telegram_bot():
    """Check if Telegram bot is running"""
    print(f"\n{BOLD}8. Telegram Bot{RESET}")
    
    # Check if bot process is running
    try:
        result = subprocess.run(
            ['ps', 'aux'],
            capture_output=True,
            text=True
        )
        
        bot_running = 'telegram_bot.py' in result.stdout or 'python voice/telegram/bot.py' in result.stdout
        
        check_item(
            "Telegram bot process",
            bot_running,
            "Bot is running" if bot_running else "Start with: python voice/telegram/bot.py",
            critical=False
        )
    except Exception as e:
        check_item("Telegram bot process", False, str(e), critical=False)


def print_summary():
    """Print summary and recommendations"""
    print(f"\n{BOLD}{'=' * 70}{RESET}")
    print(f"{BOLD}SUMMARY{RESET}")
    print(f"{'=' * 70}")
    
    total = checks_passed + checks_failed
    pass_rate = (checks_passed / total * 100) if total > 0 else 0
    
    print(f"\nPassed: {GREEN}{checks_passed}{RESET}")
    print(f"Failed: {RED}{checks_failed}{RESET}")
    if warnings:
        print(f"Warnings: {YELLOW}{len(warnings)}{RESET}")
    print(f"Pass Rate: {pass_rate:.1f}%")
    
    if checks_failed == 0:
        print(f"\n{GREEN}{BOLD}🎉 ALL CRITICAL CHECKS PASSED!{RESET}")
        print(f"{GREEN}System is ready for the demo.{RESET}")
    else:
        print(f"\n{RED}{BOLD}⚠️  CRITICAL ISSUES FOUND{RESET}")
        print(f"{RED}Please fix the failed checks before the demo.{RESET}")
    
    if warnings:
        print(f"\n{YELLOW}{BOLD}⚠️  Warnings (non-critical):{RESET}")
        for warning in warnings:
            print(f"  • {warning}")
    
    # Quick start commands
    print(f"\n{BOLD}Quick Start Commands:{RESET}")
    print(f"  Start Redis:  {BLUE}brew services start redis{RESET}")
    print(f"  Start Celery: {BLUE}cd /Users/manu/Trust-Voice && source venv/bin/activate && celery -A voice.tasks.celery_app worker --loglevel=info{RESET}")
    print(f"  Start Bot:    {BLUE}cd /Users/manu/Trust-Voice && source venv/bin/activate && python voice/telegram/bot.py{RESET}")
    print(f"  Run Tests:    {BLUE}cd /Users/manu/Trust-Voice && source venv/bin/activate && python tests/test_voice_modules_automated.py{RESET}")
    
    return checks_failed == 0


def main():
    """Run all checks"""
    print(f"\n{BOLD}{BLUE}{'=' * 70}")
    print("  TrustVoice Pre-Demo Verification")
    print(f"{'=' * 70}{RESET}\n")
    
    check_env_vars()
    check_redis()
    check_celery()
    check_database()
    check_audio_tools()
    check_directories()
    check_test_files()
    check_telegram_bot()
    
    success = print_summary()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Check interrupted{RESET}")
        sys.exit(130)
    except Exception as e:
        print(f"\n{RED}Error: {e}{RESET}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
