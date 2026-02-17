#!/usr/bin/env python3
"""
Research Scheduler Module
Handles automated research jobs for the beverage brands dashboard.
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

# Setup logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from sqlalchemy.orm import Session

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import get_db_session, Brand, PendingBrand, UpdateLog
from services.credits_tracker import CreditsTracker, track_research_job

# Import brand research module
scripts_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), 'scripts')
sys.path.insert(0, scripts_path)

try:
    from brand_research import BrandResearcher, BrandInfo
except ImportError as e:
    # Fallback: define a simple BrandResearcher if the module is not available
    logger.warning(f"Could not import brand_research module: {e}. Using fallback implementation.")
    BrandResearcher = None
    BrandInfo = None

# Import simple research as fallback
try:
    from services.simple_research import research_website_simple
except ImportError:
    research_website_simple = None


class ResearchStatus(str, Enum):
    """Status of research jobs."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    APPROVED = "approved"
    REJECTED = "rejected"


@dataclass
class ResearchResult:
    """Result of a research operation."""
    success: bool
    brand_name: str
    data: Optional[Dict[str, Any]] = None
    updates: Optional[List[Dict]] = None
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)


class ResearchScheduler:
    """Handles automated research jobs for beverage brands."""
    
    # Industry sites to browse for new brand discovery
    DISCOVERY_SOURCES = [
        "beverage industry news emerging brands 2024",
        "new beverage startups trending",
        "functional beverage brands launch",
        "better-for-you drink brands",
        "craft beverage brands emerging",
    ]
    
    def __init__(self, db_session: Optional[Session] = None, use_selenium: bool = False):
        """
        Initialize the research scheduler.
        
        Args:
            db_session: Optional database session
            use_selenium: Whether to use Selenium for web scraping
        """
        self.db = db_session
        self._db_owner = db_session is None
        self.use_selenium = use_selenium
        self.researcher = None
        self.credits_tracker = CreditsTracker(db_session)
    
    def _get_db(self) -> Session:
        """Get database session."""
        if self.db is None:
            self.db = get_db_session()
        return self.db
    
    def _get_researcher(self):
        """Get or create BrandResearcher instance."""
        if BrandResearcher is None:
            raise ImportError("BrandResearcher not available. Please install required dependencies.")
        if self.researcher is None:
            self.researcher = BrandResearcher(use_selenium=self.use_selenium)
        return self.researcher
    
    def _log_update(self, brand_id: int, brand_name: str, field: str,
                    old_value: str, new_value: str, update_type: str):
        """Log a brand update to the update log."""
        db = self._get_db()
        
        log = UpdateLog(
            brand_id=brand_id,
            brand_name=brand_name,
            field_changed=field,
            old_value=old_value,
            new_value=new_value,
            update_type=update_type,
            updated_at=datetime.utcnow()
        )
        
        db.add(log)
        db.commit()
        logger.info(f"Logged update for {brand_name}: {field} changed")
    
    def _update_brand_field(self, brand: Brand, field: str, new_value: Optional[str],
                            update_type: str) -> bool:
        """
        Update a single brand field if changed.
        
        Returns:
            True if field was updated, False otherwise
        """
        old_value = getattr(brand, field)
        
        # Normalize values for comparison
        old_str = str(old_value) if old_value else ""
        new_str = str(new_value) if new_value else ""
        
        if old_str != new_str and new_value:
            setattr(brand, field, new_value)
            self._log_update(brand.id, brand.name, field, old_str, new_str, update_type)
            return True
        return False

    # ===== JOB A: Monthly Update Job =====
    
    def run_monthly_update(self, brand_ids: Optional[List[int]] = None) -> List[ResearchResult]:
        """
        Run monthly update job to re-research all existing brands.
        
        Args:
            brand_ids: Optional list of specific brand IDs to update. If None, updates all.
            
        Returns:
            List of research results
        """
        logger.info("Starting monthly update job...")
        track_research_job('monthly_update_start', metadata={'brand_count': len(brand_ids) if brand_ids else 'all'})
        
        db = self._get_db()
        
        if brand_ids:
            brands = db.query(Brand).filter(Brand.id.in_(brand_ids)).all()
        else:
            brands = db.query(Brand).all()
        
        results = []
        
        for brand in brands:
            try:
                result = self._research_and_update_brand(brand, 'monthly_update')
                results.append(result)
            except Exception as e:
                logger.error(f"Error updating brand {brand.name}: {str(e)}")
                results.append(ResearchResult(
                    success=False,
                    brand_name=brand.name,
                    error_message=str(e)
                ))
        
        # Track completion
        track_research_job('monthly_update_complete', metadata={
            'brands_processed': len(brands),
            'successful': sum(1 for r in results if r.success)
        })
        
        logger.info(f"Monthly update complete. Processed {len(brands)} brands.")
        return results
    
    def _research_and_update_brand(self, brand: Brand, update_type: str) -> ResearchResult:
        """
        Research a brand and update its information.
        
        Args:
            brand: Brand model instance
            update_type: Type of update (monthly_update, immediate, etc.)
            
        Returns:
            ResearchResult
        """
        researcher = self._get_researcher()
        db = self._get_db()
        
        # Research the brand
        info = researcher.research_brand(brand.name)
        
        updates = []
        
        # Check for changes and update
        fields_to_check = [
            ('website', info.website),
            ('instagram_handle', info.instagram.lstrip('@') if info.instagram else None),
            ('tiktok_handle', info.tiktok.lstrip('@') if info.tiktok else None),
            ('category', info.category),
        ]
        
        # Parse location if available
        if info.location:
            # Simple location parsing - could be enhanced
            parts = info.location.split(',')
            if len(parts) >= 2:
                city = parts[0].strip()
                state = parts[1].strip()
                if self._update_brand_field(brand, 'hq_city', city, update_type):
                    updates.append({'field': 'hq_city', 'new_value': city})
                if self._update_brand_field(brand, 'hq_state', state, update_type):
                    updates.append({'field': 'hq_state', 'new_value': state})
        
        for field, new_value in fields_to_check:
            if self._update_brand_field(brand, field, new_value, update_type):
                updates.append({'field': field, 'new_value': new_value})
        
        # Update the updated_at timestamp
        brand.updated_at = datetime.utcnow()
        
        db.commit()
        
        return ResearchResult(
            success=True,
            brand_name=brand.name,
            data=info.to_dict(),
            updates=updates if updates else None
        )

    # ===== JOB B: Immediate Research Job =====
    
    def research_brand_from_website(self, website_url: str) -> ResearchResult:
        """
        Research a brand from its website and add to database.
        
        Args:
            website_url: URL of the brand website
            
        Returns:
            ResearchResult
        """
        logger.info(f"Starting immediate research for website: {website_url}")
        track_research_job('immediate_start', metadata={'website': website_url})
        
        try:
            # Fetch and parse the website
            researcher = self._get_researcher()
            html = researcher._fetch_page(website_url, use_selenium=self.use_selenium)
            
            if not html:
                return ResearchResult(
                    success=False,
                    brand_name="Unknown",
                    error_message=f"Could not fetch website: {website_url}"
                )
            
            # Extract information from the website
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'lxml')
            
            # Try to extract brand name from title or meta
            brand_name = None
            if soup.title:
                brand_name = soup.title.string.split('|')[0].split('-')[0].strip()
            
            # Extract social handles
            social = researcher._extract_social_handles(html, website_url)
            
            # Extract location
            location = researcher._extract_location(html)
            
            # Extract category
            category = researcher._extract_category(html)
            
            # If no brand name found, use domain
            if not brand_name:
                from urllib.parse import urlparse
                domain = urlparse(website_url).netloc
                brand_name = domain.replace('www.', '').split('.')[0].title()
            
            # Check if brand already exists
            db = self._get_db()
            existing = db.query(Brand).filter(Brand.name.ilike(brand_name)).first()
            
            if existing:
                # Update existing brand
                result = self._research_and_update_brand(existing, 'immediate')
                track_research_job('immediate_complete', brand_name, {
                    'website': website_url,
                    'action': 'updated_existing'
                })
                return result
            
            # Parse location
            hq_city = None
            hq_state = None
            if location:
                parts = location.split(',')
                if len(parts) >= 2:
                    hq_city = parts[0].strip()
                    hq_state = parts[1].strip()
            
            # Create new brand
            brand_data = {
                'name': brand_name,
                'website': website_url,
                'instagram_handle': social.get('instagram', '').lstrip('@') if social.get('instagram') else None,
                'tiktok_handle': social.get('tiktok', '').lstrip('@') if social.get('tiktok') else None,
                'category': category or 'Unknown',
                'hq_city': hq_city,
                'hq_state': hq_state,
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow(),
            }
            
            new_brand = Brand(**brand_data)
            db.add(new_brand)
            db.commit()
            db.refresh(new_brand)
            
            track_research_job('immediate_complete', brand_name, {
                'website': website_url,
                'action': 'created_new',
                'brand_id': new_brand.id
            })
            
            logger.info(f"Created new brand: {brand_name}")
            
            return ResearchResult(
                success=True,
                brand_name=brand_name,
                data=brand_data
            )
            
        except Exception as e:
            logger.error(f"Error researching website {website_url}: {str(e)}")
            track_research_job('immediate_failed', metadata={'website': website_url, 'error': str(e)})
            return ResearchResult(
                success=False,
                brand_name="Unknown",
                error_message=str(e)
            )

    # ===== JOB C: Weekly New Brand Discovery =====
    
    def discover_new_brands(self, limit: int = 10) -> List[Dict]:
        """
        Discover new/emerging beverage brands.
        
        Args:
            limit: Maximum number of brands to discover
            
        Returns:
            List of discovered brand dictionaries
        """
        logger.info("Starting new brand discovery...")
        track_research_job('discovery_start', metadata={'limit': limit})
        
        try:
            researcher = self._get_researcher()
            discovered = []
            
            # Search for new brands using different queries
            for query in self.DISCOVERY_SOURCES:
                try:
                    results = researcher._search_google(query)
                    
                    for url in results[:5]:  # Top 5 results per query
                        # Skip social media and known directories
                        if any(x in url for x in ['instagram.com', 'tiktok.com', 'facebook.com',
                                                   'linkedin.com', 'youtube.com', 'wikipedia.org']):
                            continue
                        
                        # Try to extract brand name from URL
                        from urllib.parse import urlparse
                        domain = urlparse(url).netloc.lower()
                        brand_name = domain.replace('www.', '').split('.')[0].title()
                        
                        # Check if already in database
                        db = self._get_db()
                        existing = db.query(Brand).filter(
                            Brand.website.ilike(f"%{domain}%")
                        ).first()
                        
                        if existing:
                            continue
                        
                        # Check if already pending
                        pending = db.query(PendingBrand).filter(
                            PendingBrand.website.ilike(f"%{domain}%")
                        ).first()
                        
                        if pending:
                            continue
                        
                        # Try to get more info from the website
                        try:
                            html = researcher._fetch_page(url, timeout=10)
                            if html:
                                social = researcher._extract_social_handles(html, url)
                                category = researcher._extract_category(html)
                                location = researcher._extract_location(html)
                                
                                # Add to pending
                                pending_brand = PendingBrand(
                                    name=brand_name,
                                    website=url,
                                    instagram_handle=social.get('instagram', '').lstrip('@') if social.get('instagram') else None,
                                    tiktok_handle=social.get('tiktok', '').lstrip('@') if social.get('tiktok') else None,
                                    category=category,
                                    location=location,
                                    confidence_score=50,  # Base confidence
                                    source='discovery',
                                    metadata_json=json.dumps({'discovered_via': query})
                                )
                                
                                db.add(pending_brand)
                                db.commit()
                                
                                discovered.append(pending_brand.to_dict())
                                
                                if len(discovered) >= limit:
                                    break
                        except Exception as e:
                            logger.warning(f"Could not process {url}: {str(e)}")
                            continue
                    
                    if len(discovered) >= limit:
                        break
                        
                except Exception as e:
                    logger.warning(f"Error searching with query '{query}': {str(e)}")
                    continue
            
            track_research_job('discovery_complete', metadata={
                'brands_discovered': len(discovered)
            })
            
            logger.info(f"Discovery complete. Found {len(discovered)} new brands.")
            return discovered
            
        except Exception as e:
            logger.error(f"Error in brand discovery: {str(e)}")
            track_research_job('discovery_failed', metadata={'error': str(e)})
            return []
    
    def get_pending_brands(self, status: Optional[str] = None) -> List[Dict]:
        """
        Get pending brands for approval.
        
        Args:
            status: Filter by status
            
        Returns:
            List of pending brand dictionaries
        """
        db = self._get_db()
        query = db.query(PendingBrand)
        
        if status:
            query = query.filter(PendingBrand.status == status)
        
        pending = query.order_by(PendingBrand.discovered_at.desc()).all()
        return [p.to_dict() for p in pending]
    
    def approve_pending_brand(self, pending_id: int) -> Optional[Brand]:
        """
        Approve a pending brand and add it to the main database.
        
        Args:
            pending_id: ID of the pending brand
            
        Returns:
            Created Brand or None
        """
        db = self._get_db()
        
        pending = db.query(PendingBrand).filter(PendingBrand.id == pending_id).first()
        if not pending:
            return None
        
        # Parse location
        hq_city = None
        hq_state = None
        if pending.location:
            parts = pending.location.split(',')
            if len(parts) >= 2:
                hq_city = parts[0].strip()
                hq_state = parts[1].strip()
        
        # Create brand
        brand_data = {
            'name': pending.name,
            'website': pending.website,
            'instagram_handle': pending.instagram_handle,
            'tiktok_handle': pending.tiktok_handle,
            'category': pending.category or 'Unknown',
            'hq_city': hq_city,
            'hq_state': hq_state,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
        }
        
        brand = Brand(**brand_data)
        db.add(brand)
        
        # Update pending status
        pending.status = ResearchStatus.APPROVED.value
        
        db.commit()
        db.refresh(brand)
        
        logger.info(f"Approved pending brand: {pending.name}")
        return brand
    
    def reject_pending_brand(self, pending_id: int) -> bool:
        """
        Reject a pending brand.
        
        Args:
            pending_id: ID of the pending brand
            
        Returns:
            True if rejected, False if not found
        """
        db = self._get_db()
        
        pending = db.query(PendingBrand).filter(PendingBrand.id == pending_id).first()
        if not pending:
            return False
        
        pending.status = ResearchStatus.REJECTED.value
        db.commit()
        
        logger.info(f"Rejected pending brand: {pending.name}")
        return True
    
    def get_update_logs(self, brand_id: Optional[int] = None, 
                        days: int = 30) -> List[Dict]:
        """
        Get update logs.
        
        Args:
            brand_id: Filter by brand ID
            days: Number of days to look back
            
        Returns:
            List of update log dictionaries
        """
        db = self._get_db()
        
        since = datetime.utcnow() - timedelta(days=days)
        query = db.query(UpdateLog).filter(UpdateLog.updated_at >= since)
        
        if brand_id:
            query = query.filter(UpdateLog.brand_id == brand_id)
        
        logs = query.order_by(UpdateLog.updated_at.desc()).all()
        return [log.to_dict() for log in logs]
    
    def close(self):
        """Clean up resources."""
        if self.researcher:
            self.researcher.close()
            self.researcher = None
        if self.credits_tracker:
            self.credits_tracker.close()
            self.credits_tracker = None
        if self._db_owner and self.db:
            self.db.close()
            self.db = None


