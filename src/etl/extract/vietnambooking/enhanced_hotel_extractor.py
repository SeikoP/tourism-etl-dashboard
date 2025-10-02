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

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedHotelExtractor:
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
            'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1'
        }
        
        # Configuration - Fast mode for development
        self.batch_size = 5
        self.delay_range = (0.5, 1.0)  # Much faster for development
        self.max_retries = 3
        self.current_batch_hotels = []
        
    async def fetch_page(self, url: str) -> str:
        """Fetch page with retry logic"""
        logger.info(f"Fetching: {url}")
        
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
                
    async def extract_hotels_from_page(self, location_data: Dict[str, Any], page_url: str = None) -> List[Dict[str, Any]]:
        """Extract hotels from a single page with LESS STRICT filtering"""
        
        url = page_url if page_url else location_data['url']
        current_location_code = location_data['code']
        
        try:
            html = await self.fetch_page(url)
            soup = BeautifulSoup(html, 'html.parser')
            
            # Find all hotel links - MORE PERMISSIVE
            all_links = soup.find_all('a', href=True)
            hotel_links = [a for a in all_links if '/hotel/vietnam/' in a.get('href', '')]
            
            logger.info(f"Found {len(hotel_links)} hotel links on page")
            
            hotels = []
            seen_urls = set()
            
            for link in hotel_links:
                href = link.get('href', '')
                
                # Skip duplicates
                if href in seen_urls:
                    continue
                seen_urls.add(href)
                
                # LESS STRICT filtering - only exclude obvious wrong locations
                # Skip only if URL explicitly mentions another major city
                major_cities = ['ha-noi', 'ho-chi-minh', 'da-nang', 'nha-trang', 'da-lat', 'hoi-an', 'sapa', 'phu-quoc']
                is_wrong_city = False
                
                for city in major_cities:
                    if city != current_location_code and f'khach-san-{city}' in href:
                        is_wrong_city = True
                        break
                        
                if is_wrong_city:
                    continue
                
                # Get hotel name - MORE FLEXIBLE
                hotel_name = link.get_text(strip=True)
                
                # Skip empty names or very short ones
                if not hotel_name or len(hotel_name) < 2:
                    continue
                    
                # Skip only very obvious generic names
                if hotel_name.lower() in ['khách sạn', 'hotel', 'resort']:
                    continue
                
                # Create simplified hotel object with only essential fields
                hotel = {
                    'location_name': location_data['location_name'],
                    'location_code': location_data['code'],
                    'url': href,
                    'name': hotel_name
                }
                hotels.append(hotel)
            
            # Check for pagination - Skip for now to avoid issues
            pagination_links = []
            # Disable pagination to focus on single page extraction
            # page_links = soup.find_all('a', href=True)
            # for link in page_links:
            #     href = link.get('href', '')
            #     text = link.get_text(strip=True)
            #     # Look for pagination patterns
            #     if any(pattern in href for pattern in ['page=', '/page/', 'p=']):
            #         pagination_links.append(href)
            #     elif text.isdigit() and int(text) > 1:  # Page numbers
            #         pagination_links.append(href)
                    
            if pagination_links:
                logger.info(f"Found {len(pagination_links)} pagination links")
            
            logger.info(f"Extracted {len(hotels)} hotels from {len(hotel_links)} total links")
            return hotels, pagination_links
            
        except Exception as e:
            logger.error(f"Error extracting hotels for {location_data['location_name']}: {e}")
            return [], []
    
    async def extract_all_pages_for_location(self, location_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract hotels from all pages of a location"""
        
        all_hotels = []
        processed_urls = set()
        
        # Start with main page
        hotels, pagination_links = await self.extract_hotels_from_page(location_data)
        all_hotels.extend(hotels)
        processed_urls.add(location_data['url'])
        
        # Process pagination if exists
        for page_url in pagination_links[:5]:  # Limit to first 5 pages
            if page_url in processed_urls:
                continue
                
            processed_urls.add(page_url)
            
            # Make absolute URL
            if not page_url.startswith('http'):
                page_url = f"https://www.vietnambooking.com{page_url}"
            
            try:
                page_hotels, _ = await self.extract_hotels_from_page(location_data, page_url)
                all_hotels.extend(page_hotels)
                logger.info(f"Added {len(page_hotels)} hotels from page: {page_url}")
            except Exception as e:
                logger.error(f"Error processing page {page_url}: {e}")
                continue
        
        return all_hotels
    
    async def process_location(self, location_data: Dict[str, Any], max_retries: int = 3) -> List[Dict[str, Any]]:
        """Process a single location with retry logic"""
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Processing {location_data['location_name']} (attempt {attempt + 1})")
                
                hotels = await self.extract_all_pages_for_location(location_data)
                
                logger.info(f"Found {len(hotels)} hotels for {location_data['location_name']}")
                return hotels
                
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed for {location_data['location_name']}: {e}")
                if attempt == max_retries - 1:
                    logger.error(f"Failed to process {location_data['location_name']} after {max_retries} attempts")
                    return []
                await asyncio.sleep(random.uniform(10, 20))
        
        return []

    def save_progress(self, hotels: List[Dict[str, Any]], output_file: str):
        """Save hotels to JSON file"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(hotels, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved progress: {len(hotels)} hotels to {output_file}")
        except Exception as e:
            logger.error(f"Error saving to {output_file}: {e}")

async def process_locations_batch_enhanced(locations_file: str, output_dir: str, start_idx: int = 0, batch_size: int = 5):
    """Process locations with enhanced extraction"""
    
    # Load locations
    with open(locations_file, 'r', encoding='utf-8') as f:
        locations = json.load(f)
    
    extractor = EnhancedHotelExtractor()
    
    end_idx = min(start_idx + batch_size, len(locations))
    logger.info(f"Processing locations {start_idx}-{end_idx-1} of {len(locations)}")
    
    all_hotels = []
    
    for i in range(start_idx, end_idx):
        location = locations[i]
        logger.info(f"Processing location {i+1}/{len(locations)}: {location['location_name']}")
        
        hotels = await extractor.process_location(location)
        all_hotels.extend(hotels)
        
        # Save progress after each location
        output_file = os.path.join(output_dir, f"enhanced_hotels_batch_{start_idx}_{end_idx}.json")
        extractor.save_progress(all_hotels, output_file)
    
    logger.info(f"Completed batch {start_idx}-{end_idx-1}: {len(all_hotels)} total hotels")
    return all_hotels

if __name__ == "__main__":
    locations_file = "data/raw/vietnambooking/locations.json"
    output_dir = "data/raw/vietnambooking/"
    
    # Process more locations
    batch_size = 10
    start_idx = 3  # Continue from where we left off
    
    print(f"Enhanced Hotel Extractor - Testing Mode")
    print(f"Batch size: {batch_size}")
    
    try:
        asyncio.run(process_locations_batch_enhanced(locations_file, output_dir, start_idx, batch_size))
    except KeyboardInterrupt:
        print("\nStopped by user")
    except Exception as e:
        print(f"Error: {e}")