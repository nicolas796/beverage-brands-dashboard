from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from database import get_db, get_top_growing_brands, get_brand_rankings, get_follower_growth

router = APIRouter()


@router.get("/")
async def get_rankings(
    db: Session = Depends(get_db),
    period: str = Query(default='7d', regex='^(7d|30d|90d)$', description='Time period'),
    platform: str = Query(default='instagram', description='Social platform'),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200)
):
    """Get brand rankings by follower growth"""
    days_map = {'7d': 7, '30d': 30, '90d': 90}
    days = days_map.get(period, 7)
    
    rankings = get_brand_rankings(db, platform=platform, days=days, skip=skip, limit=limit)
    
    return {
        "period": period,
        "days": days,
        "platform": platform,
        "rankings": rankings,
        "count": len(rankings)
    }


@router.get("/top")
async def get_top_brands(
    db: Session = Depends(get_db),
    period: str = Query(default='7d', regex='^(7d|30d|90d)$'),
    platform: str = Query(default='instagram'),
    limit: int = Query(default=10, ge=1, le=50)
):
    """Get top growing brands (simplified)"""
    days_map = {'7d': 7, '30d': 30, '90d': 90}
    days = days_map.get(period, 7)
    
    rankings = get_top_growing_brands(db, platform=platform, days=days, limit=limit)
    
    return {
        "period": period,
        "platform": platform,
        "top_brands": rankings
    }


@router.get("/by-category")
async def get_rankings_by_category(
    db: Session = Depends(get_db),
    category: str = Query(..., description='Brand category'),
    period: str = Query(default='7d', regex='^(7d|30d|90d)$'),
    platform: str = Query(default='instagram')
):
    """Get rankings filtered by category"""
    days_map = {'7d': 7, '30d': 30, '90d': 90}
    days = days_map.get(period, 7)
    
    # Get all rankings and filter by category
    all_rankings = get_top_growing_brands(db, platform=platform, days=days, limit=1000)
    filtered = [r for r in all_rankings if r['brand']['category'] == category]
    
    return {
        "category": category,
        "period": period,
        "platform": platform,
        "rankings": filtered,
        "count": len(filtered)
    }


@router.get("/brand/{brand_id}")
async def get_brand_ranking_position(
    brand_id: int,
    db: Session = Depends(get_db),
    period: str = Query(default='7d', regex='^(7d|30d|90d)$'),
    platform: str = Query(default='instagram')
):
    """Get a specific brand's ranking position"""
    days_map = {'7d': 7, '30d': 30, '90d': 90}
    days = days_map.get(period, 7)
    
    # Get brand
    from database import get_brand_by_id
    brand = get_brand_by_id(db, brand_id)
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    # Get growth
    growth = get_follower_growth(db, brand_id, platform, days)
    
    # Get all rankings to find position
    all_rankings = get_top_growing_brands(db, platform=platform, days=days, limit=1000)
    
    position = None
    for idx, ranking in enumerate(all_rankings):
        if ranking['brand']['id'] == brand_id:
            position = idx + 1
            break
    
    return {
        "brand": brand.to_dict(),
        "period": period,
        "platform": platform,
        "position": position,
        "total_ranked": len(all_rankings),
        "growth": growth
    }
