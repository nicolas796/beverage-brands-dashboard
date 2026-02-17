from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Text, BigInteger, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import json
import os

Base = declarative_base()

class Brand(Base):
    __tablename__ = 'brands'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    category = Column(String(100), nullable=False, index=True)
    
    # Location
    hq_city = Column(String(100))
    hq_state = Column(String(50))
    country = Column(String(50))
    
    # Online presence
    website = Column(String(500))
    instagram_handle = Column(String(100))
    tiktok_handle = Column(String(100))
    
    # Company info
    founders = Column(String(500))
    founded_year = Column(Integer)
    revenue = Column(String(100))
    funding = Column(String(100))
    parent_company = Column(String(200))
    notes = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    metrics = relationship("SocialMetric", back_populates="brand", cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category,
            'hq_city': self.hq_city,
            'hq_state': self.hq_state,
            'country': self.country,
            'website': self.website,
            'instagram_handle': self.instagram_handle,
            'tiktok_handle': self.tiktok_handle,
            'founders': self.founders,
            'founded_year': self.founded_year,
            'revenue': self.revenue,
            'funding': self.funding,
            'parent_company': self.parent_company,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class SocialMetric(Base):
    __tablename__ = 'social_metrics'
    
    id = Column(Integer, primary_key=True, index=True)
    brand_id = Column(Integer, ForeignKey('brands.id'), nullable=False, index=True)
    
    # Platform
    platform = Column(String(50), nullable=False, index=True)  # instagram, tiktok, twitter, etc.
    
    # Metrics
    followers = Column(BigInteger)
    following = Column(Integer)
    posts = Column(Integer)
    likes = Column(BigInteger)
    comments = Column(BigInteger)
    shares = Column(BigInteger)
    views = Column(BigInteger)
    engagement_rate = Column(Float)
    
    # Metadata
    recorded_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    brand = relationship("Brand", back_populates="metrics")
    
    def to_dict(self):
        return {
            'id': self.id,
            'brand_id': self.brand_id,
            'platform': self.platform,
            'followers': self.followers,
            'following': self.following,
            'posts': self.posts,
            'likes': self.likes,
            'comments': self.comments,
            'shares': self.shares,
            'views': self.views,
            'engagement_rate': self.engagement_rate,
            'recorded_at': self.recorded_at.isoformat() if self.recorded_at else None,
        }


class SyncLog(Base):
    __tablename__ = 'sync_logs'
    
    id = Column(Integer, primary_key=True)
    source = Column(String(50))  # google_sheets, manual, api
    status = Column(String(20))  # success, error, partial
    records_processed = Column(Integer)
    records_inserted = Column(Integer)
    records_updated = Column(Integer)
    error_message = Column(Text)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    
    def to_dict(self):
        return {
            'id': self.id,
            'source': self.source,
            'status': self.status,
            'records_processed': self.records_processed,
            'records_inserted': self.records_inserted,
            'records_updated': self.records_updated,
            'error_message': self.error_message,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
        }


class CreditUsage(Base):
    """Tracks API usage and costs."""
    __tablename__ = 'credit_usage'
    
    id = Column(Integer, primary_key=True)
    operation_type = Column(String(50), nullable=False, index=True)
    description = Column(Text)
    cost_usd = Column(Float, nullable=False)
    metadata_json = Column(Text)  # JSON string for additional metadata
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'operation_type': self.operation_type,
            'description': self.description,
            'cost_usd': self.cost_usd,
            'metadata': json.loads(self.metadata_json) if self.metadata_json else {},
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class PendingBrand(Base):
    """New brands discovered pending approval."""
    __tablename__ = 'pending_brands'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    website = Column(String(500))
    instagram_handle = Column(String(100))
    tiktok_handle = Column(String(100))
    category = Column(String(100))
    location = Column(String(200))
    confidence_score = Column(Float)
    discovered_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20), default='pending')  # pending, approved, rejected
    source = Column(String(100))  # 'discovery', 'manual', etc.
    metadata_json = Column(Text)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'website': self.website,
            'instagram_handle': self.instagram_handle,
            'tiktok_handle': self.tiktok_handle,
            'category': self.category,
            'location': self.location,
            'confidence_score': self.confidence_score,
            'discovered_at': self.discovered_at.isoformat() if self.discovered_at else None,
            'status': self.status,
            'source': self.source,
            'metadata': json.loads(self.metadata_json) if self.metadata_json else {},
        }


class UpdateLog(Base):
    """Logs changes to brand information."""
    __tablename__ = 'update_logs'
    
    id = Column(Integer, primary_key=True)
    brand_id = Column(Integer, nullable=False, index=True)
    brand_name = Column(String(255), nullable=False)
    field_changed = Column(String(100), nullable=False)
    old_value = Column(Text)
    new_value = Column(Text)
    update_type = Column(String(50))  # 'monthly_update', 'immediate', 'discovery'
    updated_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'brand_id': self.brand_id,
            'brand_name': self.brand_name,
            'field_changed': self.field_changed,
            'old_value': self.old_value,
            'new_value': self.new_value,
            'update_type': self.update_type,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


# Database connection
def get_database_url():
    """Get database URL from environment or default to SQLite"""
    db_url = os.getenv('DATABASE_URL')
    if db_url:
        # Handle Render's postgres:// format
        if db_url.startswith('postgres://'):
            db_url = db_url.replace('postgres://', 'postgresql://', 1)
        return db_url
    return 'sqlite:///./beverage_brands.db'


def get_engine():
    """Create database engine"""
    db_url = get_database_url()
    
    if db_url.startswith('sqlite'):
        return create_engine(db_url, connect_args={"check_same_thread": False})
    else:
        return create_engine(db_url)


def get_session_factory():
    """Get session factory"""
    engine = get_engine()
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db_session():
    """Get a database session"""
    SessionLocal = get_session_factory()
    return SessionLocal()


def init_database():
    """Initialize database tables"""
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    print(f"Database initialized at {get_database_url()}")


if __name__ == '__main__':
    init_database()
