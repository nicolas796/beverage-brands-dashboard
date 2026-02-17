#!/usr/bin/env python3
"""
Credits Tracker Module
Tracks API usage and costs for the beverage brands dashboard.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum

from sqlalchemy.orm import Session

from models import get_db_session, CreditUsage

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OperationType(str, Enum):
    """Types of operations that incur costs."""
    API_CALL_TIKTOK = "api_call_tiktok"
    API_CALL_INSTAGRAM = "api_call_instagram"
    API_CALL_WEB_SEARCH = "api_call_web_search"
    DATABASE_QUERY = "database_query"
    RESEARCH_JOB = "research_job"
    COMPUTE_TIME = "compute_time"


# Cost configuration (in USD)
# These can be overridden via environment variables
DEFAULT_COSTS = {
    OperationType.API_CALL_TIKTOK: 0.001,      # $0.001 per TikTok API call
    OperationType.API_CALL_INSTAGRAM: 0.001,   # $0.001 per Instagram API call
    OperationType.API_CALL_WEB_SEARCH: 0.01,   # $0.01 per web search (Brave API)
    OperationType.DATABASE_QUERY: 0.0001,      # $0.0001 per database query
    OperationType.RESEARCH_JOB: 0.05,          # $0.05 per research job
    OperationType.COMPUTE_TIME: 0.01,          # $0.01 per minute of compute time
}

# Monthly budget default
DEFAULT_MONTHLY_BUDGET = 100.0  # $100 USD


@dataclass
class UsageStats:
    """Usage statistics for a period."""
    total_cost: float
    api_calls_cost: float
    research_jobs_cost: float
    database_ops_cost: float
    compute_cost: float
    total_operations: int
    api_calls_count: int
    research_jobs_count: int
    database_ops_count: int
    compute_minutes: float
    
    def to_dict(self) -> Dict:
        return asdict(self)


class CreditsTracker:
    """Tracks API usage and costs."""
    
    def __init__(self, db_session: Optional[Session] = None):
        """
        Initialize the credits tracker.
        
        Args:
            db_session: Optional database session. If not provided, a new one will be created.
        """
        self.db = db_session
        self._db_owner = db_session is None
        self.costs = self._load_costs()
        self.monthly_budget = float(os.getenv('MONTHLY_BUDGET', DEFAULT_MONTHLY_BUDGET))
    
    def _load_costs(self) -> Dict[OperationType, float]:
        """Load cost configuration from environment or defaults."""
        costs = {}
        for op_type in OperationType:
            env_var = f"COST_{op_type.value.upper()}"
            costs[op_type] = float(os.getenv(env_var, DEFAULT_COSTS.get(op_type, 0.0)))
        return costs
    
    def _get_db(self) -> Session:
        """Get database session."""
        if self.db is None:
            self.db = get_db_session()
        return self.db
    
    def log_usage(self, operation_type: OperationType, 
                  description: Optional[str] = None,
                  metadata: Optional[Dict] = None,
                  custom_cost: Optional[float] = None) -> CreditUsage:
        """
        Log a credit usage event.
        
        Args:
            operation_type: Type of operation
            description: Optional description
            metadata: Optional metadata dictionary
            custom_cost: Optional custom cost (uses default if not provided)
            
        Returns:
            CreditUsage record
        """
        db = self._get_db()
        
        cost = custom_cost if custom_cost is not None else self.costs.get(operation_type, 0.0)
        
        usage = CreditUsage(
            operation_type=operation_type.value,
            description=description,
            cost_usd=cost,
            metadata_json=json.dumps(metadata) if metadata else None,
            created_at=datetime.utcnow()
        )
        
        db.add(usage)
        db.commit()
        db.refresh(usage)
        
        logger.debug(f"Logged usage: {operation_type.value} - ${cost:.4f}")
        return usage
    
    def log_api_call(self, platform: str, endpoint: Optional[str] = None,
                     metadata: Optional[Dict] = None) -> CreditUsage:
        """
        Log an API call.
        
        Args:
            platform: Platform name (tiktok, instagram, web_search)
            endpoint: API endpoint
            metadata: Additional metadata
            
        Returns:
            CreditUsage record
        """
        if platform.lower() == 'tiktok':
            op_type = OperationType.API_CALL_TIKTOK
        elif platform.lower() == 'instagram':
            op_type = OperationType.API_CALL_INSTAGRAM
        elif platform.lower() == 'web_search':
            op_type = OperationType.API_CALL_WEB_SEARCH
        else:
            op_type = OperationType.API_CALL_WEB_SEARCH
        
        desc = f"API call to {platform}"
        if endpoint:
            desc += f" - {endpoint}"
        
        meta = metadata or {}
        meta['platform'] = platform
        if endpoint:
            meta['endpoint'] = endpoint
        
        return self.log_usage(op_type, desc, meta)
    
    def log_database_query(self, query_type: str, 
                           metadata: Optional[Dict] = None) -> CreditUsage:
        """
        Log a database query.
        
        Args:
            query_type: Type of query (select, insert, update, delete)
            metadata: Additional metadata
            
        Returns:
            CreditUsage record
        """
        meta = metadata or {}
        meta['query_type'] = query_type
        
        return self.log_usage(
            OperationType.DATABASE_QUERY,
            f"Database {query_type} query",
            meta
        )
    
    def log_research_job(self, job_type: str, brand_name: Optional[str] = None,
                         metadata: Optional[Dict] = None) -> CreditUsage:
        """
        Log a research job.
        
        Args:
            job_type: Type of research job (monthly_update, immediate, discovery)
            brand_name: Name of brand being researched
            metadata: Additional metadata
            
        Returns:
            CreditUsage record
        """
        meta = metadata or {}
        meta['job_type'] = job_type
        if brand_name:
            meta['brand_name'] = brand_name
        
        desc = f"Research job: {job_type}"
        if brand_name:
            desc += f" for {brand_name}"
        
        return self.log_usage(OperationType.RESEARCH_JOB, desc, meta)
    
    def log_compute_time(self, minutes: float, task_name: Optional[str] = None,
                         metadata: Optional[Dict] = None) -> CreditUsage:
        """
        Log compute time usage.
        
        Args:
            minutes: Minutes of compute time
            task_name: Name of the task
            metadata: Additional metadata
            
        Returns:
            CreditUsage record
        """
        meta = metadata or {}
        meta['minutes'] = minutes
        if task_name:
            meta['task'] = task_name
        
        # Calculate cost based on minutes
        cost = self.costs[OperationType.COMPUTE_TIME] * minutes
        
        desc = f"Compute time: {minutes:.2f} minutes"
        if task_name:
            desc += f" for {task_name}"
        
        return self.log_usage(OperationType.COMPUTE_TIME, desc, meta, cost)
    
    def get_usage_for_period(self, days: int = 30) -> UsageStats:
        """
        Get usage statistics for a period.
        
        Args:
            days: Number of days to look back
            
        Returns:
            UsageStats object
        """
        db = self._get_db()
        
        since = datetime.utcnow() - timedelta(days=days)
        
        records = db.query(CreditUsage).filter(
            CreditUsage.created_at >= since
        ).all()
        
        stats = UsageStats(
            total_cost=0.0,
            api_calls_cost=0.0,
            research_jobs_cost=0.0,
            database_ops_cost=0.0,
            compute_cost=0.0,
            total_operations=0,
            api_calls_count=0,
            research_jobs_count=0,
            database_ops_count=0,
            compute_minutes=0.0
        )
        
        for record in records:
            stats.total_cost += record.cost_usd
            stats.total_operations += 1
            
            op_type = record.operation_type
            
            if 'api_call' in op_type:
                stats.api_calls_cost += record.cost_usd
                stats.api_calls_count += 1
            elif op_type == OperationType.RESEARCH_JOB.value:
                stats.research_jobs_cost += record.cost_usd
                stats.research_jobs_count += 1
            elif op_type == OperationType.DATABASE_QUERY.value:
                stats.database_ops_cost += record.cost_usd
                stats.database_ops_count += 1
            elif op_type == OperationType.COMPUTE_TIME.value:
                stats.compute_cost += record.cost_usd
                metadata = json.loads(record.metadata_json) if record.metadata_json else {}
                stats.compute_minutes += metadata.get('minutes', 0)
        
        return stats
    
    def get_monthly_usage(self) -> UsageStats:
        """Get usage for current month."""
        return self.get_usage_for_period(30)
    
    def get_daily_breakdown(self, days: int = 30) -> List[Dict]:
        """
        Get daily usage breakdown.
        
        Args:
            days: Number of days to look back
            
        Returns:
            List of daily usage dictionaries
        """
        db = self._get_db()
        
        since = datetime.utcnow() - timedelta(days=days)
        
        records = db.query(CreditUsage).filter(
            CreditUsage.created_at >= since
        ).all()
        
        # Group by day
        daily = {}
        for record in records:
            day = record.created_at.strftime('%Y-%m-%d')
            if day not in daily:
                daily[day] = {
                    'date': day,
                    'total_cost': 0.0,
                    'api_calls_cost': 0.0,
                    'research_jobs_cost': 0.0,
                    'database_ops_cost': 0.0,
                    'compute_cost': 0.0,
                    'operations_count': 0
                }
            
            daily[day]['total_cost'] += record.cost_usd
            daily[day]['operations_count'] += 1
            
            op_type = record.operation_type
            if 'api_call' in op_type:
                daily[day]['api_calls_cost'] += record.cost_usd
            elif op_type == OperationType.RESEARCH_JOB.value:
                daily[day]['research_jobs_cost'] += record.cost_usd
            elif op_type == OperationType.DATABASE_QUERY.value:
                daily[day]['database_ops_cost'] += record.cost_usd
            elif op_type == OperationType.COMPUTE_TIME.value:
                daily[day]['compute_cost'] += record.cost_usd
        
        # Convert to sorted list
        result = sorted(daily.values(), key=lambda x: x['date'])
        return result
    
    def get_budget_status(self) -> Dict:
        """
        Get current budget status.
        
        Returns:
            Dictionary with budget information
        """
        usage = self.get_monthly_usage()
        
        remaining = self.monthly_budget - usage.total_cost
        percent_used = (usage.total_cost / self.monthly_budget * 100) if self.monthly_budget > 0 else 0
        
        return {
            'monthly_budget': self.monthly_budget,
            'used_amount': round(usage.total_cost, 2),
            'remaining_amount': round(max(0, remaining), 2),
            'percent_used': round(percent_used, 2),
            'is_over_budget': usage.total_cost > self.monthly_budget,
            'projected_monthly': round(usage.total_cost * (30 / max(1, self._get_days_into_month())), 2)
        }
    
    def _get_days_into_month(self) -> int:
        """Get number of days into current month."""
        now = datetime.utcnow()
        return now.day
    
    def close(self):
        """Close database session if owned."""
        if self._db_owner and self.db:
            self.db.close()
            self.db = None


# Convenience functions for quick usage tracking

def track_api_call(platform: str, endpoint: Optional[str] = None,
                   metadata: Optional[Dict] = None) -> CreditUsage:
    """Track an API call (convenience function)."""
    tracker = CreditsTracker()
    try:
        return tracker.log_api_call(platform, endpoint, metadata)
    finally:
        tracker.close()


def track_research_job(job_type: str, brand_name: Optional[str] = None,
                       metadata: Optional[Dict] = None) -> CreditUsage:
    """Track a research job (convenience function)."""
    tracker = CreditsTracker()
    try:
        return tracker.log_research_job(job_type, brand_name, metadata)
    finally:
        tracker.close()


def track_database_query(query_type: str, metadata: Optional[Dict] = None) -> CreditUsage:
    """Track a database query (convenience function)."""
    tracker = CreditsTracker()
    try:
        return tracker.log_database_query(query_type, metadata)
    finally:
        tracker.close()


def get_usage_summary(days: int = 30) -> Dict:
    """Get usage summary (convenience function)."""
    tracker = CreditsTracker()
    try:
        stats = tracker.get_usage_for_period(days)
        budget = tracker.get_budget_status()
        return {
            'stats': stats.to_dict(),
            'budget': budget,
            'daily_breakdown': tracker.get_daily_breakdown(days)
        }
    finally:
        tracker.close()


if __name__ == '__main__':
    # Test the module
    print("Testing Credits Tracker...")
    
    tracker = CreditsTracker()
    
    # Log some test usage
    tracker.log_api_call('tiktok', '/user/info', {'user_id': '12345'})
    tracker.log_api_call('instagram', '/user/profile', {'username': 'test'})
    tracker.log_research_job('immediate', 'Test Brand', {'website': 'https://example.com'})
    tracker.log_database_query('select', {'table': 'brands'})
    tracker.log_compute_time(5.5, 'brand_research')
    
    # Get usage stats
    stats = tracker.get_monthly_usage()
    print(f"\nTotal cost this month: ${stats.total_cost:.2f}")
    print(f"API calls: {stats.api_calls_count} (${stats.api_calls_cost:.2f})")
    print(f"Research jobs: {stats.research_jobs_count} (${stats.research_jobs_cost:.2f})")
    print(f"Database ops: {stats.database_ops_count} (${stats.database_ops_cost:.2f})")
    
    # Get budget status
    budget = tracker.get_budget_status()
    print(f"\nBudget: ${budget['monthly_budget']:.2f}")
    print(f"Used: ${budget['used_amount']:.2f} ({budget['percent_used']:.1f}%)")
    print(f"Remaining: ${budget['remaining_amount']:.2f}")
    
    tracker.close()
    print("\nTest complete!")
