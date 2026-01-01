#!/bin/bash

# ============================================
# Set All TrustVoice Variables on Railway
# ============================================
# Sets all configured variables from .env
# Skips empty values and placeholder text
# Auto-configures production URLs
# ============================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Setting TrustVoice Environment Variables on Railway${NC}\n"

# Load .env file
if [ ! -f .env ]; then
    echo -e "${RED}❌ Error: .env file not found${NC}"
    echo "Please create .env file with your configuration"
    exit 1
fi

# Load variables from .env
set -a
source .env
set +a

# Get Railway domain
echo -e "${YELLOW}📡 Fetching Railway domain...${NC}"
RAILWAY_DOMAIN=$(railway variables --kv | grep RAILWAY_PUBLIC_DOMAIN | cut -d'=' -f2)
if [ -z "$RAILWAY_DOMAIN" ]; then
    echo -e "${RED}❌ Error: Could not fetch Railway domain${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Railway domain: $RAILWAY_DOMAIN${NC}\n"

# Function to check if variable is set and not a placeholder
is_valid_value() {
    local value="$1"
    if [ -z "$value" ]; then
        return 1
    fi
    # Skip common placeholder patterns
    if [[ "$value" == *"your-"* ]] || [[ "$value" == *"change-this"* ]] || \
       [[ "$value" == *"localhost"* ]] || [[ "$value" == "ACxxxxxxxxx" ]]; then
        return 1
    fi
    return 0
}

# Build Railway command
CMD="railway variables"
COUNT=0

# Core Database & Cache
if is_valid_value "$DATABASE_URL"; then
    CMD="$CMD --set \"DATABASE_URL=$DATABASE_URL\""
    ((COUNT++))
    echo "✓ DATABASE_URL"
fi

if is_valid_value "$REDIS_URL"; then
    CMD="$CMD --set \"REDIS_URL=$REDIS_URL\""
    ((COUNT++))
    echo "✓ REDIS_URL"
fi

# AI/ML APIs
if is_valid_value "$OPENAI_API_KEY"; then
    CMD="$CMD --set \"OPENAI_API_KEY=$OPENAI_API_KEY\""
    ((COUNT++))
    echo "✓ OPENAI_API_KEY"
fi

if is_valid_value "$ADDIS_AI_API_KEY"; then
    CMD="$CMD --set \"ADDIS_AI_API_KEY=$ADDIS_AI_API_KEY\""
    ((COUNT++))
    echo "✓ ADDIS_AI_API_KEY"
fi

if is_valid_value "$ADDIS_AI_URL"; then
    CMD="$CMD --set \"ADDIS_AI_URL=$ADDIS_AI_URL\""
    ((COUNT++))
    echo "✓ ADDIS_AI_URL"
fi

if is_valid_value "$ADDIS_TRANSLATE_URL"; then
    CMD="$CMD --set \"ADDIS_TRANSLATE_URL=$ADDIS_TRANSLATE_URL\""
    ((COUNT++))
    echo "✓ ADDIS_TRANSLATE_URL"
fi

# Payment Processing - Stripe
if is_valid_value "$STRIPE_SECRET_KEY"; then
    CMD="$CMD --set \"STRIPE_SECRET_KEY=$STRIPE_SECRET_KEY\""
    ((COUNT++))
    echo "✓ STRIPE_SECRET_KEY"
fi

if is_valid_value "$STRIPE_PUBLISHABLE_KEY"; then
    CMD="$CMD --set \"STRIPE_PUBLISHABLE_KEY=$STRIPE_PUBLISHABLE_KEY\""
    ((COUNT++))
    echo "✓ STRIPE_PUBLISHABLE_KEY"
fi

if is_valid_value "$STRIPE_WEBHOOK_SECRET"; then
    CMD="$CMD --set \"STRIPE_WEBHOOK_SECRET=$STRIPE_WEBHOOK_SECRET\""
    ((COUNT++))
    echo "✓ STRIPE_WEBHOOK_SECRET"
fi

# Payment Processing - M-Pesa
if is_valid_value "$MPESA_CONSUMER_KEY"; then
    CMD="$CMD --set \"MPESA_CONSUMER_KEY=$MPESA_CONSUMER_KEY\""
    ((COUNT++))
    echo "✓ MPESA_CONSUMER_KEY"
fi

if is_valid_value "$MPESA_CONSUMER_SECRET"; then
    CMD="$CMD --set \"MPESA_CONSUMER_SECRET=$MPESA_CONSUMER_SECRET\""
    ((COUNT++))
    echo "✓ MPESA_CONSUMER_SECRET"
fi

if is_valid_value "$MPESA_BUSINESS_SHORT_CODE"; then
    CMD="$CMD --set \"MPESA_BUSINESS_SHORT_CODE=$MPESA_BUSINESS_SHORT_CODE\""
    ((COUNT++))
    echo "✓ MPESA_BUSINESS_SHORT_CODE"
fi

if is_valid_value "$MPESA_PASSKEY"; then
    CMD="$CMD --set \"MPESA_PASSKEY=$MPESA_PASSKEY\""
    ((COUNT++))
    echo "✓ MPESA_PASSKEY"
fi

if is_valid_value "$MPESA_INITIATOR_NAME"; then
    CMD="$CMD --set \"MPESA_INITIATOR_NAME=$MPESA_INITIATOR_NAME\""
    ((COUNT++))
    echo "✓ MPESA_INITIATOR_NAME"
