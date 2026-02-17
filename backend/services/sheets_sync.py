"""
Google Sheets sync service for importing brand data
"""
import os
import json
from datetime import datetime
from typing import Optional, List, Dict

try:
    import gspread
    from google.oauth2.service_account import Credentials
    GOOGLE_LIBS_AVAILABLE = True
except ImportError:
    GOOGLE_LIBS_AVAILABLE = False

from database import get_db_session, create_brand, create_metric, create_sync_log, update_sync_log


def get_sheets_client():
    """Get authenticated Google Sheets client"""
    if not GOOGLE_LIBS_AVAILABLE:
        raise ImportError("Google libraries not installed. Run: pip install gspread google-auth")
    
    # Check for credentials file
    creds_path = os.getenv('GOOGLE_CREDENTIALS_PATH', 'credentials.json')
    
    if not os.path.exists(creds_path):
        raise FileNotFoundError(f"Credentials file not found: {creds_path}")
    
    scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    
    creds = Credentials.from_service_account_file(creds_path, scopes=scopes)
    client = gspread.authorize(creds)
    
    return client


def sync_from_sheets(sheet_id: Optional[str] = None) -> Dict:
    """
    Sync brand data from Google Sheets
    
    Expected sheet structure:
    - Sheet 1: Brands (name, category, hq_city, hq_state, country, website, instagram_handle, tiktok_handle, founders, founded_year, revenue, funding, parent_company, notes)
    - Sheet 2: Metrics (brand_name, platform, followers, following, posts, likes, comments, shares, views, engagement_rate, date)
    """
    if not GOOGLE_LIBS_AVAILABLE:
        return {
            "status": "error",
            "message": "Google libraries not installed"
        }
    
    db = get_db_session()
    
    # Create sync log
    log = create_sync_log(db, 'google_sheets')
    
    try:
        client = get_sheets_client()
        
        sheet_id = sheet_id or os.getenv('GOOGLE_SHEETS_ID')
        if not sheet_id:
            raise ValueError("Google Sheet ID not provided")
        
        spreadsheet = client.open_by_key(sheet_id)
        
        # Process Brands sheet
        brands_sheet = spreadsheet.worksheet('Brands')
        brands_data = brands_sheet.get_all_records()
        
        brands_created = 0
        brands_updated = 0
        
        for row in brands_data:
            # Check if brand exists
            from database import get_brand_by_name
            existing = get_brand_by_name(db, row.get('name', ''))
            
            brand_dict = {
                'name': row.get('name'),
                'category': row.get('category'),
                'hq_city': row.get('hq_city'),
                'hq_state': row.get('hq_state'),
                'country': row.get('country'),
                'website': row.get('website'),
                'instagram_handle': row.get('instagram_handle'),
                'tiktok_handle': row.get('tiktok_handle'),
                'founders': row.get('founders'),
                'founded_year': int(row.get('founded_year')) if row.get('founded_year') else None,
                'revenue': row.get('revenue'),
                'funding': row.get('funding'),
                'parent_company': row.get('parent_company'),
                'notes': row.get('notes')
            }
            
            if existing:
                # Update existing brand
                from database import update_brand
                update_brand(db, existing.id, brand_dict)
                brands_updated += 1
            else:
                # Create new brand
                create_brand(db, brand_dict)
                brands_created += 1
        
        # Process Metrics sheet
        try:
            metrics_sheet = spreadsheet.worksheet('Metrics')
            metrics_data = metrics_sheet.get_all_records()
            
            metrics_created = 0
            
            for row in metrics_data:
                brand_name = row.get('brand_name')
                brand = get_brand_by_name(db, brand_name)
                
                if not brand:
                    continue
                
                metric_dict = {
                    'brand_id': brand.id,
                    'platform': row.get('platform', 'instagram'),
                    'followers': int(row.get('followers')) if row.get('followers') else None,
                    'following': int(row.get('following')) if row.get('following') else None,
                    'posts': int(row.get('posts')) if row.get('posts') else None,
                    'likes': int(row.get('likes')) if row.get('likes') else None,
                    'comments': int(row.get('comments')) if row.get('comments') else None,
                    'shares': int(row.get('shares')) if row.get('shares') else None,
                    'views': int(row.get('views')) if row.get('views') else None,
                    'engagement_rate': float(row.get('engagement_rate')) if row.get('engagement_rate') else None,
                    'recorded_at': datetime.strptime(row.get('date'), '%Y-%m-%d') if row.get('date') else datetime.utcnow()
                }
                
                create_metric(db, metric_dict)
                metrics_created += 1
        except gspread.WorksheetNotFound:
            metrics_created = 0
        
        # Update sync log
        update_sync_log(
            db,
            log.id,
            status='success',
            records_processed=brands_created + brands_updated + metrics_created,
            records_inserted=brands_created + metrics_created,
            records_updated=brands_updated
        )
        
        return {
            "status": "success",
            "brands_created": brands_created,
            "brands_updated": brands_updated,
            "metrics_created": metrics_created,
            "sync_log_id": log.id
        }
        
    except Exception as e:
        # Update sync log with error
        update_sync_log(
            db,
            log.id,
            status='error',
            error_message=str(e)
        )
        
        return {
            "status": "error",
            "error": str(e),
            "sync_log_id": log.id
        }
    finally:
        db.close()


