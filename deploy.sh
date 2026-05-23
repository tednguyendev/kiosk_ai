#!/bin/bash
# Deploy to Netlify
# Usage: NETLIFY_AUTH_TOKEN=xxx ./deploy.sh
# Or set NETLIFY_AUTH_TOKEN in your .bashrc/.zshrc

echo "🚀 Deploying to Netlify..."

# Check for token
if [ -z "$NETLIFY_AUTH_TOKEN" ]; then
    echo "❌ Error: NETLIFY_AUTH_TOKEN not set"
    echo "   Run: export NETLIFY_AUTH_TOKEN=your_token"
    exit 1
fi

# Check if netlify CLI is installed
if ! command -v netlify &> /dev/null; then
    echo "Installing Netlify CLI..."
    npm install -g netlify-cli
fi

# Deploy
netlify deploy --prod --site=af102dd2-52fc-48b5-a799-26a683abed1c --auth="$NETLIFY_AUTH_TOKEN"

echo "✅ Done!"
