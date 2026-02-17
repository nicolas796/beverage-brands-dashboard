from fastapi import FastAPI, Depends, HTTPException, Query, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import os
import asyncio
import jwt
from pydantic import BaseModel

from models import get_session_factory, init_database
from database import (
    get_db, get_brands, get_brand_by_id, get_brand_by_name,
    get_categories, get_metrics, get_growth_data, get_follower_growth,
    get_top_growing_brands, get_brand_rankings, get_recent_syncs,
    export_brands_to_csv, export_metrics_to_csv
)
from api.brands import router as brands_router
from api.rankings import router as rankings_router
from api.metrics import router as metrics_router
from api.social_sync import router as social_sync_router
from services.credits_tracker import CreditsTracker, get_usage_summary

# JWT Configuration
JWT_SECRET = os.getenv('JWT_SECRET')
if not JWT_SECRET:
    # Generate a warning in production, use default for development only
    import warnings
    warnings.warn(
        "JWT_SECRET not set! Using default secret. "
        "This is insecure for production. Set JWT_SECRET environment variable.",
        RuntimeWarning
    )
    JWT_SECRET = 'dev-secret-not-for-production-change-me'

JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24

# User configuration - can be overridden via environment
# Format: USER_<username>=password:role:name
# Example: USER_FRED=securepass:user:Fred,USER_ADMIN=adminpass:admin:Administrator
def load_users_from_env():
    """Load users from environment variables or use defaults for development"""
    users = {}
    
    # Check for environment-based users
    for key, value in os.environ.items():
        if key.startswith('USER_'):
            username = key[5:].lower()
            try:
                password, role, name = value.split(':', 2)
                permissions = ['view_dashboard', 'view_brands', 'view_rankings', 'view_billing']
                if role == 'admin':
                    permissions.extend(['approve_brands', 'manage_settings'])
                users[username] = {
                    'id': username,
                    'username': username,
                    'password': password,
                    'role': role,
                    'name': name,
                    'permissions': permissions
                }
            except ValueError:
                print(f"Warning: Invalid USER_ format for {key}. Expected: password:role:name")
    
    # Fallback to default users for development only
    if not users and os.getenv('NODE_ENV') != 'production':
        users = {
            'fred': {
                'id': 'fred',
                'username': 'fred',
                'password': os.getenv('DEFAULT_USER_PASSWORD', '123456'),
                'role': 'user',
                'name': 'Fred',
                'permissions': ['view_dashboard', 'view_brands', 'view_rankings', 'view_billing']
            },
            'admin': {
                'id': 'admin',
                'username': 'admin',
                'password': os.getenv('DEFAULT_ADMIN_PASSWORD', 'password123'),
                'role': 'admin',
                'name': 'Admin',
                'permissions': ['view_dashboard', 'view_brands', 'view_rankings', 'view_billing', 'approve_brands', 'manage_settings']
            }
        }
    
    return users

USERS = load_users_from_env()

# Pydantic models
class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict

# Initialize FastAPI app
app = FastAPI(
    title="Beverage Brands Social Listening API",
    description="API for tracking beverage brand social media metrics",
    version="1.0.0"
)

