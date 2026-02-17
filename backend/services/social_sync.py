"""
Social Media Sync Service
Syncs TikTok and Instagram metrics for all brands in the database
"""
import os
import json
import logging
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from sqlalchemy.orm import Session

# Import API clients
from services.tiktok_api import TikTokAPI, TikTokAPIError, get_tiktok_user
from services.instagram_api import InstagramAPI, InstagramAPIError, get_instagram_user
from models import get_db_session, Brand, SocialMetric, SyncLog
from database import create_metric, create_sync_log, update_sync_log

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Sync configuration
SYNC_DELAY_BETWEEN_REQUESTS = float(os.getenv('SYNC_DELAY', '2'))  # seconds between API calls
BATCH_SIZE = int(os.getenv('SYNC_BATCH_SIZE', '10'))  # brands per batch


@dataclass
class SyncResult:
    """Result of a single brand sync"""
    brand_id: int
    brand_name: str
    tiktok_success: bool
    instagram_success: bool
    tiktok_error: Optional[str] = None
    instagram_error: Optional[str] = None
    tiktok_followers: Optional[int] = None
    instagram_followers: Optional[int] = None


@dataclass
class SyncSummary:
    """Summary of full sync operation"""
    sync_id: int
    started_at: datetime
    completed_at: Optional[datetime]
    total_brands: int
    tiktok_success: int
    instagram_success: int
    errors: int
    results: List[SyncResult]


