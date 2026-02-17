# Render Deployment Checklist

Use this checklist to ensure successful deployment to Render.com.

## Pre-Deployment

- [ ] All code committed to git
- [ ] `.env` file added to `.gitignore`
- [ ] No secrets in committed code
- [ ] `render.yaml` is valid YAML
- [ ] `Dockerfile` builds locally (test with `docker build .`)
- [ ] Environment variables documented in `.env.example`

## Environment Variables Setup

### Required (Must set before first deploy)

- [ ] `JWT_SECRET` - Generate with `openssl rand -base64 32`
- [ ] `RAPIDAPI_KEY` - From RapidAPI dashboard
- [ ] `CORS_ORIGINS` - Your Render app URL

### Optional (Can set later)

- [ ] `GOOGLE_SHEETS_ID` - For Google Sheets sync
- [ ] `GOOGLE_CREDENTIALS_JSON` - Service account JSON
- [ ] `AUTO_SYNC_HOURS` - Default is 6

## Deployment Steps

1. [ ] Push code to GitHub
2. [ ] Create new Web Service on Render
3. [ ] Select Docker environment
4. [ ] Set all required environment variables
5. [ ] Add persistent disk (1GB, mount at /app/data)
6. [ ] Deploy and wait for build
7. [ ] Check logs for errors
8. [ ] Visit app URL to verify
9. [ ] Log in with default credentials
10. [ ] Test social sync functionality

## Post-Deployment Verification

### Health Checks

- [ ] `GET /api/health` returns 200 OK
- [ ] Frontend loads without errors
- [ ] Can log in successfully
- [ ] Dashboard displays data

### Functionality Tests

- [ ] Brand list loads
- [ ] Rankings page works
- [ ] Social sync triggers (may need RapidAPI key)
- [ ] CSV export works
- [ ] Database persists after restart

### Security Checks

- [ ] Changed default JWT_SECRET
- [ ] CORS origins restricted to production domain
- [ ] No sensitive data in environment variables exposed to frontend

## Troubleshooting Common Issues

### Build Fails

```bash
# Test build locally
docker build -t beverage-dashboard .
docker run -p 8000:8000 beverage-dashboard
```

### Database Not Persisting

1. Check disk is mounted at `/app/data`
2. Verify `DATABASE_URL=sqlite:////app/data/beverage_brands.db`
3. Check disk usage in Render dashboard (< 1GB)

### CORS Errors

1. Update `CORS_ORIGINS` with exact Render URL
2. Include both `https://` and `http://` if needed
3. Redeploy after changing env vars

### API Not Responding

1. Check logs in Render dashboard
2. Verify `API_PORT=8000` (Render expects this)
3. Ensure health check endpoint works: `/api/health`

## Cost Estimation

### Free Tier (Sufficient for testing)

- Web Service: $0
- Disk (1GB): $0
- **Total: $0/month**

### Starter Tier (Recommended for production)

- Web Service: $7/month
- Disk (1GB): $0
- PostgreSQL (optional): $7/month
- **Total: $7-14/month**

## Upgrade Path

1. **Start**: Free tier with SQLite
2. **Growth**: Upgrade to Starter for better performance
3. **Scale**: Add PostgreSQL for concurrent users
4. **Advanced**: Add Redis caching if needed

## Rollback Plan

If deployment fails:

1. Check logs in Render dashboard
2. Revert to last working commit
3. Push to trigger new deployment
4. Contact Render support if issues persist

## Notes

- First deployment may take 5-10 minutes
- SQLite has limitations for concurrent writes
- Consider PostgreSQL for production with multiple users
- RapidAPI free tier has rate limits (500 requests/day)
