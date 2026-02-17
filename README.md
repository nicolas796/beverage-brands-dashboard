# Beverage Brands Dashboard

A full-stack web application for tracking and analyzing beverage brand social media metrics. Built with FastAPI, React, and SQLite.

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

## Features

- 📊 **Dashboard**: Visualize brand growth, rankings, and metrics
- 🔍 **Brand Research**: Research and track beverage brands
- 📱 **Social Sync**: Sync TikTok and Instagram metrics via RapidAPI
- 📈 **Analytics**: Track follower growth, engagement rates, and rankings
- 📤 **Export**: Export data to CSV
- 🔐 **Authentication**: JWT-based user authentication

## Tech Stack

**Backend:**
- FastAPI (Python)
- SQLAlchemy ORM
- SQLite (with PostgreSQL option)
- JWT Authentication

**Frontend:**
- React 18
- Chart.js for visualizations
- React Router for navigation
- Axios for API calls

**Infrastructure:**
- Docker containerization
- Render.com hosting
- Persistent disk for database

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Git

### Local Development

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd web-interface
```

2. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. **Start the backend**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python init_db.py
uvicorn app:app --reload --port 8000
```

4. **Start the frontend (new terminal)**
```bash
cd frontend
npm install
npm start
```

5. **Open the app**
Navigate to http://localhost:3000

**Default Login:**
- Username: `fred` / Password: `123456`
- Username: `admin` / Password: `password123`

## Deployment

See [DEPLOY.md](./DEPLOY.md) for detailed deployment instructions.

### One-Click Deploy

Click the "Deploy to Render" button above to deploy automatically.

### Manual Deploy

1. Push code to GitHub
2. Create new Web Service on Render
3. Connect your repository
4. Set environment variables
5. Deploy!

## Project Structure

```
web-interface/
├── backend/
│   ├── app.py              # FastAPI main application
│   ├── models.py           # Database models
│   ├── database.py         # Database operations
│   ├── init_db.py          # Database initialization
│   ├── requirements.txt    # Python dependencies
│   ├── api/                # API route handlers
│   │   ├── brands.py
│   │   ├── metrics.py
│   │   ├── rankings.py
│   │   └── social_sync.py
│   └── services/           # Business logic
│       ├── sheets_sync.py
│       └── credits_tracker.py
├── frontend/
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── pages/          # Page components
│   │   ├── utils/
│   │   │   └── api.js      # API client
│   │   └── index.js        # Entry point
│   ├── package.json
│   └── build/              # Production build
├── Dockerfile              # Container configuration
├── render.yaml             # Render.com configuration
└── DEPLOY.md               # Deployment guide
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | SQLite or PostgreSQL connection string |
| `JWT_SECRET` | Yes | Secret key for JWT tokens |
| `RAPIDAPI_KEY` | Yes | RapidAPI key for social sync |
| `CORS_ORIGINS` | Yes | Allowed CORS origins |
| `GOOGLE_SHEETS_ID` | No | Google Sheets integration |
| `AUTO_SYNC_HOURS` | No | Auto-sync interval (default: 6) |

See `.env.example` for full list.

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/health` | Health check |
| `POST /api/auth/login` | User login |
| `GET /api/auth/me` | Current user info |
| `GET /api/dashboard` | Dashboard data |
| `GET /api/brands` | List brands |
| `GET /api/brands/{id}` | Brand details |
| `GET /api/rankings` | Brand rankings |
| `GET /api/metrics` | Social metrics |
| `POST /api/sync` | Trigger data sync |

Full API documentation available at `/docs` when running locally.

## Database

**Default:** SQLite (easy setup, single file)

**Production Options:**
1. SQLite with persistent disk (Render free tier)
2. PostgreSQL (Render paid tier, $7/month)

To migrate to PostgreSQL, update `DATABASE_URL` to a PostgreSQL connection string.

## External Services

### RapidAPI (Required)

Used for social media data:
- **TikTok API**: Follower counts, video metrics
- **Instagram Looter**: Profile data, engagement stats

Get your API key at https://rapidapi.com

### Google Sheets (Optional)

Sync brand data from Google Sheets:
1. Create service account in Google Cloud Console
2. Share sheet with service account email
3. Set `GOOGLE_SHEETS_ID` and `GOOGLE_CREDENTIALS_JSON`

## Security

- JWT-based authentication
- CORS protection
- Environment variables for secrets
- No hardcoded credentials in production

**Important:** Change default passwords before production use!

## Free Tier Limits (Render)

- **RAM**: 512 MB
- **CPU**: Shared
- **Disk**: 1 GB
- **Bandwidth**: 100 GB/month
- **Builds**: Unlimited

Sufficient for small to medium usage. Upgrade to Starter ($7/month) for more resources.

## Troubleshooting

**Database locked errors?**
- Increase database timeout in code
- Consider upgrading to PostgreSQL

**RapidAPI rate limits?**
- Increase `TIKTOK_RATE_LIMIT_DELAY` and `INSTAGRAM_RATE_LIMIT_DELAY`

**CORS errors?**
- Verify `CORS_ORIGINS` includes your domain

See [DEPLOY.md](./DEPLOY.md) for more troubleshooting.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - feel free to use for your own projects.

## Support

- Create an issue for bugs
- Check DEPLOY.md for deployment help
- Review code comments for implementation details
