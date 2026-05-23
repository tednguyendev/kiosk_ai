#!/bin/bash
# Deploy to Netlify
# Usage: ./deploy.sh

echo "🚀 Deploying to Netlify..."

# Check if netlify CLI is installed
if ! command -v netlify &> /dev/null; then
    echo "Installing Netlify CLI..."
    npm install -g netlify-cli
fi

# Deploy
netlify deploy --prod --site=af102dd2-52fc-48b5-a799-26a683abed1c

echo "✅ Done!"