class SocialSyncService:
    """Service for syncing social media metrics"""
    
    def __init__(self, db_session: Optional[Session] = None):
        self.db = db_session or get_db_session()
        self.tiktok_api = TikTokAPI()
        self.instagram_api = InstagramAPI()
        self.delay = SYNC_DELAY_BETWEEN_REQUESTS
        
    def __del__(self):
        """Cleanup database session"""
        if hasattr(self, 'db') and self.db:
            self.db.close()
    
    def get_brands_to_sync(self) -> List[Brand]:
        """
        Get all brands that have social media handles
        
        Returns:
            List of Brand objects with at least one social handle
        """
        brands = self.db.query(Brand).all()
        
        # Filter to only brands with social handles
        brands_with_handles = [
            b for b in brands 
            if b.tiktok_handle or b.instagram_handle
        ]
        
        logger.info(f"Found {len(brands_with_handles)} brands with social media handles")
        return brands_with_handles
    
    def sync_brand(self, brand: Brand) -> SyncResult:
        """
        Sync a single brand's social media metrics
        
        Args:
            brand: Brand object to sync
            
        Returns:
            SyncResult with sync status
        """
        result = SyncResult(
            brand_id=brand.id,
            brand_name=brand.name,
            tiktok_success=False,
            instagram_success=False
        )
        
        # Sync TikTok if handle exists
        if brand.tiktok_handle:
            try:
                logger.info(f"Syncing TikTok for {brand.name}: @{brand.tiktok_handle}")
                
                # Fetch from API
                tiktok_data = get_tiktok_user(brand.tiktok_handle)
                
                if tiktok_data.get('success'):
                    # Save to database
                    metric = create_metric(self.db, {
                        'brand_id': brand.id,
                        'platform': 'tiktok',
                        'followers': tiktok_data.get('followers'),
                        'following': tiktok_data.get('following'),
                        'posts': tiktok_data.get('video_count'),
                        'likes': tiktok_data.get('likes'),
                        'recorded_at': datetime.utcnow()
                    })
                    
                    result.tiktok_success = True
                    result.tiktok_followers = tiktok_data.get('followers')
                    logger.info(f"✓ TikTok synced for {brand.name}: {result.tiktok_followers:,} followers")
                else:
                    result.tiktok_error = tiktok_data.get('error', 'Unknown error')
                    logger.warning(f"✗ TikTok failed for {brand.name}: {result.tiktok_error}")
                
                # Respect rate limits
                time.sleep(self.delay)
                
            except Exception as e:
                result.tiktok_error = str(e)
                logger.error(f"✗ TikTok exception for {brand.name}: {e}")
        
        # Sync Instagram if handle exists
        if brand.instagram_handle:
            try:
                logger.info(f"Syncing Instagram for {brand.name}: @{brand.instagram_handle}")
                
                # Fetch from API
                instagram_data = get_instagram_user(brand.instagram_handle)
                
                if instagram_data.get('success'):
                    # Save to database
                    metric = create_metric(self.db, {
                        'brand_id': brand.id,
                        'platform': 'instagram',
                        'followers': instagram_data.get('followers'),
                        'following': instagram_data.get('following'),
                        'posts': instagram_data.get('posts'),
                        'recorded_at': datetime.utcnow()
                    })
                    
                    result.instagram_success = True
                    result.instagram_followers = instagram_data.get('followers')
                    logger.info(f"✓ Instagram synced for {brand.name}: {result.instagram_followers:,} followers")
                else:
                    result.instagram_error = instagram_data.get('error', 'Unknown error')
                    logger.warning(f"✗ Instagram failed for {brand.name}: {result.instagram_error}")
                
                # Respect rate limits
                time.sleep(self.delay)
                
            except Exception as e:
                result.instagram_error = str(e)
                logger.error(f"✗ Instagram exception for {brand.name}: {e}")
        
        return result
    
    def sync_all_brands(self, brand_ids: Optional[List[int]] = None) -> SyncSummary:
        """
        Sync all brands or a specific list of brand IDs
        
        Args:
            brand_ids: Optional list of brand IDs to sync. If None, syncs all brands.
            
        Returns:
            SyncSummary with complete sync results
        """
        started_at = datetime.utcnow()
        
        # Create sync log
        sync_log = create_sync_log(self.db, 'social_media_api')
        logger.info(f"Starting social media sync (log_id: {sync_log.id})")
        
        # Get brands to sync
        if brand_ids:
            brands = self.db.query(Brand).filter(Brand.id.in_(brand_ids)).all()
        else:
            brands = self.get_brands_to_sync()
        
        results: List[SyncResult] = []
        tiktok_success_count = 0
        instagram_success_count = 0
        error_count = 0
        
        logger.info(f"Syncing {len(brands)} brands...")
        
        for i, brand in enumerate(brands, 1):
            logger.info(f"[{i}/{len(brands)}] Processing: {brand.name}")
            
            result = self.sync_brand(brand)
            results.append(result)
            
            if result.tiktok_success:
                tiktok_success_count += 1
            if result.instagram_success:
                instagram_success_count += 1
            if result.tiktok_error or result.instagram_error:
                error_count += 1
            
            # Commit after each brand to save progress
            self.db.commit()
        
        completed_at = datetime.utcnow()
        duration = (completed_at - started_at).total_seconds()
        
        # Update sync log
        records_processed = len(brands)
        records_inserted = tiktok_success_count + instagram_success_count
        
        update_sync_log(
            self.db,
            sync_log.id,
            status='success' if error_count == 0 else 'partial',
            records_processed=records_processed,
            records_inserted=records_inserted,
            records_updated=0,
            error_message=None if error_count == 0 else f"{error_count} errors occurred"
        )
        
        summary = SyncSummary(
            sync_id=sync_log.id,
            started_at=started_at,
            completed_at=completed_at,
            total_brands=len(brands),
            tiktok_success=tiktok_success_count,
            instagram_success=instagram_success_count,
            errors=error_count,
            results=results
        )
        
        logger.info(f"✓ Sync completed in {duration:.1f}s")
        logger.info(f"  TikTok: {tiktok_success_count}/{len(brands)} successful")
        logger.info(f"  Instagram: {instagram_success_count}/{len(brands)} successful")
        logger.info(f"  Errors: {error_count}")
        
        return summary
    
    def get_rate_limit_status(self) -> Dict[str, Any]:
        """Get current rate limit status for both APIs"""
        return {
            "tiktok": self.tiktok_api.get_rate_limit_status(),
            "instagram": self.instagram_api.get_rate_limit_status()
        }
    
    def get_last_sync_info(self) -> Optional[Dict]:
        """Get information about the last sync operation"""
        last_sync = self.db.query(SyncLog).filter(
            SyncLog.source == 'social_media_api'
        ).order_by(SyncLog.started_at.desc()).first()
        
        if not last_sync:
            return None
        
        return {
            "id": last_sync.id,
            "source": last_sync.source,
            "status": last_sync.status,
            "records_processed": last_sync.records_processed,
            "records_inserted": last_sync.records_inserted,
            "records_updated": last_sync.records_updated,
            "error_message": last_sync.error_message,
            "started_at": last_sync.started_at.isoformat() if last_sync.started_at else None,
            "completed_at": last_sync.completed_at.isoformat() if last_sync.completed_at else None,
        }


