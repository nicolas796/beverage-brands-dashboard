"""
TikTok API integration using RapidAPI (apibox TikTok API)
Rate limits: 1000 req/hour, 100/month
"""
import os
import time
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass
import requests

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Rate limit configuration
TIKTOK_RATE_LIMIT_HOURLY = 1000
TIKTOK_RATE_LIMIT_MONTHLY = 100

# RapidAPI configuration
RAPIDAPI_KEY = os.getenv('RAPIDAPI_KEY', '29224a2606msh79c9dc264c77b53p1c3dcbjsn81eef776109f')
TIKTOK_API_HOST = "tiktok-api23.p.rapidapi.com"

# In-memory rate limit tracking
class RateLimiter:
    """Simple rate limiter for TikTok API"""
    
    def __init__(self, hourly_limit: int = 1000, monthly_limit: int = 100):
        self.hourly_limit = hourly_limit
        self.monthly_limit = monthly_limit
        self.requests_this_hour = []
        self.requests_this_month = []
        self._cleanup_old_requests()
    
    def _cleanup_old_requests(self):
        """Remove expired request timestamps"""
        now = datetime.utcnow()
        hour_ago = now - timedelta(hours=1)
        month_ago = now - timedelta(days=30)
        
        self.requests_this_hour = [t for t in self.requests_this_hour if t > hour_ago]
        self.requests_this_month = [t for t in self.requests_this_month if t > month_ago]
    
    def can_make_request(self) -> Tuple[bool, Optional[str]]:
        """Check if a request can be made under rate limits"""
        self._cleanup_old_requests()
        
        if len(self.requests_this_hour) >= self.hourly_limit:
            # Calculate wait time until next hour slot
            if self.requests_this_hour:
                oldest = min(self.requests_this_hour)
                wait_seconds = 3600 - (datetime.utcnow() - oldest).total_seconds()
                return False, f"Hourly rate limit exceeded. Wait {int(wait_seconds)} seconds"
            return False, "Hourly rate limit exceeded"
        
        if len(self.requests_this_month) >= self.monthly_limit:
            # Calculate wait time until next month
            return False, "Monthly rate limit exceeded (100 requests/month)"
        
        return True, None
    
    def record_request(self):
        """Record that a request was made"""
        now = datetime.utcnow()
        self.requests_this_hour.append(now)
        self.requests_this_month.append(now)


# Global rate limiter instance
tiktok_rate_limiter = RateLimiter(TIKTOK_RATE_LIMIT_HOURLY, TIKTOK_RATE_LIMIT_MONTHLY)


@dataclass
class TikTokUserInfo:
    """TikTok user data structure"""
    username: str
    nickname: str
    followers: int
    following: int
    likes: int
    video_count: int
    bio: str
    verified: bool
    profile_pic_url: str
    fetched_at: datetime
    raw_data: Optional[Dict] = None


class TikTokAPIError(Exception):
    """Custom exception for TikTok API errors"""
    pass


