#!/usr/bin/env python3
"""
Initialize database with sample data for development
"""
import os
import sys
from datetime import datetime, timedelta
from random import randint, uniform

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import init_database, Brand, SocialMetric, get_engine, get_session_factory
from database import get_db_session


def create_sample_brands():
    """Create sample beverage brands"""
    brands_data = [
        {
            'name': 'Poppi',
            'category': 'Prebiotic Soda',
            'hq_city': 'Austin',
            'hq_state': 'TX',
            'country': 'USA',
            'website': 'https://drinkpoppi.com',
            'instagram_handle': 'drinkpoppi',
            'tiktok_handle': 'drinkpoppi',
            'founders': 'Allison Ellsworth, Stephen Ellsworth',
            'founded_year': 2015,
            'revenue': '~$100M+',
            'funding': '$25M Series B',
            'parent_company': 'Independent',
            'notes': 'Appeared on Shark Tank 2018'
        },
        {
            'name': 'OLIPOP',
            'category': 'Prebiotic Soda',
            'hq_city': 'Oakland',
            'hq_state': 'CA',
            'country': 'USA',
            'website': 'https://drinkolipop.com',
            'instagram_handle': 'drinkolipop',
            'tiktok_handle': 'drinkolipop',
            'founders': 'Ben Goodwin, David Lester',
            'founded_year': 2017,
            'revenue': '~$200M+',
            'funding': '$50M+ raised',
            'parent_company': 'Independent',
            'notes': 'Scientific advisory board focused on gut health'
        },
        {
            'name': 'Celsius',
            'category': 'Energy Drink',
            'hq_city': 'Boca Raton',
            'hq_state': 'FL',
            'country': 'USA',
            'website': 'https://www.celsius.com',
            'instagram_handle': 'celsiusofficial',
            'tiktok_handle': 'celsiusofficial',
            'founders': 'Steve Haley',
            'founded_year': 2004,
            'revenue': '$1.2B+',
            'funding': 'Public (NASDAQ: CELH)',
            'parent_company': 'Independent',
            'notes': 'PepsiCo distribution partnership'
        },
        {
            'name': 'Liquid Death',
            'category': 'Mountain Water',
            'hq_city': 'Los Angeles',
            'hq_state': 'CA',
            'country': 'USA',
            'website': 'https://liquiddeath.com',
            'instagram_handle': 'liquiddeath',
            'tiktok_handle': 'liquiddeath',
            'founders': 'Mike Cessario',
            'founded_year': 2019,
            'revenue': '$130M+',
            'funding': '$195M+ raised',
            'parent_company': 'Independent',
            'notes': 'Heavy metal branding, strong community'
        },
        {
            'name': 'Ghost Energy',
            'category': 'Energy Drink',
            'hq_city': 'Chicago',
            'hq_state': 'IL',
            'country': 'USA',
            'website': 'https://drinkghost.com',
            'instagram_handle': 'ghostenergy',
            'tiktok_handle': 'ghostenergy',
            'founders': 'Daniel Lourenco, Ryan Hughes',
            'founded_year': 2016,
            'revenue': '$100M+',
            'funding': 'Independent',
            'parent_company': 'Independent',
            'notes': 'Transparent labeling, gaming/esports focus'
        },
        {
            'name': 'Prime Hydration',
            'category': 'Sports Drink',
            'hq_city': 'Louisville',
            'hq_state': 'KY',
            'country': 'USA',
            'website': 'https://drinkprime.com',
            'instagram_handle': 'drinkprime',
            'tiktok_handle': 'drinkprime',
            'founders': 'Logan Paul, KSI, Max Clemons, Trey Steiger',
            'founded_year': 2022,
            'revenue': '$250M+',
            'funding': 'Independent',
            'parent_company': 'Independent',
            'notes': 'YouTube creator-led brand'
        },
        {
            'name': 'Alani Nu',
            'category': 'Energy Drink',
            'hq_city': 'Louisville',
            'hq_state': 'KY',
            'country': 'USA',
            'website': 'https://alaninu.com',
            'instagram_handle': 'alanienergy',
            'tiktok_handle': 'alaninu',
            'founders': 'Katy Hearn, Haydn Schneider',
            'founded_year': 2018,
            'revenue': '$100M+',
            'funding': 'Independent',
            'parent_company': 'Independent',
            'notes': 'Female-focused fitness brand'
        },
        {
            'name': 'Health-Ade',
            'category': 'Kombucha',
            'hq_city': 'Torrance',
            'hq_state': 'CA',
            'country': 'USA',
            'website': 'https://health-ade.com',
            'instagram_handle': 'healthade',
            'tiktok_handle': 'healthade',
            'founders': 'Daina Trout, Justin Trout, Vanessa Dew',
            'founded_year': 2012,
            'revenue': '$100M+',
            'funding': '$20M+ raised',
            'parent_company': 'Independent',
            'notes': 'Fastest-growing kombucha'
        },
        {
            'name': 'Spindrift',
            'category': 'Sparkling Water',
            'hq_city': 'Newton',
            'hq_state': 'MA',
            'country': 'USA',
            'website': 'https://spindriftfresh.com',
            'instagram_handle': 'spindriftfresh',
            'tiktok_handle': 'spindrift',
            'founders': 'Bill Creelman',
            'founded_year': 2010,
            'revenue': '$100M+',
            'funding': '$50M+ raised',
            'parent_company': 'Independent',
            'notes': 'Real squeezed fruit, no natural flavors'
        },
        {
            'name': 'Super Coffee',
            'category': 'Keto Coffee',
            'hq_city': 'Philadelphia',
            'hq_state': 'PA',
            'country': 'USA',
            'website': 'https://drinksupercoffee.com',
            'instagram_handle': 'drinksupercoffee',
            'tiktok_handle': 'drinksupercoffee',
            'founders': 'Jimmy DeCicco, Jake DeCicco, Jordan DeCicco',
            'founded_year': 2016,
            'revenue': '$50M+',
            'funding': '$70M+ raised',
            'parent_company': 'Independent',
            'notes': 'Shark Tank deal, three brothers'
        },
        {
            'name': 'BioSteel',
            'category': 'Sports Drink',
            'hq_city': 'Toronto',
            'hq_state': 'ON',
            'country': 'Canada',
            'website': 'https://biosteelsports.com',
            'instagram_handle': 'biosteelsports',
            'tiktok_handle': 'biosteelsports',
            'founders': 'Unknown',
            'founded_year': 2009,
            'revenue': 'Unknown',
            'funding': 'Independent',
            'parent_company': 'Independent',
            'notes': 'Hockey-focused, NHL partnerships'
        },
        {
            'name': 'Flow Alkaline',
            'category': 'Alkaline Water',
            'hq_city': 'Ontario',
            'hq_state': 'ON',
            'country': 'Canada',
            'website': 'https://flow.com',
            'instagram_handle': 'flow',
            'tiktok_handle': 'flow',
            'founders': 'Unknown',
            'founded_year': 2015,
            'revenue': 'Unknown',
            'funding': 'Independent',
            'parent_company': 'Independent',
            'notes': 'Carton packaging, B Corp'
        }
    ]
    
    return brands_data


