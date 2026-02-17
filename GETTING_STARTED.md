# Getting Started

## Quick Start with Docker

```bash
cd web-interface
docker-compose up --build
```

Access the app at http://localhost:8000

## Local Development Setup

### Backend Setup

```bash
cd web-interface/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialize database with sample data
python init_db.py

# Start development server
uvicorn app:app --reload --port 8000
```

The API will be available at http://localhost:8000
API documentation at http://localhost:8000/docs

### Frontend Setup

```bash
cd web-interface/frontend

# Install dependencies
npm install

# Start development server
npm start
```

The frontend will be available at http://localhost:3000

## Environment Configuration

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

## Google Sheets Integration

1. Create a Google Cloud project and enable Google Sheets API
2. Download service account credentials as `credentials.json`
3. Place in `backend/credentials.json`
4. Set `GOOGLE_SHEETS_ID` in your `.env`
5. Share your Google Sheet with the service account email

## Deployment

### Render.com

1. Push code to GitHub
2. Connect repository to Render
3. Render will use `render.yaml` for configuration
4. Set environment variables in Render dashboard

### Docker

```bash
docker build -t beverage-brands .
docker run -p 8000:8000 -e DATABASE_URL=sqlite:////app/data/beverage_brands.db beverage-brands
```
