from sqlalchemy.orm import Session
from models import get_engine, get_session_factory, Brand, SocialMetric, SyncLog
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Optional
import csv
import io

# Database utilities

def get_db():
    """Get database session generator"""
    SessionLocal = get_session_factory()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_session():
    """Get a database session"""
    SessionLocal = get_session_factory()
    return SessionLocal()


# Brand operations

def get_brands(db: Session, skip: int = 0, limit: int = 100, 
               category: Optional[str] = None, search: Optional[str] = None):
    """Get brands with optional filtering"""
    query = db.query(Brand)
    
    if category:
        query = query.filter(Brand.category == category)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Brand.name.ilike(search_term)) |
            (Brand.founders.ilike(search_term)) |
            (Brand.hq_city.ilike(search_term)) |
            (Brand.hq_state.ilike(search_term))
        )
    
    return query.offset(skip).limit(limit).all()


def get_brand_by_id(db: Session, brand_id: int):
    """Get brand by ID"""
    return db.query(Brand).filter(Brand.id == brand_id).first()


def get_brand_by_name(db: Session, name: str):
    """Get brand by name"""
    return db.query(Brand).filter(Brand.name.ilike(name)).first()


def create_brand(db: Session, brand_data: dict):
    """Create a new brand"""
    brand = Brand(**brand_data)
    db.add(brand)
    db.commit()
    db.refresh(brand)
    return brand


def update_brand(db: Session, brand_id: int, brand_data: dict):
    """Update a brand"""
    brand = get_brand_by_id(db, brand_id)
    if brand:
        for key, value in brand_data.items():
            setattr(brand, key, value)
        brand.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(brand)
    return brand


def delete_brand(db: Session, brand_id: int):
    """Delete a brand"""
    brand = get_brand_by_id(db, brand_id)
    if brand:
        db.delete(brand)
        db.commit()
        return True
    return False


def get_categories(db: Session):
    """Get all unique categories"""
    return [cat[0] for cat in db.query(Brand.category).distinct().all() if cat[0]]


# Social Metric operations

def get_metrics(db: Session, brand_id: Optional[int] = None, 
                platform: Optional[str] = None, 
                days: int = 30):
    """Get social metrics with filtering"""
    query = db.query(SocialMetric)
    
    if brand_id:
        query = query.filter(SocialMetric.brand_id == brand_id)
    
    if platform:
        query = query.filter(SocialMetric.platform == platform)
    
    since = datetime.utcnow() - timedelta(days=days)
    query = query.filter(SocialMetric.recorded_at >= since)
    
    return query.order_by(SocialMetric.recorded_at.desc()).all()


def get_latest_metrics(db: Session, brand_id: int, platform: Optional[str] = None):
    """Get latest metrics for a brand"""
    query = db.query(SocialMetric).filter(SocialMetric.brand_id == brand_id)
    
    if platform:
        query = query.filter(SocialMetric.platform == platform)
    
    return query.order_by(SocialMetric.recorded_at.desc()).first()


def create_metric(db: Session, metric_data: dict):
    """Create a new social metric"""
    metric = SocialMetric(**metric_data)
    db.add(metric)
    db.commit()
    db.refresh(metric)
    return metric


def create_metrics_bulk(db: Session, metrics_data: List[dict]):
    """Create multiple metrics at once"""
    metrics = [SocialMetric(**data) for data in metrics_data]
    db.add_all(metrics)
    db.commit()
    return metrics


# Growth calculations

def get_growth_data(db: Session, brand_id: int, platform: str, days: int = 30):
    """Get follower growth data for charts"""
    since = datetime.utcnow() - timedelta(days=days)
    
    metrics = db.query(SocialMetric).filter(
        SocialMetric.brand_id == brand_id,
        SocialMetric.platform == platform,
        SocialMetric.recorded_at >= since
    ).order_by(SocialMetric.recorded_at.asc()).all()
    
    return [
        {
            'date': m.recorded_at.strftime('%Y-%m-%d'),
            'followers': m.followers,
            'posts': m.posts,
            'engagement_rate': m.engagement_rate
        }
        for m in metrics if m.followers is not None
    ]


