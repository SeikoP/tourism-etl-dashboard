#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import httpx
import json
import logging
import random
import time
import os
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
import re

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HotelDetailsExtractor:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'vi-VN,vi;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'Host': 'www.vietnambooking.com',
            'Referer': 'https://www.vietnambooking.com/',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Upgrade-Insecure-Requests': '1'
        }
        
        # Configuration
        self.batch_size = 50  # Process 50 hotels per batch
        self.delay_range = (1, 3)  # Faster for detail pages
        self.max_retries = 3
        
    async def fetch_page(self, url: str) -> str:
        """Fetch page with retry logic"""
        logger.debug(f"Fetching: {url}")
        
        for attempt in range(self.max_retries):
            try:
                await asyncio.sleep(random.uniform(*self.delay_range))
                
                async with httpx.AsyncClient(headers=self.headers, timeout=30) as client:
                    response = await client.get(url)
                    response.raise_for_status()
                    return response.text
                    
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(random.uniform(5, 10))
                
    def extract_rating(self, soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
        """Extract hotel rating/stars"""
        rating_info = {}
        
        # Look for star rating
        star_elements = soup.find_all(['div', 'span'], class_=re.compile(r'star|rating'))
        for elem in star_elements:
            text = elem.get_text(strip=True)
            if 'sao' in text.lower() or '★' in text:
                rating_info['stars'] = text
                break
        
        # Look for numeric rating
        rating_pattern = r'(\d+(?:\.\d+)?)\s*(?:/\s*\d+|điểm)'
        all_text = soup.get_text()
        rating_match = re.search(rating_pattern, all_text)
        if rating_match:
            rating_info['numeric_rating'] = rating_match.group(1)
        
        return rating_info if rating_info else None
    
    def extract_address(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract hotel address"""
        # Common address selectors
        address_selectors = [
            '[class*="address"]',
            '[class*="location"]',
            '[class*="map"]',
            '.hotel-info',
            '.detail-address'
        ]
        
        for selector in address_selectors:
            elements = soup.select(selector)
            for elem in elements:
                text = elem.get_text(strip=True)
                if len(text) > 20 and any(keyword in text.lower() for keyword in ['quận', 'huyện', 'thành phố', 'tp', 'đường', 'phố']):
                    return text[:200]  # Limit length
        
        # Fallback: look for address patterns in all text
        all_text = soup.get_text()
        address_patterns = [
            r'[^\n]*(?:quận|huyện|thành phố|tp\.?|đường|phố)[^\n]*',
            r'\d+[^\n]*(?:đường|phố)[^\n]*',
        ]
        
        for pattern in address_patterns:
            matches = re.findall(pattern, all_text, re.IGNORECASE)
            if matches:
                return matches[0].strip()[:200]
        
        return None
    
    def extract_price_info(self, soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
        """Extract price information"""
        price_info = {}
        
        # Look for price elements
        price_elements = soup.find_all(['div', 'span'], string=re.compile(r'VND|VNĐ|đ|\d+,\d+'))
        
        prices = []
        for elem in price_elements:
            text = elem.get_text(strip=True)
            # Extract numeric prices
            price_matches = re.findall(r'([\d,]+)(?:\s*(?:VND|VNĐ|đ))', text)
            for match in price_matches:
                try:
                    price_num = int(match.replace(',', ''))
                    if 50000 <= price_num <= 50000000:  # Valid hotel price range
                        prices.append(price_num)
                except:
                    continue
        
        if prices:
            price_info['min_price'] = min(prices)
            price_info['max_price'] = max(prices)
            price_info['avg_price'] = sum(prices) // len(prices)
            price_info['currency'] = 'VND'
        
        # Look for price labels
        price_labels = soup.find_all(string=re.compile(r'giá.*(?:từ|chỉ)|price.*from', re.IGNORECASE))
        if price_labels:
            price_info['price_label'] = price_labels[0].strip()[:100]
        
        return price_info if price_info else None
    
    def extract_amenities(self, soup: BeautifulSoup) -> List[str]:
        """Extract hotel amenities"""
        amenities = []
        
        # Common amenity keywords
        amenity_keywords = [
            'wifi', 'máy lạnh', 'điều hòa', 'tv', 'tivi', 'minibar', 'tủ lạnh',
            'phòng tắm', 'vòi sen', 'bồn tắm', 'ban công', 'view', 'hồ bơi',
            'gym', 'spa', 'massage', 'nhà hàng', 'quán bar', 'bãi đỗ xe',
            'đưa đón', 'reception', 'lễ tân', 'thang máy', 'không hút thuốc'
        ]
        
        # Look in amenity sections
        amenity_sections = soup.find_all(['div', 'ul'], class_=re.compile(r'amenity|facility|service'))
        for section in amenity_sections:
            text = section.get_text().lower()
            for keyword in amenity_keywords:
                if keyword in text and keyword not in amenities:
                    amenities.append(keyword)
        
        # Look for amenity icons or lists
        amenity_items = soup.find_all(['li', 'span'], string=re.compile('|'.join(amenity_keywords), re.IGNORECASE))
        for item in amenity_items[:10]:  # Limit to avoid noise
            text = item.get_text(strip=True)
            if len(text) < 50:  # Avoid long descriptions
                amenities.append(text)
        
        return list(set(amenities))[:15]  # Remove duplicates, limit to 15
    
    def extract_photos(self, soup: BeautifulSoup) -> List[str]:
        """Extract hotel photo URLs"""
        photos = []
        
        # Find image elements
        img_elements = soup.find_all('img')
        for img in img_elements:
            src = img.get('src') or img.get('data-src') or img.get('data-lazy')
            if src:
                # Filter for hotel photos (avoid icons, logos, etc.)
                if any(keyword in src.lower() for keyword in ['hotel', 'room', 'jpg', 'jpeg', 'png']) and \
                   not any(exclude in src.lower() for exclude in ['icon', 'logo', 'avatar', 'flag']):
                    if src.startswith('//'):
                        src = 'https:' + src
                    elif src.startswith('/'):
                        src = 'https://www.vietnambooking.com' + src
                    photos.append(src)
        
        return list(set(photos))[:10]  # Remove duplicates, limit to 10
    
    def extract_description(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract hotel description"""
        # Look for description sections
        desc_selectors = [
            '[class*="description"]',
            '[class*="about"]',
            '[class*="overview"]',
            '.hotel-detail',
            '.content'
        ]
        
        for selector in desc_selectors:
            elements = soup.select(selector)
            for elem in elements:
                text = elem.get_text(strip=True)
                if len(text) > 100:  # Meaningful description
                    return text[:1000]  # Limit length
        
        return None
    
    async def extract_hotel_details(self, hotel: Dict[str, Any]) -> Dict[str, Any]:
        """Extract detailed information for a single hotel"""
        
        try:
            html = await self.fetch_page(hotel['url'])
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract all details
            details = {
                'basic_info': {
                    'location_name': hotel['location_name'],
                    'location_code': hotel['location_code'],
                    'url': hotel['url'],
                    'name': hotel['name']
                },
                'rating': self.extract_rating(soup),
                'address': self.extract_address(soup),
                'price_info': self.extract_price_info(soup),
                'amenities': self.extract_amenities(soup),
                'photos': self.extract_photos(soup),
                'description': self.extract_description(soup),
                'extraction_date': time.strftime('%Y-%m-%d %H:%M:%S'),
                'extraction_success': True
            }
            
            logger.debug(f"Successfully extracted details for {hotel['name']}")
            return details
            
        except Exception as e:
            logger.error(f"Error extracting details for {hotel['name']} ({hotel['url']}): {e}")
            return {
                'basic_info': {
                    'location_name': hotel['location_name'],
                    'location_code': hotel['location_code'],
                    'url': hotel['url'],
                    'name': hotel['name']
                },
                'extraction_date': time.strftime('%Y-%m-%d %H:%M:%S'),
                'extraction_success': False,
                'error': str(e)
            }
    
    def save_batch_details(self, details: List[Dict[str, Any]], batch_idx: int, output_dir: str):
        """Save hotel details batch to file"""
        output_file = os.path.join(output_dir, f"hotel_details_batch_{batch_idx}.json")
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(details, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved {len(details)} hotel details to {output_file}")
        except Exception as e:
            logger.error(f"Error saving batch {batch_idx}: {e}")

async def process_hotels_for_details(hotels_file: str, output_dir: str, start_idx: int = 0, batch_size: int = 50):
    """Process hotels to extract detailed information"""
    
    # Load hotels
    with open(hotels_file, 'r', encoding='utf-8') as f:
        hotels = json.load(f)
    
    extractor = HotelDetailsExtractor()
    
    total_hotels = len(hotels)
    end_idx = min(start_idx + batch_size, total_hotels)
    
    logger.info(f"Processing hotel details {start_idx}-{end_idx-1} of {total_hotels}")
    
    batch_details = []
    
    for i in range(start_idx, end_idx):
        hotel = hotels[i]
        logger.info(f"Extracting details for hotel {i+1}/{total_hotels}: {hotel['name']}")
        
        details = await extractor.extract_hotel_details(hotel)
        batch_details.append(details)
        
        # Save progress every 10 hotels
        if (i - start_idx) % 10 == 9:
            batch_idx = start_idx // batch_size
            extractor.save_batch_details(batch_details, batch_idx, output_dir)
    
    # Save final batch
    batch_idx = start_idx // batch_size
    extractor.save_batch_details(batch_details, batch_idx, output_dir)
    
    logger.info(f"Completed details extraction for batch {start_idx}-{end_idx-1}: {len(batch_details)} hotels")
    return batch_details

if __name__ == "__main__":
    hotels_file = "data/raw/vietnambooking/all_hotels_enhanced.json"
    output_dir = "data/raw/vietnambooking/details/"
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Test with first 10 hotels
    batch_size = 10
    start_idx = 0
    
    print(f"Hotel Details Extractor - Testing Mode")
    print(f"Processing {batch_size} hotels starting from index {start_idx}")
    
    try:
        asyncio.run(process_hotels_for_details(hotels_file, output_dir, start_idx, batch_size))
    except KeyboardInterrupt:
        print("\nStopped by user")
    except Exception as e:
        print(f"Error: {e}")