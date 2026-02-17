# 🚀 Quick Deploy to Render

This folder contains the Beverage Brands Dashboard ready for deployment on Render.com.

## ⚡ One-Click Deploy

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/yourusername/your-repo-name)

## 📋 Prerequisites

1. **Render.com account** (free)
2. **RapidAPI key** (get at https://rapidapi.com)
3. **GitHub account** (to host this code)

## 🔧 Required Environment Variables

Set these in the Render dashboard after deployment:

| Variable | How to Get | Example |
|----------|-----------|---------|
| `JWT_SECRET` | `openssl rand -base64 32` | Random 32+ char string |
| `RAPIDAPI_KEY` | RapidAPI Dashboard | Your API key |
| `CORS_ORIGINS` | Your Render URL | `https://app.onrender.com` |

## 📚 Documentation

- **DEPLOY.md** - Full deployment guide
- **DEPLOY_CHECKLIST.md** - Verification steps
- **DEPLOY_SUMMARY.md** - Package overview
- **README.md** - Project documentation

## 🏗️ What's Included

- ✅ FastAPI backend with SQLite database
- ✅ React frontend with Chart.js
- ✅ JWT authentication
- ✅ RapidAPI integration (TikTok + Instagram)
- ✅ Docker containerization
- ✅ Persistent disk configuration
- ✅ Health checks

## 💰 Cost

**Free Tier:** $0/month
- 512MB RAM
- 1GB persistent disk
- Sleeps after 15 min inactivity

**Starter Tier:** $7/month
- 1GB RAM
- Never sleeps
- Custom domain

## ⚠️ Important

1. Change default passwords after deployment
2. Set secure JWT_SECRET before going live
3. Add your RapidAPI key for social sync
4. See DEPLOY.md for complete setup

## 🆘 Support

Check **DEPLOY.md** for:
- Detailed setup instructions
- Troubleshooting guide
- Security checklist
- Upgrade paths

---

**Ready to deploy?** Click the button above or follow DEPLOY.md!
