# Beverage Brands Dashboard - Deployment Guide

Complete guide for deploying the Beverage Brands Dashboard to Render.com.

## Prerequisites

1. **Render.com Account**: Sign up at https://render.com (free tier available)
2. **RapidAPI Account**: Get API keys at https://rapidapi.com
3. **GitHub Account**: For hosting your code
4. **Git**: Installed locally

## Quick Deploy (One-Click)

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

Click the button above to deploy directly from this repository. You'll still need to configure environment variables after deployment.

## Manual Deployment Steps

### Step 1: Prepare Your Repository

1. Fork or clone this repository to your GitHub account
2. Ensure the following files are present:
   - `render.yaml` - Render configuration
   - `Dockerfile` - Container build instructions
   - `backend/requirements.txt` - Python dependencies
   - `frontend/package.json` - Node dependencies

### Step 2: Create New Web Service on Render

1. Log in to [Render Dashboard](https://dashboard.render.com)
2. Click **New +** → **Web Service**
3. Connect your GitHub repository
4. Configure the service:
   - **Name**: `beverage-brands-dashboard` (or your preferred name)
   - **Environment**: Docker
   - **Dockerfile Path**: `./Dockerfile`
   - **Plan**: Free

### Step 3: Configure Environment Variables

In the Render dashboard, go to **Environment** and add these variables:

#### Required Variables

| Variable | Value | Description |
|----------|-------|-------------|
| `DATABASE_URL` | `sqlite:////app/data/beverage_brands.db` | SQLite path with persistent disk |
| `JWT_SECRET` | (auto-generated or your own) | Generate with `openssl rand -base64 32` |
| `CORS_ORIGINS` | `https://your-app-name.onrender.com` | Your Render app URL |
| `RAPIDAPI_KEY` | (your key) | Get from RapidAPI dashboard |

#### Optional Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `AUTO_SYNC_HOURS` | 6 | Hours between auto-syncs (0 to disable) |
| `TIKTOK_RATE_LIMIT_DELAY` | 4 | Seconds between TikTok API calls |
| `INSTAGRAM_RATE_LIMIT_DELAY` | 4 | Seconds between Instagram API calls |
| `GOOGLE_SHEETS_ID` | - | For Google Sheets integration |
| `GOOGLE_CREDENTIALS_JSON` | - | Service account JSON |

### Step 4: Add Persistent Disk

1. In Render dashboard, go to **Disks**
2. Click **Add Disk**
3. Configure:
   - **Name**: `beverage-data`
   - **Mount Path**: `/app/data`
   - **Size**: 1 GB (free tier max)

### Step 5: Deploy

1. Click **Create Web Service**
2. Wait for the build to complete (5-10 minutes)
3. Once deployed, visit your app URL (shown in dashboard)

### Step 6: Initialize Database

After first deployment, you may need to initialize the database:

```bash
# Option 1: Via Render Shell
# Go to Render Dashboard → Your Service → Shell
# Run:
cd /app/backend && python init_db.py

# Option 2: Via API endpoint (if implemented)
curl https://your-app.onrender.com/api/init-db
```

### Step 7: Update CORS Origins

After deployment, update the `CORS_ORIGINS` environment variable with your actual Render URL:

```
CORS_ORIGINS=https://beverage-brands-dashboard-xyz.onrender.com
```

Then redeploy (Render will auto-deploy on env var changes).

## Post-Deployment Setup

### 1. Create Admin User

The default users are hardcoded in `backend/app.py`:
- Username: `fred` / Password: `123456` (regular user)
- Username: `admin` / Password: `password123` (admin)

**Important**: Change these passwords in production by modifying `USERS` in `app.py` or implementing proper user management.

### 2. Configure RapidAPI

1. Sign up at https://rapidapi.com
2. Subscribe to:
   - [TikTok API](https://rapidapi.com/tiktok-api)
   - [Instagram Looter](https://rapidapi.com/instagram-looter)
3. Copy your RapidAPI key to the `RAPIDAPI_KEY` environment variable

### 3. Test Social Sync

1. Log in to your deployed dashboard
2. Go to **Social Sync** page
3. Click **Sync Now** to test the connection

## Troubleshooting

### Build Failures

**Problem**: Docker build fails
```
Solution: Check that all files are committed to git
Run: git status
Ensure Dockerfile and render.yaml are tracked
```

**Problem**: npm install fails
```
Solution: Delete node_modules and package-lock.json locally
Commit the changes and redeploy
```

### Database Issues

**Problem**: Database not persisting
```
Solution: 
1. Verify disk is mounted at /app/data
2. Check DATABASE_URL=sqlite:////app/data/beverage_brands.db
3. Ensure disk size < 1GB (free tier limit)
```

**Problem**: "database is locked" errors
```
Solution: SQLite on network drives can have issues
Consider upgrading to PostgreSQL ($7/month on Render)
```

### API Connection Issues

**Problem**: Frontend can't connect to backend
```
Solution:
1. Check CORS_ORIGINS includes your Render URL
2. Verify REACT_APP_API_URL is empty (for same-domain deployment)
3. Check browser console for CORS errors
```

**Problem**: RapidAPI rate limits
```
Solution:
1. Increase TIKTOK_RATE_LIMIT_DELAY and INSTAGRAM_RATE_LIMIT_DELAY
2. Check RapidAPI dashboard for quota usage
3. Consider upgrading RapidAPI plan
```

### Performance Issues

**Problem**: App is slow
```
Solution:
1. Free tier has 512MB RAM - consider upgrading
2. Database queries may need optimization
3. Enable caching (Redis available as add-on)
```

## Upgrading

### To PostgreSQL

1. Create PostgreSQL database in Render dashboard
2. Update `DATABASE_URL` to PostgreSQL connection string
3. Remove or comment out the `disk` section in render.yaml
4. Redeploy

### To Paid Tier

1. Go to Render Dashboard → Your Service → Settings
2. Change Plan to Starter ($7/month)
3. Benefits: More RAM, faster builds, custom domains

## Environment-Specific Configuration

### Local Development
```bash
# .env file for local development
DATABASE_URL=sqlite:///./beverage_brands.db
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
REACT_APP_API_URL=http://localhost:8000
JWT_SECRET=dev-secret-not-for-production
RAPIDAPI_KEY=your-key-here
```

### Production (Render)
```bash
# Environment variables in Render dashboard
DATABASE_URL=sqlite:////app/data/beverage_brands.db
CORS_ORIGINS=https://your-app.onrender.com
REACT_APP_API_URL=  # Empty - same domain
JWT_SECRET=(generate with openssl rand -base64 32)
RAPIDAPI_KEY=your-production-key
```

## Security Checklist

- [ ] Changed JWT_SECRET from default
- [ ] Changed default user passwords
- [ ] Using HTTPS (Render provides this)
- [ ] Restricted CORS origins
- [ ] API keys in environment variables only
- [ ] No secrets committed to git

## Support

- **Render Docs**: https://render.com/docs
- **FastAPI Docs**: https://fastapi.tiangolo.com
- **React Docs**: https://react.dev

## Monitoring

- Check **Logs** in Render dashboard for errors
- Monitor **Metrics** for performance
- Set up **Health Checks** to detect issues
