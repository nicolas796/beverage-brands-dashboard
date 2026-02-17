"""
Analytics service for calculating growth metrics and statistics
"""
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func

from models import Brand, SocialMetric, get_db_session


def calculate_growth_rate(current: int, previous: int) -> float:
    """Calculate growth rate as percentage"""
    if not previous or previous == 0:
        return 0.0
    return round(((current - previous) / previous) * 100, 2)


def calculate_engagement_rate(likes: int, comments: int, followers: int) -> float:
    """Calculate engagement rate"""
    if not followers or followers == 0:
        return 0.0
    total_engagement = (likes or 0) + (comments or 0)
    return round((total_engagement / followers) * 100, 2)


def get_brand_growth_summary(db: Session, brand_id: int, days: int = 30) -> Dict:
    """Get comprehensive growth summary for a brand"""
    # Get current and historical metrics
    current = db.query(SocialMetric).filter(
        SocialMetric.brand_id == brand_id
    ).order_by(SocialMetric.recorded_at.desc()).first()
    
    if not current:
        return None
    
    since = datetime.utcnow() - timedelta(days=days)
    
    # Get metrics at the start of the period
    historical = db.query(SocialMetric).filter(
        SocialMetric.brand_id == brand_id,
        SocialMetric.platform == current.platform,
        SocialMetric.recorded_at <= since
    ).order_by(SocialMetric.recorded_at.desc()).first()
    
    # Calculate growth
    if historical and historical.followers:
        growth_pct = calculate_growth_rate(current.followers, historical.followers)
        growth_abs = current.followers - historical.followers
    else:
        growth_pct = 0
        growth_abs = 0
    
    # Get average engagement rate over the period
    avg_engagement = db.query(func.avg(SocialMetric.engagement_rate)).filter(
        SocialMetric.brand_id == brand_id,
        SocialMetric.recorded_at >= since
    ).scalar()
    
    return {
        'brand_id': brand_id,
        'platform': current.platform,
        'current_followers': current.followers,
        'historical_followers': historical.followers if historical else None,
        'growth_absolute': growth_abs,
        'growth_percentage': growth_pct,
        'avg_engagement_rate': round(float(avg_engagement), 2) if avg_engagement else None,
        'posts_count': current.posts,
        'period_days': days
    }


def get_category_growth(db: Session, category: str, days: int = 30) -> Dict:
    """Get average growth metrics for a category"""
    brands = db.query(Brand).filter(Brand.category == category).all()
    
    growth_rates = []
    total_followers = 0
    
    for brand in brands:
        summary = get_brand_growth_summary(db, brand.id, days)
        if summary and summary['growth_percentage'] is not None:
            growth_rates.append(summary['growth_percentage'])
            total_followers += summary['current_followers'] or 0
    
    if not growth_rates:
        return {
            'category': category,
            'brand_count': len(brands),
            'avg_growth': 0,
            'total_followers': 0
        }
    
    return {
        'category': category,
        'brand_count': len(brands),
        'avg_growth': round(sum(growth_rates) / len(growth_rates), 2),
        'total_followers': total_followers,
        'fastest_growing': max(growth_rates),
        'slowest_growing': min(growth_rates)
    }


def get_platform_comparison(db: Session, brand_id: int) -> Dict:
    """Compare metrics across platforms for a brand"""
    platforms = ['instagram', 'tiktok']
    comparison = {}
    
    for platform in platforms:
        latest = db.query(SocialMetric).filter(
            SocialMetric.brand_id == brand_id,
            SocialMetric.platform == platform
        ).order_by(SocialMetric.recorded_at.desc()).first()
        
        if latest:
            comparison[platform] = {
                'followers': latest.followers,
                'posts': latest.posts,
                'engagement_rate': latest.engagement_rate
            }
        else:
            comparison[platform] = None
    
    return comparison


def calculate_momentum_score(db: Session, brand_id: int) -> float:
    """
    Calculate a momentum score based on recent growth trends
    Factors: 7-day growth, 30-day growth, engagement rate consistency
    """
    # Get growth data
    growth_7d = get_brand_growth_summary(db, brand_id, days=7)
    growth_30d = get_brand_growth_summary(db, brand_id, days=30)
    
    if not growth_7d or not growth_30d:
        return 0.0
    
    # Weight recent growth higher
    score = (growth_7d['growth_percentage'] * 0.6) + (growth_30d['growth_percentage'] * 0.4)
    
    # Bonus for engagement rate
    if growth_7d['avg_engagement_rate']:
        score += growth_7d['avg_engagement_rate'] * 0.1
    
    return round(score, 2)


