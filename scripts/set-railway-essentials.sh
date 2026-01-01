#!/bin/bash
# Set essential Railway environment variables
# Run from your local machine after railway login and railway link

set -e

echo "🚀 Setting essential Railway environment variables..."
echo ""

# Read from .env file
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    exit 1
fi

# Load .env
export $(cat .env | grep -v '^#' | xargs)

# Get Railway domain
RAILWAY_DOMAIN=$(railway variables --kv | grep RAILWAY_PUBLIC_DOMAIN | cut -d'=' -f2)
echo "🌐 Railway Domain: $RAILWAY_DOMAIN"
echo ""

# Generate SECRET_KEY if not in .env
if [ -z "$SECRET_KEY" ] || [ "$SECRET_KEY" = "change-this-in-production" ]; then
    SECRET_KEY=$(openssl rand -hex 32)
    echo "🔐 Generated new SECRET_KEY"
fi

echo "📤 Setting variables in Railway..."
echo ""

# Set essential variables
railway variables \
  --set "DATABASE_URL=$DATABASE_URL" \
  --set "OPENAI_API_KEY=$OPENAI_API_KEY" \
  --set "ADDIS_AI_API_KEY=$ADDIS_AI_API_KEY" \
  --set "ADDIS_AI_URL=$ADDIS_AI_URL" \
  --set "TELEGRAM_BOT_TOKEN=$TELEGRAM_BOT_TOKEN" \
  --set "APP_ENV=production" \
  --set "SECRET_KEY=$SECRET_KEY" \
  --set "ALLOWED_ORIGINS=https://$RAILWAY_DOMAIN" \
  --set "TELEGRAM_WEBHOOK_URL=https://$RAILWAY_DOMAIN/webhooks/telegram"

echo ""
echo "✅ Essential variables set!"
echo ""
echo "🎉 Railway will now redeploy automatically"
echo "📍 Your app: https://$RAILWAY_DOMAIN"
echo ""
echo "Next: Set optional variables if needed (Stripe, M-Pesa, Twilio)"