def export_to_sheets(sheet_id: Optional[str] = None) -> Dict:
    """Export current database data to Google Sheets"""
    if not GOOGLE_LIBS_AVAILABLE:
        return {
            "status": "error",
            "message": "Google libraries not installed"
        }
    
    db = get_db_session()
    
    try:
        client = get_sheets_client()
        
        sheet_id = sheet_id or os.getenv('GOOGLE_SHEETS_ID')
        if not sheet_id:
            raise ValueError("Google Sheet ID not provided")
        
        spreadsheet = client.open_by_key(sheet_id)
        
        # Get all brands
        from database import get_brands
        brands = get_brands(db, limit=10000)
        
        # Prepare brands data
        brands_headers = ['name', 'category', 'hq_city', 'hq_state', 'country', 
                         'website', 'instagram_handle', 'tiktok_handle', 'founders',
                         'founded_year', 'revenue', 'funding', 'parent_company', 'notes']
        
        brands_rows = [brands_headers]
        for brand in brands:
            row = [getattr(brand, h) for h in brands_headers]
            brands_rows.append(row)
        
        # Update or create Brands sheet
        try:
            brands_sheet = spreadsheet.worksheet('Brands')
            brands_sheet.clear()
        except gspread.WorksheetNotFound:
            brands_sheet = spreadsheet.add_worksheet('Brands', rows=1000, cols=20)
        
        brands_sheet.update(brands_rows)
        
        # Get all metrics
        from database import get_metrics
        metrics = get_metrics(db, limit=10000)
        
        # Prepare metrics data
        metrics_headers = ['brand_name', 'platform', 'followers', 'following', 'posts',
                          'likes', 'comments', 'shares', 'views', 'engagement_rate', 'date']
        
        metrics_rows = [metrics_headers]
        for metric in metrics:
            brand = get_brand_by_id(db, metric.brand_id)
            if brand:
                row = [
                    brand.name,
                    metric.platform,
                    metric.followers,
                    metric.following,
                    metric.posts,
                    metric.likes,
                    metric.comments,
                    metric.shares,
                    metric.views,
                    metric.engagement_rate,
                    metric.recorded_at.strftime('%Y-%m-%d')
                ]
                metrics_rows.append(row)
        
        # Update or create Metrics sheet
        try:
            metrics_sheet = spreadsheet.worksheet('Metrics')
            metrics_sheet.clear()
        except gspread.WorksheetNotFound:
            metrics_sheet = spreadsheet.add_worksheet('Metrics', rows=5000, cols=15)
        
        metrics_sheet.update(metrics_rows)
        
        return {
            "status": "success",
            "brands_exported": len(brands),
            "metrics_exported": len(metrics)
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }
    finally:
        db.close()


def mock_sync_data():
    """Create mock data for testing without Google Sheets"""
    db = get_db_session()
    
    log = create_sync_log(db, 'mock_data')
    
    try:
        # This will use the sample data from init_db
        from init_db import init_sample_data
        init_sample_data()
        
        update_sync_log(
            db,
            log.id,
            status='success',
            records_processed=50,
            records_inserted=50,
            records_updated=0
        )
        
        return {
            "status": "success",
            "message": "Mock data synced successfully"
        }
        
    except Exception as e:
        update_sync_log(
            db,
            log.id,
            status='error',
            error_message=str(e)
        )
        return {
            "status": "error",
            "error": str(e)
        }
    finally:
        db.close()


if __name__ == '__main__':
    # Test sync
    result = sync_from_sheets()
    print(result)
