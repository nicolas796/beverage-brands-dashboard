from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from database import get_db, get_brands, get_brand_by_id, get_brand_by_name, create_brand, update_brand, delete_brand, get_metrics, get_growth_data
from services.research_scheduler import ResearchScheduler
from services.credits_tracker import CreditsTracker

router = APIRouter()


class WebsiteResearchRequest(BaseModel):
    website_url: str


class PendingBrandResponse(BaseModel):
    id: int
    name: str
    website: Optional[str]
    instagram_handle: Optional[str]
    tiktok_handle: Optional[str]
    category: Optional[str]
    location: Optional[str]
    confidence_score: Optional[float]
    status: str
    discovered_at: str
    
    class Config:
        from_attributes = True


@router.get("/")
async def list_brands(
    db: Session = Depends(get_db),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    category: Optional[str] = None,
    search: Optional[str] = None
):
    """List all brands with optional filtering"""
    brands = get_brands(db, skip=skip, limit=limit, category=category, search=search)
    return {
        "brands": [b.to_dict() for b in brands],
        "total": len(brands),
        "skip": skip,
        "limit": limit
    }


@router.get("/search")
async def search_brands(
    q: str = Query(..., min_length=1, description="Search query"),
    db: Session = Depends(get_db)
):
    """Search brands by name, founders, or location"""
    brands = get_brands(db, search=q, limit=50)
    return {
        "query": q,
        "results": [b.to_dict() for b in brands],
        "count": len(brands)
    }


@router.get("/{brand_id}")
async def get_brand(brand_id: int, db: Session = Depends(get_db)):
    """Get brand by ID"""
    brand = get_brand_by_id(db, brand_id)
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    return brand.to_dict()


@router.get("/{brand_id}/full")
async def get_brand_full(brand_id: int, db: Session = Depends(get_db)):
    """Get brand with latest metrics"""
    brand = get_brand_by_id(db, brand_id)
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    from database import get_latest_metrics
    
    ig_metrics = get_latest_metrics(db, brand_id, 'instagram')
    tt_metrics = get_latest_metrics(db, brand_id, 'tiktok')
    
    brand_dict = brand.to_dict()
    brand_dict['latest_metrics'] = {
        'instagram': ig_metrics.to_dict() if ig_metrics else None,
        'tiktok': tt_metrics.to_dict() if tt_metrics else None
    }
    
    return brand_dict


@router.get("/{brand_id}/metrics")
async def get_brand_metrics(
    brand_id: int,
    platform: Optional[str] = Query(default=None, description="Filter by platform"),
    days: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Get metrics history for a brand"""
    brand = get_brand_by_id(db, brand_id)
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    metrics = get_metrics(db, brand_id=brand_id, platform=platform, days=days)
    
    return {
        "brand_id": brand_id,
        "platform": platform,
        "days": days,
        "metrics_count": len(metrics),
        "metrics": [m.to_dict() for m in metrics]
    }


@router.get("/{brand_id}/growth")
async def get_brand_growth(
    brand_id: int,
    platform: str = Query(default='instagram', description='Platform'),
    days: int = Query(default=30, ge=1, le=365, description='Days to look back'),
    db: Session = Depends(get_db)
):
    """Get growth data for charts"""
    brand = get_brand_by_id(db, brand_id)
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    growth_data = get_growth_data(db, brand_id, platform, days)
    
    return {
        "brand_id": brand_id,
        "brand_name": brand.name,
        "platform": platform,
        "days": days,
        "data_points": len(growth_data),
        "data": growth_data
    }


@router.post("/")
async def create_new_brand(brand_data: dict, db: Session = Depends(get_db)):
    """Create a new brand"""
    # Check if brand with same name exists
    existing = get_brand_by_name(db, brand_data.get('name', ''))
    if existing:
        raise HTTPException(status_code=400, detail="Brand with this name already exists")
    
    brand = create_brand(db, brand_data)
    return brand.to_dict()


@router.put("/{brand_id}")
async def update_existing_brand(brand_id: int, brand_data: dict, db: Session = Depends(get_db)):
    """Update a brand"""
    brand = update_brand(db, brand_id, brand_data)
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    return brand.to_dict()


@router.delete("/{brand_id}")
async def delete_existing_brand(brand_id: int, db: Session = Depends(get_db)):
    """Delete a brand"""
    success = delete_brand(db, brand_id)
    if not success:
        raise HTTPException(status_code=404, detail="Brand not found")
    return {"message": "Brand deleted successfully"}


# ===== Research Endpoints =====

@router.post("/research/website")
async def research_website(
    request: WebsiteResearchRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Research a brand from its website URL.
    Extracts brand name, social handles, category, and location.
    """
    scheduler = ResearchScheduler(db)
    try:
        result = scheduler.research_brand_from_website(request.website_url)
        
        if result.success:
            return {
                "success": True,
                "brand_name": result.brand_name,
                "data": result.data,
                "message": f"Successfully researched and added {result.brand_name}"
            }
        else:
            raise HTTPException(status_code=400, detail=result.error_message)
    finally:
        scheduler.close()


@router.get("/research/pending", response_model=List[PendingBrandResponse])
async def get_pending_brands(
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get pending brands awaiting approval."""
    scheduler = ResearchScheduler(db)
    try:
        pending = scheduler.get_pending_brands(status)
        return pending
    finally:
        scheduler.close()


@router.post("/research/pending/{pending_id}/approve")
async def approve_pending_brand(pending_id: int, db: Session = Depends(get_db)):
    """Approve a pending brand and add it to the main database."""
    scheduler = ResearchScheduler(db)
    try:
        brand = scheduler.approve_pending_brand(pending_id)
        if not brand:
            raise HTTPException(status_code=404, detail="Pending brand not found")
        return {
            "success": True,
            "brand": brand.to_dict(),
            "message": f"Brand '{brand.name}' approved and added to database"
        }
    finally:
        scheduler.close()


@router.post("/research/pending/{pending_id}/reject")
async def reject_pending_brand(pending_id: int, db: Session = Depends(get_db)):
    """Reject a pending brand."""
    scheduler = ResearchScheduler(db)
    try:
        success = scheduler.reject_pending_brand(pending_id)
        if not success:
            raise HTTPException(status_code=404, detail="Pending brand not found")
        return {
            "success": True,
            "message": "Brand rejected"
        }
    finally:
        scheduler.close()


@router.get("/research/updates")
async def get_update_logs(
    brand_id: Optional[int] = None,
    days: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Get update logs for brand changes."""
    scheduler = ResearchScheduler(db)
    try:
        logs = scheduler.get_update_logs(brand_id, days)
        return {
            "logs": logs,
            "count": len(logs),
            "days": days
        }
    finally:
        scheduler.close()