# Convenience functions for cron jobs

def run_monthly_update(brand_ids: Optional[List[int]] = None) -> List[ResearchResult]:
    """Run monthly update job (convenience function)."""
    scheduler = ResearchScheduler()
    try:
        return scheduler.run_monthly_update(brand_ids)
    finally:
        scheduler.close()


def research_brand_website(website_url: str) -> ResearchResult:
    """Research a brand from website (convenience function)."""
    # Try simple research first (no Selenium required)
    if research_website_simple:
        try:
            result = research_website_simple(website_url)
            if result.get('success'):
                return ResearchResult(
                    success=True,
                    brand_name=result.get('brand_name', 'Unknown'),
                    data=result
                )
        except Exception as e:
            logger.warning(f"Simple research failed: {e}, trying full research...")
    
    # Fall back to full research scheduler
    scheduler = ResearchScheduler()
    try:
        return scheduler.research_brand_from_website(website_url)
    finally:
        scheduler.close()


def discover_new_brands(limit: int = 10) -> List[Dict]:
    """Discover new brands (convenience function)."""
    scheduler = ResearchScheduler()
    try:
        return scheduler.discover_new_brands(limit)
    finally:
        scheduler.close()


if __name__ == '__main__':
    # Test the module
    print("Testing Research Scheduler...")
    
    scheduler = ResearchScheduler()
    
    # Test immediate research
    print("\n1. Testing immediate research from website...")
    result = scheduler.research_brand_from_website("https://drinkpoppi.com")
    print(f"Success: {result.success}")
    print(f"Brand: {result.brand_name}")
    if result.data:
        print(f"Data: {json.dumps(result.data, indent=2)}")
    if result.error_message:
        print(f"Error: {result.error_message}")
    
    # Test pending brands
    print("\n2. Getting pending brands...")
    pending = scheduler.get_pending_brands()
    print(f"Found {len(pending)} pending brands")
    
    # Test update logs
    print("\n3. Getting update logs...")
    logs = scheduler.get_update_logs(days=7)
    print(f"Found {len(logs)} update logs in last 7 days")
    
    scheduler.close()
    print("\nTest complete!")
