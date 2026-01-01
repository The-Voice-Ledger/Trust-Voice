#!/bin/bash
# Railway Environment Variables Setup Script
# This script helps you set all environment variables in Railway programmatically

set -e

echo "🚀 TrustVoice - Railway Environment Setup"
echo "========================================="
echo ""

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found!"
    echo "Install it with: npm i -g @railway/cli"
    echo "Or: brew install railway"
    exit 1
fi

echo "✅ Railway CLI found"
echo ""

# Check if logged in
if ! railway whoami &> /dev/null; then
    echo "❌ Not logged in to Railway"
    echo "Run: railway login"
    exit 1
fi

echo "✅ Logged in to Railway"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    echo "Create .env from .env.example first"
    exit 1
fi

echo "✅ Found .env file"
echo ""

# Prompt for confirmation
echo "⚠️  WARNING: This will set environment variables in Railway"
echo "   Make sure you're linked to the correct project!"
echo ""
railway status
echo ""
read -p "Continue? (y/N) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi

echo ""
echo "📤 Uploading environment variables to Railway..."
echo ""

# Option 1: Bulk upload from .env file
railway variables --set-from-file .env

echo ""
echo "✅ Environment variables uploaded!"
echo ""
echo "🔧 Now you need to set Railway-specific variables:"
echo ""
echo "1. Get your Railway domain:"
echo "   railway domain"
echo ""
echo "2. Manually set these using your Railway URL:"
echo "   railway variables set APP_ENV=production"
echo "   railway variables set ALLOWED_ORIGINS=https://your-app.railway.app"
echo "   railway variables set TELEGRAM_WEBHOOK_URL=https://your-app.railway.app/webhooks/telegram"
echo "   railway variables set MPESA_CALLBACK_URL=https://your-app.railway.app/webhooks/mpesa"
echo "   railway variables set MPESA_B2C_RESULT_URL=https://your-app.railway.app/webhooks/mpesa/b2c/result"
echo "   railway variables set MPESA_B2C_QUEUE_TIMEOUT_URL=https://your-app.railway.app/webhooks/mpesa/b2c/timeout"
echo ""
echo "3. Generate a strong SECRET_KEY:"
echo "   railway variables set SECRET_KEY=\$(openssl rand -hex 32)"
echo ""
echo "✨ Done! Your variables are set in Railway."