def sync_all_brands(brand_ids: Optional[List[int]] = None, db_session: Optional[Session] = None) -> Dict[str, Any]:
    """
    Convenience function to sync all brands
    
    Args:
        brand_ids: Optional list of brand IDs to sync
        db_session: Optional database session
        
    Returns:
        Dictionary with sync summary
    """
    service = SocialSyncService(db_session)
    
    try:
        summary = service.sync_all_brands(brand_ids)
        
        return {
            "success": True,
            "sync_id": summary.sync_id,
            "started_at": summary.started_at.isoformat(),
            "completed_at": summary.completed_at.isoformat() if summary.completed_at else None,
            "total_brands": summary.total_brands,
            "tiktok_success": summary.tiktok_success,
            "instagram_success": summary.instagram_success,
            "errors": summary.errors,
            "details": [
                {
                    "brand_id": r.brand_id,
                    "brand_name": r.brand_name,
                    "tiktok_success": r.tiktok_success,
                    "instagram_success": r.instagram_success,
                    "tiktok_error": r.tiktok_error,
                    "instagram_error": r.instagram_error,
                    "tiktok_followers": r.tiktok_followers,
                    "instagram_followers": r.instagram_followers
                }
                for r in summary.results
            ]
        }
    except Exception as e:
        logger.error(f"Sync failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }


def sync_single_brand(brand_id: int, db_session: Optional[Session] = None) -> Dict[str, Any]:
    """
    Sync a single brand by ID
    
    Args:
        brand_id: Brand ID to sync
        db_session: Optional database session
        
    Returns:
        Dictionary with sync result
    """
    service = SocialSyncService(db_session)
    
    try:
        brand = service.db.query(Brand).filter(Brand.id == brand_id).first()
        if not brand:
            return {
                "success": False,
                "error": f"Brand with ID {brand_id} not found"
            }
        
        # Capture brand info before sync in case session gets closed
        brand_id = brand.id
        brand_name = brand.name
        
        result = service.sync_brand(brand)
        service.db.commit()
        
        return {
            "success": True,
            "brand_id": result.brand_id,
            "brand_name": result.brand_name,
            "tiktok": {
                "success": result.tiktok_success,
                "followers": result.tiktok_followers,
                "error": result.tiktok_error
            },
            "instagram": {
                "success": result.instagram_success,
                "followers": result.instagram_followers,
                "error": result.instagram_error
            }
        }
    except Exception as e:
        logger.error(f"Single brand sync failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }


def get_sync_status() -> Dict[str, Any]:
    """Get current sync and rate limit status"""
    service = SocialSyncService()
    
    return {
        "rate_limits": service.get_rate_limit_status(),
        "last_sync": service.get_last_sync_info()
    }


# Test function
if __name__ == "__main__":
    # Test sync status
    status = get_sync_status()
    print("Sync Status:")
    print(json.dumps(status, indent=2, default=str))
    
    print("\n" + "="*60 + "\n")
    
    # Test sync with one brand
    print("Testing sync for brand ID 1...")
    result = sync_single_brand(1)
    print(json.dumps(result, indent=2, default=str))
