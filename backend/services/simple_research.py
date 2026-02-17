#!/usr/bin/env python3
"""
Simple Brand Research - No Selenium required
Uses requests and BeautifulSoup only
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import re

def research_website_simple(url):
    """
    Simple website research using requests + BeautifulSoup
    No Selenium/Chrome required
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract title
        title = soup.title.string.strip() if soup.title else ""
        
        # Extract meta description
        description = ""
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            description = meta_desc.get('content', '')
        
        # Extract brand name from title or URL
        brand_name = extract_brand_name(title, url)
        
        # Look for social links
        social_links = {
            'instagram': find_social_link(soup, 'instagram'),
            'tiktok': find_social_link(soup, 'tiktok'),
            'twitter': find_social_link(soup, 'twitter'),
            'facebook': find_social_link(soup, 'facebook')
        }
        
        # Extract category keywords from content
        category = guess_category(soup.get_text())
        
        return {
            'success': True,
            'brand_name': brand_name,
            'website': url,
            'title': title,
            'description': description[:200],
            'category': category,
            'social_links': social_links
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def extract_brand_name(title, url):
    """Extract brand name from title or URL"""
    # Try to get from title first
    if title:
        # Remove common suffixes
        name = re.sub(r'\s*[-|]\s*(Home|Official|Website).*$', '', title, flags=re.IGNORECASE)
        name = name.strip()
        if name and len(name) > 2:
            return name
    
    # Fall back to domain name
    domain = urlparse(url).netloc
    domain = domain.replace('www.', '')
    domain = domain.split('.')[0]
    return domain.capitalize()

def find_social_link(soup, platform):
    """Find social media link for a platform"""
    patterns = {
        'instagram': r'instagram\.com/([^/?&"\']+)',
        'tiktok': r'tiktok\.com/@([^/?&"\']+)',
        'twitter': r'twitter\.com/([^/?&"\']+)',
        'facebook': r'facebook\.com/([^/?&"\']+)'
    }
    
    # Search in all links
    for link in soup.find_all('a', href=True):
        href = link['href']
        match = re.search(patterns.get(platform, ''), href)
        if match:
            handle = match.group(1)
            # Filter out common non-handle paths
            if handle and handle not in ['home', 'pages', 'groups', 'events']:
                return handle
    
    return None

def guess_category(text):
    """Guess category from website text"""
    text_lower = text.lower()
    
    categories = {
        'beverage': ['drink', 'beverage', 'water', 'juice', 'soda', 'tea', 'coffee', 'energy drink'],
        'food': ['food', 'snack', 'organic', 'natural food'],
        'supplements': ['supplement', 'vitamin', 'protein', 'nutrition'],
        'personal_care': ['beauty', 'skincare', 'personal care', 'cosmetics'],
        'health': ['health', 'wellness', 'fitness']
    }
    
    for category, keywords in categories.items():
        if any(keyword in text_lower for keyword in keywords):
            return category.replace('_', ' ').title()
    
    return 'Beverage'

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        url = sys.argv[1]
        result = research_website_simple(url)
        import json
        print(json.dumps(result, indent=2))
    else:
        print("Usage: python simple_research.py <website_url>")