class TikTokAPI:
    """TikTok API client using RapidAPI"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or RAPIDAPI_KEY
        self.base_url = f"https://{TIKTOK_API_HOST}"
        self.headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": TIKTOK_API_HOST,
            "Accept": "application/json"
        }
        self.rate_limiter = tiktok_rate_limiter
    
    def _make_request(self, endpoint: str, params: Dict[str, Any] = None, retries: int = 2) -> Dict:
        """Make authenticated request to TikTok API"""
        # Check rate limits
        can_request, error_msg = self.rate_limiter.can_make_request()
        if not can_request:
            raise TikTokAPIError(f"Rate limit exceeded: {error_msg}")
        
        url = f"{self.base_url}/{endpoint}"
        
        for attempt in range(retries + 1):
            try:
                response = requests.get(
                    url,
                    headers=self.headers,
                    params=params,
                    timeout=30
                )
                
                # Record the request
                self.rate_limiter.record_request()
                
                # Handle specific HTTP errors
                if response.status_code == 429:
                    raise TikTokAPIError("Rate limit exceeded (429 from API)")
                elif response.status_code == 404:
                    raise TikTokAPIError(f"User not found (404)")
                elif response.status_code == 401:
                    raise TikTokAPIError("Invalid API key (401)")
                
                response.raise_for_status()
                
                data = response.json()
                
                # Check for API-level errors
                if isinstance(data, dict) and data.get('status') == 'error':
                    raise TikTokAPIError(f"API Error: {data.get('message', 'Unknown error')}")
                
                return data
                
            except requests.exceptions.Timeout:
                if attempt < retries:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.warning(f"Request timeout, retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    raise TikTokAPIError("Request timeout after retries")
                    
            except requests.exceptions.RequestException as e:
                if attempt < retries:
                    wait_time = 2 ** attempt
                    logger.warning(f"Request error: {e}, retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    raise TikTokAPIError(f"Request failed: {str(e)}")
        
        raise TikTokAPIError("Unexpected error in request")
    
    def get_user_info(self, username: str) -> TikTokUserInfo:
        """
        Fetch user information by username
        
        Args:
            username: TikTok username (without @)
            
        Returns:
            TikTokUserInfo object with user data
            
        Raises:
            TikTokAPIError: If API request fails or user not found
        """
        # Remove @ if present
        username = username.lstrip('@')
        
        logger.info(f"Fetching TikTok user info for: {username}")
        
        # API endpoint for user info - uses 'uniqueId' parameter
        endpoint = "api/user/info"
        params = {
            "uniqueId": username
        }
        
        try:
            data = self._make_request(endpoint, params)
            
            # Parse response from tiktok-api23 (apibox)
            # Response structure: {"userInfo": {"user": {...}, "stats": {...}}}
            user_info_data = data.get('userInfo', {})
            user_data = user_info_data.get('user', {})
            stats = user_info_data.get('stats', {})
            
            # Extract user info with safe defaults
            user_info = TikTokUserInfo(
                username=username,
                nickname=user_data.get('nickname', ''),
                followers=self._parse_number(stats.get('followerCount', 0)),
                following=self._parse_number(stats.get('followingCount', 0)),
                likes=self._parse_number(stats.get('heartCount', stats.get('heart', 0))),
                video_count=self._parse_number(stats.get('videoCount', 0)),
                bio=user_data.get('signature', ''),
                verified=user_data.get('verified', False),
                profile_pic_url=user_data.get('avatarThumb', ''),
                fetched_at=datetime.utcnow(),
                raw_data=data
            )
            
            logger.info(f"Successfully fetched TikTok user: {username} "
                       f"({user_info.followers:,} followers, {user_info.video_count} videos)")
            
            return user_info
            
        except TikTokAPIError:
            raise
        except Exception as e:
            logger.error(f"Error parsing TikTok API response: {e}")
            raise TikTokAPIError(f"Failed to parse user data: {str(e)}")
    
    def _parse_number(self, value: Any) -> int:
        """Safely parse a number value"""
        if value is None:
            return 0
        if isinstance(value, (int, float)):
            return int(value)
        if isinstance(value, str):
            # Handle shorthand notation like "1.2M" or "5K"
            value = value.upper().replace(',', '').strip()
            try:
                if 'M' in value:
                    return int(float(value.replace('M', '')) * 1_000_000)
                if 'K' in value:
                    return int(float(value.replace('K', '')) * 1_000)
                return int(value)
            except ValueError:
                return 0
        return 0
    
    def get_rate_limit_status(self) -> Dict[str, Any]:
        """Get current rate limit status"""
        self.rate_limiter._cleanup_old_requests()
        
        return {
            "hourly_limit": self.rate_limiter.hourly_limit,
            "hourly_used": len(self.rate_limiter.requests_this_hour),
            "hourly_remaining": self.rate_limiter.hourly_limit - len(self.rate_limiter.requests_this_hour),
            "monthly_limit": self.rate_limiter.monthly_limit,
            "monthly_used": len(self.rate_limiter.requests_this_month),
            "monthly_remaining": self.rate_limiter.monthly_limit - len(self.rate_limiter.requests_this_month),
        }


# Convenience function for direct use
def get_tiktok_user(username: str, api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Convenience function to fetch TikTok user info
    
    Args:
        username: TikTok username
        api_key: Optional API key (uses env var if not provided)
        
    Returns:
        Dictionary with user data or error info
    """
    api = TikTokAPI(api_key)
    
    try:
        user_info = api.get_user_info(username)
        return {
            "success": True,
            "username": user_info.username,
            "nickname": user_info.nickname,
            "followers": user_info.followers,
            "following": user_info.following,
            "likes": user_info.likes,
            "video_count": user_info.video_count,
            "bio": user_info.bio,
            "verified": user_info.verified,
            "profile_pic_url": user_info.profile_pic_url,
            "fetched_at": user_info.fetched_at.isoformat()
        }
    except TikTokAPIError as e:
        logger.error(f"TikTok API error for @{username}: {e}")
        return {
            "success": False,
            "error": str(e),
            "username": username
        }
    except Exception as e:
        logger.error(f"Unexpected error for @{username}: {e}")
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "username": username
        }


# Test function
if __name__ == "__main__":
    # Test with a known account
    test_username = "celsiusofficial"
    result = get_tiktok_user(test_username)
    print(json.dumps(result, indent=2))
    
    # Print rate limit status
    api = TikTokAPI()
    print("\nRate limit status:")
    print(json.dumps(api.get_rate_limit_status(), indent=2))
