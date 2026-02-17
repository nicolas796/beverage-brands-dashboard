# Social Media API Integration Documentation

This document describes the TikTok and Instagram API integration for the Beverage Brands Social Listening platform.

## Overview

The integration uses RapidAPI to fetch social media metrics for brands:
- **TikTok API** by apibox (tiktok-api23)
- **Instagram Looter** by IRROR Systems (instagram-looter2)

## API Rate Limits

| Platform | Hourly | Monthly |
|----------|--------|---------|
| TikTok | 1000 | 100 |
| Instagram | 1000 | 150 |

## Files Created

### Service Layer
- `/services/tiktok_api.py` - TikTok API client with rate limiting
- `/services/instagram_api.py` - Instagram API client with rate limiting
- `/services/social_sync.py` - Sync orchestration service

### API Endpoints
- `/api/social_sync.py` - REST endpoints for social sync

## API Endpoints

### 1. Test API Connectivity
```
POST /api/social/sync/test?tiktok_username={username}&instagram_username={username}
```
Tests the APIs without saving data.

### 2. Sync Single Brand
```
POST /api/social/sync/{brand_id}
```
Syncs social metrics for a specific brand.

### 3. Sync All Brands
```
POST /api/social/sync?sync_all=true
```
Syncs all brands with social media handles.

### 4. Check Rate Limits
```
GET /api/social/sync/limits
```
Returns current rate limit status.

### 5. Check Sync Status
```
GET /api/social/sync/status
```
Returns sync status and rate limits.

### 6. Sync History
```
GET /api/social/sync/history?limit=10
```
Returns history of sync operations.

### 7. Brand Social Status
```
GET /api/social/brands/{brand_id}/social
```
Returns social media status for a specific brand.

## Usage Examples

### Test the APIs
```bash
curl -X POST "http://localhost:8000/api/social/sync/test?tiktok_username=celsiusofficial&instagram_username=celsiusofficial"
```

### Sync a Single Brand
```bash
curl -X POST "http://localhost:8000/api/social/sync/3"
```

### Sync All Brands
```bash
curl -X POST "http://localhost:8000/api/social/sync?sync_all=true"
```

### Check Rate Limits
```bash
curl "http://localhost:8000/api/social/sync/limits"
```

## Environment Variables

Add to your `.env` file:
```
RAPIDAPI_KEY=your_rapidapi_key_here
SYNC_DELAY=2  # seconds between API calls
```

## Data Extracted

### TikTok Metrics
- Followers count
- Following count
- Total likes (hearts)
- Video count
- Nickname
- Bio/signature
- Verified status
- Profile picture URL

### Instagram Metrics
- Followers count
- Following count
- Posts count
- Full name
- Biography
- Verified status
- Business account status
- Profile picture URL
- External URL

## Database Schema

Metrics are saved to the `social_metrics` table with:
- `brand_id` - Reference to the brand
- `platform` - 'tiktok' or 'instagram'
- `followers` - Follower count
- `following` - Following count
- `posts` - Post count (Instagram) or video count (TikTok)
- `likes` - Like count (TikTok)
- `recorded_at` - Timestamp of the metric

## Rate Limit Handling

The integration includes:
- In-memory rate limit tracking
- Automatic delays between requests (configurable)
- Exponential backoff on errors
- Clear error messages when limits exceeded

## Error Handling

Common errors:
- `404` - User not found on platform
- `429` - Rate limit exceeded
- `401` - Invalid API key
- `500` - Server error

## Testing Results

Tested successfully with the following brands:

| Brand | TikTok Handle | Instagram Handle |
|-------|---------------|------------------|
| Poppi | drinkpoppi | drinkpoppi |
| OLIPOP | drinkolipop | drinkolipop |
| Celsius | celsiusofficial | celsiusofficial |
| Liquid Death | liquiddeath | liquiddeath |
| Ghost Energy | ghostenergy | ghostenergy |
| Prime Hydration | drinkprime | drinkprime |
| Alani Nu | alaninu | alanienergy |
| Health-Ade | healthade | healthade |
| Spindrift | spindrift | spindriftfresh |
| Super Coffee | drinksupercoffee | drinksupercoffee |

## Maintenance

### Monthly Reset
The monthly rate limits reset automatically. The counters are in-memory only and reset when the server restarts.

### API Key Management
If you need to rotate the RapidAPI key:
1. Update the `RAPIDAPI_KEY` environment variable
2. Restart the server

### Monitoring
Monitor the sync logs and rate limit status via:
- `/api/social/sync/history` - View sync history
- `/api/social/sync/limits` - Check remaining quota

## Troubleshooting

### High Error Rate
- Check rate limits with `/api/social/sync/limits`
- Verify API key is valid
- Check RapidAPI dashboard for subscription status

### Missing Data
- Ensure brand has social handles configured
- Check individual brand with `/api/social/brands/{id}/social`
- Review server logs for errors

### Rate Limit Exceeded
- Wait for hourly reset
- Reduce sync frequency
- Consider upgrading RapidAPI subscription