fi

if is_valid_value "$MPESA_SECURITY_CREDENTIAL"; then
    CMD="$CMD --set \"MPESA_SECURITY_CREDENTIAL=$MPESA_SECURITY_CREDENTIAL\""
    ((COUNT++))
    echo "✓ MPESA_SECURITY_CREDENTIAL"
fi

if is_valid_value "$MPESA_ENVIRONMENT"; then
    CMD="$CMD --set \"MPESA_ENVIRONMENT=$MPESA_ENVIRONMENT\""
    ((COUNT++))
    echo "✓ MPESA_ENVIRONMENT"
fi

# M-Pesa webhook URLs (auto-configure for production)
CMD="$CMD --set \"MPESA_CALLBACK_URL=https://$RAILWAY_DOMAIN/webhooks/mpesa\""
((COUNT++))
echo "✓ MPESA_CALLBACK_URL (auto-configured)"

CMD="$CMD --set \"MPESA_B2C_RESULT_URL=https://$RAILWAY_DOMAIN/webhooks/mpesa/b2c/result\""
((COUNT++))
echo "✓ MPESA_B2C_RESULT_URL (auto-configured)"

CMD="$CMD --set \"MPESA_B2C_QUEUE_TIMEOUT_URL=https://$RAILWAY_DOMAIN/webhooks/mpesa/b2c/timeout\""
((COUNT++))
echo "✓ MPESA_B2C_QUEUE_TIMEOUT_URL (auto-configured)"

# Communication - Twilio
if is_valid_value "$TWILIO_ACCOUNT_SID"; then
    CMD="$CMD --set \"TWILIO_ACCOUNT_SID=$TWILIO_ACCOUNT_SID\""
    ((COUNT++))
    echo "✓ TWILIO_ACCOUNT_SID"
fi

if is_valid_value "$TWILIO_AUTH_TOKEN"; then
    CMD="$CMD --set \"TWILIO_AUTH_TOKEN=$TWILIO_AUTH_TOKEN\""
    ((COUNT++))
    echo "✓ TWILIO_AUTH_TOKEN"
fi

if is_valid_value "$TWILIO_PHONE_NUMBER"; then
    CMD="$CMD --set \"TWILIO_PHONE_NUMBER=$TWILIO_PHONE_NUMBER\""
    ((COUNT++))
    echo "✓ TWILIO_PHONE_NUMBER"
fi

# Communication - Telegram
if is_valid_value "$TELEGRAM_BOT_TOKEN"; then
    CMD="$CMD --set \"TELEGRAM_BOT_TOKEN=$TELEGRAM_BOT_TOKEN\""
    ((COUNT++))
    echo "✓ TELEGRAM_BOT_TOKEN"
fi

# Telegram webhook URL (auto-configure for production)
CMD="$CMD --set \"TELEGRAM_WEBHOOK_URL=https://$RAILWAY_DOMAIN/webhooks/telegram\""
((COUNT++))
echo "✓ TELEGRAM_WEBHOOK_URL (auto-configured)"

# Application Settings - Production values
CMD="$CMD --set \"APP_ENV=production\""
((COUNT++))
echo "✓ APP_ENV (production)"

CMD="$CMD --set \"ALLOWED_ORIGINS=https://$RAILWAY_DOMAIN\""
((COUNT++))
echo "✓ ALLOWED_ORIGINS (auto-configured)"

# Secret Key - Generate if not set or is placeholder
if is_valid_value "$SECRET_KEY"; then
    CMD="$CMD --set \"SECRET_KEY=$SECRET_KEY\""
    ((COUNT++))
    echo "✓ SECRET_KEY (from .env)"
else
    # Generate random secret key
    NEW_SECRET_KEY=$(openssl rand -hex 32)
    CMD="$CMD --set \"SECRET_KEY=$NEW_SECRET_KEY\""
    ((COUNT++))
    echo "✓ SECRET_KEY (auto-generated)"
fi

# Voice AI setting (if specified)
if [ ! -z "$START_TELEGRAM_BOT" ]; then
    CMD="$CMD --set \"START_TELEGRAM_BOT=$START_TELEGRAM_BOT\""
    ((COUNT++))
    echo "✓ START_TELEGRAM_BOT"
fi

echo -e "\n${YELLOW}📤 Setting $COUNT variables on Railway...${NC}\n"

# Execute command
eval $CMD

echo -e "\n${GREEN}✅ Successfully set $COUNT environment variables!${NC}"
echo -e "${GREEN}🔄 Railway will automatically redeploy with new configuration${NC}"
echo -e "\n${YELLOW}📋 Next Steps:${NC}"
echo "1. Monitor deployment: railway logs"
echo "2. Test health: curl https://$RAILWAY_DOMAIN/health"
echo "3. Test miniapps: https://$RAILWAY_DOMAIN/campaigns.html"
echo "4. Test admin: https://$RAILWAY_DOMAIN/admin/dashboard.html"
echo -e "\n${YELLOW}🔗 External Services Configuration:${NC}"
echo "• Telegram: Set webhook via bot or Railway will auto-configure"
echo "• Stripe: Add webhook URL: https://$RAILWAY_DOMAIN/webhooks/stripe"
echo "• M-Pesa: Add callback URLs (already configured in variables)"
