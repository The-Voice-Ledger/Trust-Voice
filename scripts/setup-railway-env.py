#!/usr/bin/env python3
"""
Railway Environment Variables Setup Script
Programmatically set all environment variables in Railway using CLI
"""

import os
import sys
import subprocess
from pathlib import Path
from dotenv import dotenv_values

def run_command(cmd, capture=True):
    """Run shell command and return output"""
    try:
        if capture:
            result = subprocess.run(
                cmd, shell=True, check=True, 
                capture_output=True, text=True
            )
            return result.stdout.strip()
        else:
            subprocess.run(cmd, shell=True, check=True)
            return None
    except subprocess.CalledProcessError as e:
        return None

def check_railway_cli():
    """Check if Railway CLI is installed"""
    if run_command("railway --version"):
        print("✅ Railway CLI found")
        return True
    print("❌ Railway CLI not found!")
    print("Install: npm i -g @railway/cli")
    return False

def check_railway_login():
    """Check if logged in to Railway"""
    if run_command("railway whoami"):
        print("✅ Logged in to Railway")
        return True
    print("❌ Not logged in to Railway")
    print("Run: railway login")
    return False

def get_railway_domain():
    """Get Railway domain for this project"""
    domain = run_command("railway domain")
    if domain and not domain.startswith("No domain"):
        return domain
    return None

def load_env_file(filepath=".env"):
    """Load environment variables from file"""
    if not Path(filepath).exists():
        print(f"❌ {filepath} not found!")
        return None
    
    print(f"✅ Found {filepath}")
    return dotenv_values(filepath)

def set_railway_variable(key, value):
    """Set a single variable in Railway"""
    # Escape special characters
    escaped_value = value.replace('"', '\\"').replace('$', '\\$')
    cmd = f'railway variables set {key}="{escaped_value}"'
    
    result = run_command(cmd, capture=False)
    if result is not None:
        print(f"  ✓ {key}")
        return True
    else:
        print(f"  ✗ {key} (failed)")
        return False

def main():
    print("🚀 TrustVoice - Railway Environment Setup")
    print("=" * 50)
    print()
    
    # Check prerequisites
    if not check_railway_cli():
        sys.exit(1)
    
    if not check_railway_login():
        sys.exit(1)
    
    print()
    
    # Show current project
    print("📋 Current Railway Project:")
    run_command("railway status", capture=False)
    print()
    
    # Confirm
    response = input("⚠️  Set environment variables in this project? (y/N): ")
    if response.lower() != 'y':
        print("Cancelled.")
        sys.exit(0)
    
    print()
    
    # Load .env
    env_vars = load_env_file(".env")
    if not env_vars:
        sys.exit(1)
    
    print()
    print(f"📤 Uploading {len(env_vars)} environment variables...")
    print()
    
    # Get Railway domain
    domain = get_railway_domain()
    if domain:
        print(f"🌐 Railway Domain: {domain}")
        print()
    
    # Set each variable
    success_count = 0
    failed_count = 0
    
    # First pass: Set all existing variables
    for key, value in env_vars.items():
        # Skip empty values
        if not value or value == "":
            continue
        
        # Skip Railway-specific URLs (will set separately)
        if key in ["TELEGRAM_WEBHOOK_URL", "MPESA_CALLBACK_URL", 
                   "MPESA_B2C_RESULT_URL", "MPESA_B2C_QUEUE_TIMEOUT_URL"]:
            continue
        
        if set_railway_variable(key, value):
            success_count += 1
        else:
            failed_count += 1
    
    print()
    print(f"✅ Set {success_count} variables")
    if failed_count > 0:
        print(f"❌ Failed to set {failed_count} variables")
    print()
    
    # Set production-specific variables
    print("🔧 Setting production-specific variables...")
    print()
    
    # Set APP_ENV to production
    if set_railway_variable("APP_ENV", "production"):
        success_count += 1
    
    # If we have a domain, set URL-based variables
    if domain:
        railway_url = f"https://{domain}"
        
        url_vars = {
            "ALLOWED_ORIGINS": railway_url,
            "TELEGRAM_WEBHOOK_URL": f"{railway_url}/webhooks/telegram",
            "MPESA_CALLBACK_URL": f"{railway_url}/webhooks/mpesa",
            "MPESA_B2C_RESULT_URL": f"{railway_url}/webhooks/mpesa/b2c/result",
            "MPESA_B2C_QUEUE_TIMEOUT_URL": f"{railway_url}/webhooks/mpesa/b2c/timeout",
        }
        
        for key, value in url_vars.items():
            if set_railway_variable(key, value):
                success_count += 1
            else:
                failed_count += 1
    else:
        print("⚠️  No Railway domain yet. Set these manually after domain is generated:")
        print("   - ALLOWED_ORIGINS")
        print("   - TELEGRAM_WEBHOOK_URL")
        print("   - MPESA_CALLBACK_URL")
        print("   - MPESA_B2C_RESULT_URL")
        print("   - MPESA_B2C_QUEUE_TIMEOUT_URL")
    
    # Generate strong SECRET_KEY
    print()
    print("🔐 Generating production SECRET_KEY...")
    secret_key = run_command("openssl rand -hex 32")
    if secret_key and set_railway_variable("SECRET_KEY", secret_key):
        success_count += 1
        print("  ✓ Generated and set SECRET_KEY")
    
    print()
    print("=" * 50)
    print(f"✨ Done! Set {success_count} variables in Railway")
    
    if domain:
        print()
        print("🎉 Next Steps:")
        print("1. Deploy your app: railway up")
        print(f"2. Visit: {railway_url}/health")
        print("3. Configure Telegram webhook (automatic)")
        print("4. Update Stripe webhook URL")
        print("5. Update M-Pesa callback URLs")
    else:
        print()
        print("🎉 Next Steps:")
        print("1. Generate domain: railway domain")
        print("2. Run this script again to set URL variables")
        print("3. Deploy: railway up")

if __name__ == "__main__":
    main()