def get_trending_brands(db: Session, limit: int = 10) -> List[Dict]:
    """Get brands with highest momentum scores"""
    brands = db.query(Brand).all()
    
    scored_brands = []
    for brand in brands:
        score = calculate_momentum_score(db, brand.id)
        if score > 0:
            scored_brands.append({
                'brand': brand.to_dict(),
                'momentum_score': score
            })
    
    # Sort by score descending
    scored_brands.sort(key=lambda x: x['momentum_score'], reverse=True)
    
    return scored_brands[:limit]


def forecast_growth(db: Session, brand_id: int, days_ahead: int = 30) -> Dict:
    """
    Simple linear growth forecast based on historical data
    """
    from database import get_growth_data
    
    data = get_growth_data(db, brand_id, 'instagram', days=90)
    
    if len(data) < 7:
        return {
            'brand_id': brand_id,
            'forecast_available': False,
            'reason': 'Insufficient historical data'
        }
    
    # Calculate average daily growth rate
    followers = [d['followers'] for d in data if d['followers']]
    if len(followers) < 2:
        return {
            'brand_id': brand_id,
            'forecast_available': False,
            'reason': 'Insufficient data points'
        }
    
    total_growth = followers[-1] - followers[0]
    avg_daily_growth = total_growth / len(followers)
    
    # Project forward
    current = followers[-1]
    forecasted = current + (avg_daily_growth * days_ahead)
    
    return {
        'brand_id': brand_id,
        'forecast_available': True,
        'current_followers': current,
        'forecasted_followers': int(forecasted),
        'projected_growth': int(forecasted - current),
        'growth_percentage': round(((forecasted - current) / current) * 100, 2) if current else 0,
        'days_ahead': days_ahead,
        'avg_daily_growth': round(avg_daily_growth, 2)
    }


def get_competitive_analysis(db: Session, brand_ids: List[int]) -> Dict:
    """Compare multiple brands across key metrics"""
    from database import get_brand_by_id, get_follower_growth
    
    brands_data = []
    
    for brand_id in brand_ids:
        brand = get_brand_by_id(db, brand_id)
        if not brand:
            continue
        
        growth_7d = get_follower_growth(db, brand_id, 'instagram', 7)
        growth_30d = get_follower_growth(db, brand_id, 'instagram', 30)
        platform_comparison = get_platform_comparison(db, brand_id)
        momentum = calculate_momentum_score(db, brand_id)
        
        brands_data.append({
            'brand': brand.to_dict(),
            'growth_7d': growth_7d,
            'growth_30d': growth_30d,
            'platform_comparison': platform_comparison,
            'momentum_score': momentum
        })
    
    # Calculate rankings
    if brands_data:
        by_followers = sorted(brands_data, 
            key=lambda x: x['growth_7d']['current_followers'] if x['growth_7d'] else 0, 
            reverse=True)
        by_growth = sorted(brands_data, 
            key=lambda x: x['growth_7d']['growth_percentage'] if x['growth_7d'] else 0, 
            reverse=True)
        by_momentum = sorted(brands_data, 
            key=lambda x: x['momentum_score'], 
            reverse=True)
    else:
        by_followers = by_growth = by_momentum = []
    
    return {
        'brands_analyzed': len(brands_data),
        'brands': brands_data,
        'rankings': {
            'by_followers': [b['brand']['name'] for b in by_followers],
            'by_growth_7d': [b['brand']['name'] for b in by_growth],
            'by_momentum': [b['brand']['name'] for b in by_momentum]
        }
    }


def generate_insights(db: Session) -> List[str]:
    """Generate automated insights about the data"""
    insights = []
    
    # Get trending brands
    trending = get_trending_brands(db, limit=5)
    if trending:
        top = trending[0]
        insights.append(f"🚀 {top['brand']['name']} is the hottest brand right now with a momentum score of {top['momentum_score']}")
    
    # Get category insights
    from database import get_categories
    categories = get_categories(db)
    
    category_growth = []
    for cat in categories:
        growth = get_category_growth(db, cat, days=30)
        category_growth.append((cat, growth['avg_growth']))
    
    if category_growth:
        category_growth.sort(key=lambda x: x[1], reverse=True)
        insights.append(f"📈 {category_growth[0][0]} is the fastest growing category with {category_growth[0][1]}% average growth")
    
    # Platform insights
    ig_total = db.query(func.sum(SocialMetric.followers)).filter(
        SocialMetric.platform == 'instagram'
    ).scalar() or 0
    
    tt_total = db.query(func.sum(SocialMetric.followers)).filter(
        SocialMetric.platform == 'tiktok'
    ).scalar() or 0
    
    if ig_total and tt_total:
        ratio = (tt_total / ig_total) * 100
        insights.append(f"📱 TikTok has {ratio:.1f}% as many followers as Instagram across all tracked brands")
    
    return insights


if __name__ == '__main__':
    # Test analytics
    db = get_db_session()
    
    insights = generate_insights(db)
    for insight in insights:
        print(insight)
    
    db.close()