# CORS configuration
origins = os.getenv('CORS_ORIGINS', 'http://localhost:3000,http://localhost:5173').split(',')
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auth helper functions
def create_access_token(user_id: str) -> str:
    """Create JWT access token"""
    expiration = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    payload = {
        'sub': user_id,
        'exp': expiration,
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_token(token: str) -> Optional[dict]:
    """Verify JWT token and return user data"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get('sub')
        if user_id and user_id in USERS:
            user = USERS[user_id].copy()
            del user['password']  # Remove password from response
            return user
        return None
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

async def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    """Dependency to get current authenticated user"""
    # Skip auth for health check and login endpoints
    # In production, you'd want stricter control
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Extract token from "Bearer <token>"
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    token = parts[1]
    user = verify_token(token)
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    return user

# Auth endpoints
@app.post("/api/auth/login", response_model=TokenResponse)
async def login(credentials: LoginRequest):
    """Authenticate user and return JWT token"""
    username = credentials.username.lower().strip()
    user = USERS.get(username)
    
    if not user or user['password'] != credentials.password:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    # Create access token
    access_token = create_access_token(user['id'])
    
    # Return user without password
    user_response = user.copy()
    del user_response['password']
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user_response
    }

@app.get("/api/auth/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    """Get current authenticated user info"""
    return current_user

@app.post("/api/auth/refresh")
async def refresh_token(current_user: dict = Depends(get_current_user)):
    """Refresh access token"""
    new_token = create_access_token(current_user['id'])
    return {
        "access_token": new_token,
        "token_type": "bearer"
    }

# Include routers
app.include_router(brands_router, prefix="/api/brands", tags=["brands"])
app.include_router(rankings_router, prefix="/api/rankings", tags=["rankings"])
app.include_router(metrics_router, prefix="/api/metrics", tags=["metrics"])
app.include_router(social_sync_router, prefix="/api/social", tags=["social_sync"])


@app.get("/")
async def root():
    """Root endpoint with API info"""
    return {
        "name": "Beverage Brands Social Listening API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "brands": "/api/brands",
            "rankings": "/api/rankings",
            "metrics": "/api/metrics",
            "social": "/api/social",
            "export": "/api/export",
            "auth": "/api/auth"
        }
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.get("/api/categories")
async def categories(db: Session = Depends(get_db)):
    """Get all unique brand categories"""
    cats = get_categories(db)
    return {"categories": cats}


@app.get("/api/dashboard")
async def dashboard(
    db: Session = Depends(get_db),
    platform: str = Query(default='instagram', description='Social platform'),
    top_n: int = Query(default=10, ge=1, le=50)
):
    """Get dashboard summary data"""
    # Top growing brands (7 days)
    top_7d = get_top_growing_brands(db, platform=platform, days=7, limit=top_n)
    
    # Top growing brands (30 days)
    top_30d = get_top_growing_brands(db, platform=platform, days=30, limit=top_n)
    
    # Brand count by category
    from database import get_db_session
    session = get_db_session()
    from sqlalchemy import func
    from models import Brand
    category_counts = session.query(
        Brand.category, 
        func.count(Brand.id).label('count')
    ).group_by(Brand.category).all()
    session.close()
    
    # Recent sync info
    recent_syncs = get_recent_syncs(db, limit=5)
    
    return {
        "top_growing_7d": top_7d,
        "top_growing_30d": top_30d,
        "category_distribution": [{"category": cat, "count": count} for cat, count in category_counts],
        "recent_syncs": [s.to_dict() for s in recent_syncs],
        "generated_at": datetime.utcnow().isoformat()
    }


@app.get("/api/credits/usage")
async def get_credits_usage(days: int = Query(default=30, ge=1, le=365)):
    """Get credit usage statistics."""
    try:
        summary = get_usage_summary(days)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/credits/budget")
async def get_credits_budget():
    """Get current budget status."""
    try:
        tracker = CreditsTracker()
        budget = tracker.get_budget_status()
        tracker.close()
        return budget
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/sync")
async def trigger_sync(db: Session = Depends(get_db)):
    """Trigger manual data sync (placeholder for actual sync implementation)"""
    # This would call the sheets_sync service
    from services.sheets_sync import sync_from_sheets
    
    try:
        result = sync_from_sheets()
        return {
            "status": "success",
            "message": "Sync completed",
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/export/brands")
async def export_brands(format: str = Query(default='csv'), db: Session = Depends(get_db)):
    """Export brands data"""
    if format == 'csv':
        csv_data = export_brands_to_csv(db)
        return StreamingResponse(
            iter([csv_data]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=brands.csv"}
        )
    else:
        brands = get_brands(db)
        return {"brands": [b.to_dict() for b in brands]}


@app.get("/api/export/metrics")
async def export_metrics(
    brand_id: Optional[int] = None,
    format: str = Query(default='csv'),
    db: Session = Depends(get_db)
):
    """Export metrics data"""
    if format == 'csv':
        csv_data = export_metrics_to_csv(db, brand_id)
        filename = f"metrics{'_' + str(brand_id) if brand_id else ''}.csv"
        return StreamingResponse(
            iter([csv_data]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    else:
        metrics_list = get_metrics(db, brand_id=brand_id)
        return {"metrics": [m.to_dict() for m in metrics_list]}


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    print("Starting up...")
    # Database will be initialized via init_db.py or Docker entrypoint


# Serve frontend in production
frontend_path = os.getenv('FRONTEND_BUILD_PATH', '../frontend/build')
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=f"{frontend_path}/static"), name="static")
    
    @app.get("/")
    async def serve_index():
        return FileResponse(f"{frontend_path}/index.html")
    
    @app.get("/{path:path}")
    async def serve_spa(path: str):
        # Check if it's an API route
        if path.startswith("api/") or path.startswith("docs") or path.startswith("openapi.json"):
            raise HTTPException(status_code=404, detail="Not found")
        # Serve index.html for all other routes (SPA support)
        index_file = f"{frontend_path}/index.html"
        if os.path.exists(index_file):
            return FileResponse(index_file)
        raise HTTPException(status_code=404, detail="Not found")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv('API_PORT', 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
