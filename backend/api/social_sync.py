"""
Social Sync API Endpoints
Provides endpoints for triggering and monitoring social media sync
"""
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import logging

from database import get_db
from models import get_db_session, Brand
from services.social_sync import (
    sync_all_brands, 
    sync_single_brand, 
    get_sync_status,
    SocialSyncService
)

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()


# IMPORTANT: Static routes must come BEFORE parameterized routes!
# Order matters in FastAPI - /sync/{brand_id} will match /sync/test before /sync/test is checked


@router.get("/sync/status")
async def get_sync_status_endpoint():
    """
    Get current sync status and rate limit information
    
    Returns:
    - Rate limit status for TikTok and Instagram APIs
    - Last sync information
    """
    try:
        status = get_sync_status()
        return {
            "status": "success",
            "data": status,
            "checked_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Status check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sync/limits")
async def get_rate_limits():
    """
    Get current API rate limit status
    
    Shows remaining requests for:
    - TikTok API (1000/hour, 100/month)
    - Instagram API (1000/hour, 150/month)
    """
    try:
        service = SocialSyncService()
        limits = service.get_rate_limit_status()
        
        return {
            "status": "success",
            "rate_limits": limits,
            "checked_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Rate limit check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sync/history")
async def get_sync_history(
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get history of social media sync operations
    
    Query params:
    - limit: Number of sync logs to return (default: 10, max: 100)
    """
    try:
        from models import SyncLog
        
        syncs = db.query(SyncLog).filter(
            SyncLog.source == 'social_media_api'
        ).order_by(SyncLog.started_at.desc()).limit(limit).all()
        
        return {
            "status": "success",
            "count": len(syncs),
            "syncs": [s.to_dict() for s in syncs]
        }
    except Exception as e:
        logger.error(f"Sync history error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync/test")
async def test_sync(
    tiktok_username: Optional[str] = Query(default=None, description="TikTok username to test"),
    instagram_username: Optional[str] = Query(default=None, description="Instagram username to test")
):
    """
    Test the social media APIs without saving to database
    
    Useful for verifying API connectivity and rate limits
    """
    results = {
        "status": "success",
        "tiktok": None,
        "instagram": None,
        "tested_at": datetime.utcnow().isoformat()
    }
    
    try:
        if tiktok_username:
            from services.tiktok_api import get_tiktok_user
            results["tiktok"] = get_tiktok_user(tiktok_username)
        
        if instagram_username:
            from services.instagram_api import get_instagram_user
            results["instagram"] = get_instagram_user(instagram_username)
        
        if not tiktok_username and not instagram_username:
            raise HTTPException(
                status_code=400,
                detail="Provide at least one username to test"
            )
        
        return results
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Test sync error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync")
async def trigger_social_sync(
    background_tasks: BackgroundTasks,
    brand_ids: Optional[List[int]] = Query(default=None, description="Specific brand IDs to sync (optional)"),
    sync_all: bool = Query(default=False, description="Sync all brands with social handles"),
    db: Session = Depends(get_db)
):
    """
    Trigger social media sync for brands
    
    Query params:
    - brand_ids: List of specific brand IDs to sync
    - sync_all: Set to true to sync all brands with social handles
    
    Note: Either brand_ids or sync_all must be provided
    """
    # Validate parameters
    if not brand_ids and not sync_all:
        raise HTTPException(
            status_code=400, 
            detail="Either provide brand_ids or set sync_all=true"
        )
    
    try:
        # Get brands to sync info for response
        if brand_ids:
            brands = db.query(Brand).filter(Brand.id.in_(brand_ids)).all()
            brand_info = [{"id": b.id, "name": b.name} for b in brands]
        else:
            brands = db.query(Brand).filter(
                (Brand.tiktok_handle.isnot(None)) | (Brand.instagram_handle.isnot(None))
            ).all()
            brand_info = [{"id": b.id, "name": b.name} for b in brands]
        
        logger.info(f"Triggering sync for {len(brands)} brands")
        
        # Perform sync synchronously for immediate feedback
        # Note: sync_all_brands creates its own session internally
        # We pass brand_ids instead of the session to avoid session conflicts
        result = sync_all_brands(
            brand_ids=[b.id for b in brands] if brand_ids else None
        )
        
        if result.get('success'):
            return {
                "status": "success",
                "message": f"Synced {result.get('total_brands')} brands",
                "sync_id": result.get('sync_id'),
                "summary": {
                    "total_brands": result.get('total_brands'),
                    "tiktok_success": result.get('tiktok_success'),
                    "instagram_success": result.get('instagram_success'),
                    "errors": result.get('errors')
                },
                "brands_synced": brand_info,
                "started_at": result.get('started_at'),
                "completed_at": result.get('completed_at')
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=result.get('error', 'Sync failed')
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Sync error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Parameterized routes come AFTER static routes
@router.post("/sync/{brand_id}")
async def sync_single_brand_endpoint(
    brand_id: int,
    db: Session = Depends(get_db)
):
    """
    Sync social media metrics for a single brand
    
    Path params:
    - brand_id: ID of the brand to sync
    """
    try:
        # Check if brand exists
        brand = db.query(Brand).filter(Brand.id == brand_id).first()
        if not brand:
            raise HTTPException(status_code=404, detail=f"Brand with ID {brand_id} not found")
        
        logger.info(f"Syncing single brand: {brand.name} (ID: {brand_id})")
        
        # Perform sync (creates its own session internally)
        result = sync_single_brand(brand_id)
        
        if result.get('success'):
            return {
                "status": "success",
                "brand": {
                    "id": brand.id,
                    "name": brand.name,
                    "tiktok_handle": brand.tiktok_handle,
                    "instagram_handle": brand.instagram_handle
                },
                "tiktok": result.get('tiktok'),
                "instagram": result.get('instagram')
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=result.get('error', 'Sync failed')
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Single brand sync error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/brands/{brand_id}/social")
async def get_brand_social_status(
    brand_id: int,
    db: Session = Depends(get_db)
):
    """
    Get social media sync status for a specific brand
    
    Shows:
    - Current handles configured
    - Latest metrics from each platform
    - Sync availability
    """
    try:
        brand = db.query(Brand).filter(Brand.id == brand_id).first()
        if not brand:
            raise HTTPException(status_code=404, detail=f"Brand with ID {brand_id} not found")
        
        # Get latest metrics
        from models import SocialMetric
        from sqlalchemy import func
        
        latest_metrics = db.query(SocialMetric).filter(
            SocialMetric.brand_id == brand_id
        ).order_by(SocialMetric.recorded_at.desc()).all()
        
        # Group by platform, keeping only the latest for each
        latest_by_platform = {}
        for metric in latest_metrics:
            if metric.platform not in latest_by_platform:
                latest_by_platform[metric.platform] = metric
        
        return {
            "status": "success",
            "brand": {
                "id": brand.id,
                "name": brand.name,
                "tiktok_handle": brand.tiktok_handle,
                "instagram_handle": brand.instagram_handle
            },
            "social_status": {
                "tiktok_configured": brand.tiktok_handle is not None,
                "instagram_configured": brand.instagram_handle is not None
            },
            "latest_metrics": {
                platform: {
                    "followers": m.followers,
                    "following": m.following,
                    "posts": m.posts,
                    "likes": m.likes,
                    "recorded_at": m.recorded_at.isoformat() if m.recorded_at else None
                }
                for platform, m in latest_by_platform.items()
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Brand social status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