def get_follower_growth(db: Session, brand_id: int, platform: str, days: int = 7):
    """Calculate follower growth over a period"""
    current = get_latest_metrics(db, brand_id, platform)
    
    if not current or not current.followers:
        return None
    
    since = datetime.utcnow() - timedelta(days=days)
    past_metric = db.query(SocialMetric).filter(
        SocialMetric.brand_id == brand_id,
        SocialMetric.platform == platform,
        SocialMetric.recorded_at <= since
    ).order_by(SocialMetric.recorded_at.desc()).first()
    
    if not past_metric or not past_metric.followers:
        return {
            'current_followers': current.followers,
            'growth_absolute': 0,
            'growth_percentage': 0.0
        }
    
    growth = current.followers - past_metric.followers
    growth_pct = (growth / past_metric.followers) * 100 if past_metric.followers else 0
    
    return {
        'current_followers': current.followers,
        'previous_followers': past_metric.followers,
        'growth_absolute': growth,
        'growth_percentage': round(growth_pct, 2)
    }


# Rankings

def get_top_growing_brands(db: Session, platform: str = 'instagram', 
                           days: int = 7, limit: int = 20):
    """Get top growing brands by follower growth"""
    brands = db.query(Brand).all()
    rankings = []
    
    for brand in brands:
        growth = get_follower_growth(db, brand.id, platform, days)
        if growth and growth['growth_percentage'] != 0:
            rankings.append({
                'brand': brand.to_dict(),
                'growth': growth
            })
    
    # Sort by growth percentage descending
    rankings.sort(key=lambda x: x['growth']['growth_percentage'], reverse=True)
    return rankings[:limit]


def get_brand_rankings(db: Session, platform: str = 'instagram', 
                       days: int = 7, skip: int = 0, limit: int = 50):
    """Get full rankings with pagination"""
    all_rankings = get_top_growing_brands(db, platform, days, limit=1000)
    return all_rankings[skip:skip + limit]


# Sync log operations

def create_sync_log(db: Session, source: str):
    """Create a new sync log entry"""
    log = SyncLog(source=source, status='running')
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def update_sync_log(db: Session, log_id: int, **kwargs):
    """Update sync log"""
    log = db.query(SyncLog).filter(SyncLog.id == log_id).first()
    if log:
        for key, value in kwargs.items():
            setattr(log, key, value)
        if kwargs.get('status') in ['success', 'error']:
            log.completed_at = datetime.utcnow()
        db.commit()
        db.refresh(log)
    return log


def get_recent_syncs(db: Session, limit: int = 10):
    """Get recent sync logs"""
    return db.query(SyncLog).order_by(SyncLog.started_at.desc()).limit(limit).all()


# Import/Export

def export_brands_to_csv(db: Session):
    """Export brands to CSV string"""
    brands = db.query(Brand).all()
    
    if not brands:
        return ""
    
    output = io.StringIO()
    fieldnames = ['id', 'name', 'category', 'hq_city', 'hq_state', 'country',
                  'website', 'instagram_handle', 'tiktok_handle', 'founders',
                  'founded_year', 'revenue', 'funding', 'parent_company', 'notes']
    
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    
    for brand in brands:
        writer.writerow(brand.to_dict())
    
    return output.getvalue()


def export_metrics_to_csv(db: Session, brand_id: Optional[int] = None):
    """Export metrics to CSV string"""
    query = db.query(SocialMetric)
    if brand_id:
        query = query.filter(SocialMetric.brand_id == brand_id)
    
    metrics = query.all()
    
    if not metrics:
        return ""
    
    output = io.StringIO()
    fieldnames = ['id', 'brand_id', 'platform', 'followers', 'following', 
                  'posts', 'likes', 'comments', 'shares', 'views', 
                  'engagement_rate', 'recorded_at']
    
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    
    for metric in metrics:
        writer.writerow(metric.to_dict())
    
    return output.getvalue()


def import_brands_from_csv(db: Session, csv_content: str):
    """Import brands from CSV content"""
    reader = csv.DictReader(io.StringIO(csv_content))
    brands = []
    
    for row in reader:
        # Convert numeric fields
        if 'founded_year' in row and row['founded_year']:
            try:
                row['founded_year'] = int(row['founded_year'])
            except ValueError:
                row['founded_year'] = None
        
        brand = create_brand(db, row)
        brands.append(brand)
    
    return brands
