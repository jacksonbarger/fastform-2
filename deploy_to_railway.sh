#!/bin/bash

echo "🚂 FastForm API Railway Deployment Script"
echo "========================================"
echo ""

# Check if logged in
echo "Checking Railway login status..."
if ! railway whoami > /dev/null 2>&1; then
    echo ""
    echo "⚠️  Not logged into Railway. Please run:"
    echo "   railway login --browserless"
    echo ""
    echo "Then visit the URL provided and enter the pairing code."
    echo "After login, run this script again."
    echo ""
    exit 1
fi

echo "✅ Logged into Railway!"
echo ""

# Check if project is linked
echo "Checking project status..."
if ! railway environment > /dev/null 2>&1; then
    echo "⚠️  No project linked. Creating and linking project..."
    railway init --name fastform-api
    railway link
fi

echo "✅ Project linked!"
echo ""

# Deploy
echo "🚀 Deploying FastForm API to Railway..."
railway up --detach

echo ""
echo "🌐 Getting your live URL..."
sleep 5
railway domain

echo ""
echo "✅ Deployment complete!"
echo ""
echo "Your FastForm API is now live! 🎉"
echo ""
echo "Next steps:"
echo "1. Test your API: curl [YOUR-URL]/v1/health"
echo "2. Update desktop app to use cloud URL"
echo "3. Build mobile app using cloud API"

