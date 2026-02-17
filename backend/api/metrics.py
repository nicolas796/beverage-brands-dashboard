from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, timedelta

from database import get_db, get_metrics, get_growth_data, get_follower_growth
from models import SocialMetric

router = APIRouter()


@router.get("/")
async def list_metrics(
    db: Session = Depends(get_db),
    brand_id: Optional[int] = Query(default=None, description='Filter by brand'),
    platform: Optional[str] = Query(default=None, description='Filter by platform'),
    days: int = Query(default=30, ge=1, le=365),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000)
):
    """List social metrics with filtering"""
    metrics = get_metrics(db, brand_id=brand_id, platform=platform, days=days)
    
    # Apply pagination
    paginated = metrics[skip:skip + limit]
    
    return {
        "metrics": [m.to_dict() for m in paginated],
        "total": len(metrics),
        "skip": skip,
        "limit": limit,
        "filters": {
            "brand_id": brand_id,
            "platform": platform,
            "days": days
        }
    }


@router.get("/growth")
async def metrics_growth(
    brand_id: int = Query(..., description='Brand ID'),
    platform: str = Query(default='instagram', description='Platform'),
    days: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Get growth data for a brand"""
    growth_data = get_growth_data(db, brand_id, platform, days)
    
    if not growth_data:
        raise HTTPException(status_code=404, detail="No metrics found for this brand")
    
    return {
        "brand_id": brand_id,
        "platform": platform,
        "days": days,
        "data_points": len(growth_data),
        "data": growth_data
    }


@router.get("/summary")
async def metrics_summary(
    db: Session = Depends(get_db),
    days: int = Query(default=30, ge=1, le=365)
):
    """Get summary statistics for all metrics"""
    from database import get_db_session
    from sqlalchemy import func
    from models import Brand
    
    session = get_db_session()
    
    # Get latest metrics count by platform
    since = datetime.utcnow() - timedelta(days=days)
    
    platform_stats = session.query(
        SocialMetric.platform,
        func.count(SocialMetric.id).label('count'),
        func.avg(SocialMetric.engagement_rate).label('avg_engagement'),
        func.sum(SocialMetric.followers).label('total_followers')
    ).filter(
        SocialMetric.recorded_at >= since
    ).group_by(SocialMetric.platform).all()
    
    # Get total brands with metrics
    brands_with_metrics = session.query(SocialMetric.brand_id).distinct().count()
    
    session.close()
    
    return {
        "period_days": days,
        "brands_with_data": brands_with_metrics,
        "platform_breakdown": [
            {
                "platform": p,
                "metrics_count": c,
                "avg_engagement": round(float(ae), 2) if ae else None,
                "total_followers": int(tf) if tf else 0
            }
            for p, c, ae, tf in platform_stats
        ]
    }


@router.get("/compare")
async def compare_brands(
    brand_ids: List[int] = Query(..., description='Brand IDs to compare'),
    platform: str = Query(default='instagram'),
    metric: str = Query(default='followers', regex='^(followers|engagement_rate|posts)$'),
    days: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Compare metrics across multiple brands"""
    from database import get_brand_by_id
    
    comparison = []
    
    for brand_id in brand_ids:
        brand = get_brand_by_id(db, brand_id)
        if not brand:
            continue
        
        growth_data = get_growth_data(db, brand_id, platform, days)
        
        # Extract just the requested metric
        chart_data = [
            {
                'date': d['date'],
                'value': d.get(metric)
            }
            for d in growth_data if d.get(metric) is not None
        ]
        
        comparison.append({
            'brand': brand.to_dict(),
            'data': chart_data
        })
    
    return {
        "brands_compared": len(comparison),
        "platform": platform,
        "metric": metric,
        "days": days,
        "comparison": comparison
    }


@router.post("/")
async def create_metric(metric_data: dict, db: Session = Depends(get_db)):
    """Create a new metric entry (for manual entry or sync)"""
    from database import create_metric
    
    metric = create_metric(db, metric_data)
    return metric.to_dict()


@router.get("/latest")
async def get_latest_metrics_all(
    db: Session = Depends(get_db),
    platform: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200)
):
    """Get latest metrics for all brands"""
    from sqlalchemy import func
    from database import get_db_session
    
    session = get_db_session()
    
    # Subquery to get latest metric per brand per platform
    subquery = session.query(
        SocialMetric.brand_id,
        SocialMetric.platform,
        func.max(SocialMetric.recorded_at).label('max_date')
    ).group_by(
        SocialMetric.brand_id,
        SocialMetric.platform
    ).subquery()
    
    # Join to get full metric data
    latest = session.query(SocialMetric).join(
        subquery,
        (SocialMetric.brand_id == subquery.c.brand_id) &
        (SocialMetric.platform == subquery.c.platform) &
        (SocialMetric.recorded_at == subquery.c.max_date)
    )
    
    if platform:
        latest = latest.filter(SocialMetric.platform == platform)
    
    latest = latest.limit(limit).all()
    session.close()
    
    return {
        "metrics": [m.to_dict() for m in latest],
        "count": len(latest),
        "platform_filter": platform
    }
