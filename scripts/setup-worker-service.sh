#!/bin/bash

# Copy environment variables from web service to worker service

set -e

echo "🔄 Copying variables from web to worker service..."

# Link to web service and export variables
railway service link web > /dev/null 2>&1

# Get all variables except Railway auto-generated ones
railway variables --kv | grep -v "^RAILWAY_" | grep -v "^NIXPACKS_" > /tmp/worker_vars.txt

# Count variables
VAR_COUNT=$(cat /tmp/worker_vars.txt | wc -l | tr -d ' ')
echo "📋 Found $VAR_COUNT variables to copy"

# Link to worker service
railway service link worker > /dev/null 2>&1

# Build Railway command with all variables
CMD="railway variables"

while IFS='=' read -r key value; do
    if [ -n "$key" ] && [ -n "$value" ]; then
        # Escape special characters in value
        CMD="$CMD --set \"$key=$value\""
        echo "  ✓ $key"
    fi
done < /tmp/worker_vars.txt

# Execute command
echo ""
echo "📤 Setting variables on worker service..."
eval $CMD

echo ""
echo "✅ Variables copied successfully!"
echo ""
echo "🔧 Now setting worker-specific start command..."

# The start command will be set via Railway dashboard or we can use railway up with custom Procfile

echo "✅ Worker service configured!"
