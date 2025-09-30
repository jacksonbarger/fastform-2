# 🚂 FastForm API - Railway Deployment Guide

## Quick Deploy Steps

### 1. 🔐 **Login to Railway**
```bash
railway login
```
This opens your browser to authenticate with Railway.

### 2. 🚀 **Initialize Railway Project**
```bash
railway init
# Choose: "Empty Project" 
# Name it: "fastform-api"
```

### 3. 📤 **Deploy Your API**
```bash
railway up
```
This deploys your FastForm API to the cloud!

### 4. 🌐 **Get Your Live URL**
```bash
railway domain
```
Railway will give you a URL like: `https://fastform-api-production-xxxx.up.railway.app`

## 🔧 **Configuration Files Created:**

✅ `Dockerfile` - Container configuration  
✅ `requirements.txt` - Python dependencies  
✅ `railway.toml` - Railway-specific settings  

## 🎯 **What Happens After Deploy:**

1. **Your API becomes globally accessible** at the Railway URL
2. **Database included** - Your `fastform.db` with 6 formularies deployed
3. **Health checks enabled** - Railway monitors `/v1/health` endpoint
4. **Auto-restarts** if the service goes down

## 📱 **Next Steps After Cloud Deploy:**

### Update Desktop App:
```bash
cd /Users/jacksonbarger/fastform-desktop
# Edit src/App.tsx to use your new Railway URL instead of localhost:8000
```

### Test Your Cloud API:
```bash
# Replace with your actual Railway URL
curl https://your-railway-url.railway.app/v1/health
curl https://your-railway-url.railway.app/v1/formularies/
```

## 💰 **Railway Pricing:**
- **Free**: $5/month usage credit
- **Pro**: $20/month for production apps
- **Perfect for FastForm**: ~$5-10/month expected usage

## 🔒 **Security Notes:**
- Railway handles HTTPS automatically
- Your database is included in the container
- Consider PostgreSQL for production scaling

Ready to deploy? Run the commands above! 🚀