def create_sample_metrics(db, brands, days=90):
    """Create sample metrics for brands"""
    base_followers = {
        'Poppi': 850000,
        'OLIPOP': 720000,
        'Celsius': 1250000,
        'Liquid Death': 2100000,
        'Ghost Energy': 950000,
        'Prime Hydration': 3200000,
        'Alani Nu': 1100000,
        'Health-Ade': 580000,
        'Spindrift': 420000,
        'Super Coffee': 380000,
        'BioSteel': 290000,
        'Flow Alkaline': 210000
    }
    
    metrics_data = []
    
    for brand in brands:
        base = base_followers.get(brand.name, 500000)
        
        for i in range(days):
            date = datetime.utcnow() - timedelta(days=days-i)
            
            # Add some realistic growth
            growth_rate = uniform(0.001, 0.015)  # 0.1% to 1.5% daily growth
            followers = int(base * (1 + growth_rate) ** i)
            
            # Create Instagram metrics
            metric = SocialMetric(
                brand_id=brand.id,
                platform='instagram',
                followers=followers,
                following=randint(500, 5000),
                posts=randint(500, 5000),
                likes=randint(followers//10, followers//3),
                engagement_rate=round(uniform(1.5, 8.5), 2),
                recorded_at=date
            )
            metrics_data.append(metric)
            
            # Create TikTok metrics (usually fewer followers)
            tiktok_followers = int(followers * uniform(0.3, 1.2))
            metric_tiktok = SocialMetric(
                brand_id=brand.id,
                platform='tiktok',
                followers=tiktok_followers,
                following=randint(100, 2000),
                posts=randint(100, 2000),
                views=randint(tiktok_followers, tiktok_followers * 5),
                engagement_rate=round(uniform(3.0, 15.0), 2),
                recorded_at=date
            )
            metrics_data.append(metric_tiktok)
    
    db.add_all(metrics_data)
    db.commit()
    print(f"Created {len(metrics_data)} sample metrics")


def init_sample_data():
    """Initialize database with sample data"""
    print("Initializing database...")
    init_database()
    
    db = get_db_session()
    
    try:
        # Check if data already exists
        existing = db.query(Brand).first()
        if existing:
            print("Database already has data, skipping sample data creation")
            return
        
        print("Creating sample brands...")
        brands_data = create_sample_brands()
        brands = []
        
        for brand_data in brands_data:
            brand = Brand(**brand_data)
            db.add(brand)
            db.flush()  # Get the ID
            brands.append(brand)
        
        db.commit()
        print(f"Created {len(brands)} sample brands")
        
        print("Creating sample metrics...")
        create_sample_metrics(db, brands)
        
        print("Database initialized successfully!")
        
    except Exception as e:
        print(f"Error initializing database: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == '__main__':
    init_sample_data()
