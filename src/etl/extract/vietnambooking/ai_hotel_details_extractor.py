#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import httpx
import json
import logging
import random
import time
import os
from typing import List, Dict, Any, Optional
import re

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIHotelDetailsExtractor:
    def __init__(self):
        self.crawl4ai_url = "http://crawl4ai:11235"  # Internal Docker network
        self.external_crawl4ai_url = "http://localhost:11235"  # For external access

        # Configuration for AI-powered extraction
        self.batch_size = 10  # Smaller batches for AI processing
        self.delay_range = (0.5, 1.0)  # Faster processing with AI
        self.max_retries = 3

        # AI extraction prompt for hotel details
        self.extraction_prompt = """
        Extract comprehensive hotel information from this Vietnamese hotel booking page.
        Focus on these key details:

        BASIC INFO:
        - Hotel name (tên khách sạn)
        - Full address (địa chỉ đầy đủ)
        - Star rating (số sao)
        - Contact phone (số điện thoại)
        - Email address

        PRICING:
        - Price range (khoảng giá)
        - Currency (đơn vị tiền tệ)
        - Room types available (loại phòng)

        AMENITIES & FACILITIES:
        - Swimming pool (hồ bơi)
        - Restaurant (nhà hàng)
        - WiFi
        - Parking (đỗ xe)
        - Spa/Fitness
        - Other facilities (cơ sở vật chất khác)

        LOCATION & TRANSPORT:
        - Distance to airport (khoảng cách đến sân bay)
        - Distance to city center (khoảng cách đến trung tâm)
        - Nearby attractions (địa điểm tham quan gần đó)

        POLICIES:
        - Check-in/check-out times (giờ nhận/trả phòng)
        - Cancellation policy (chính sách hủy phòng)
        - Pet policy (chính sách thú cưng)

        DESCRIPTION:
        - Hotel description (mô tả khách sạn)
        - Room descriptions (mô tả phòng)

        Return as structured JSON with these exact keys. If information is not available, use null.
        """

    async def extract_hotel_details_ai(self, hotel: Dict[str, Any]) -> Dict[str, Any]:
        """Extract detailed hotel information using AI-powered Crawl4AI"""

        try:
            # Prepare AI extraction request
            payload = {
                "url": hotel['url'],
                "extraction_prompt": self.extraction_prompt,
                "extraction_schema": {
                    "type": "object",
                    "properties": {
                        "hotel_name": {"type": "string"},
                        "full_address": {"type": "string"},
                        "star_rating": {"type": ["number", "null"]},
                        "contact_phone": {"type": "string"},
                        "email": {"type": "string"},
                        "price_range": {"type": "string"},
                        "currency": {"type": "string"},
                        "room_types": {"type": "array", "items": {"type": "string"}},
                        "amenities": {"type": "array", "items": {"type": "string"}},
                        "location_info": {
                            "type": "object",
                            "properties": {
                                "distance_to_airport": {"type": "string"},
                                "distance_to_city_center": {"type": "string"},
                                "nearby_attractions": {"type": "array", "items": {"type": "string"}}
                            }
                        },
                        "policies": {
                            "type": "object",
                            "properties": {
                                "check_in_time": {"type": "string"},
                                "check_out_time": {"type": "string"},
                                "cancellation_policy": {"type": "string"},
                                "pet_policy": {"type": "string"}
                            }
                        },
                        "description": {"type": "string"},
                        "room_descriptions": {"type": "array", "items": {"type": "string"}}
                    }
                },
                "wait_for": 5,  # Wait for dynamic content
                "remove_overlay_elements": True,  # Remove popups/modals
                "bypass_css": True,  # Better content extraction
                "word_count_threshold": 10  # Minimum content length
            }

            # Try internal Docker network first, then external
            urls_to_try = [self.crawl4ai_url, self.external_crawl4ai_url]

            for crawl_url in urls_to_try:
                try:
                    logger.info(f"Extracting details for {hotel['name']} using AI from {crawl_url}")

                    async with httpx.AsyncClient(timeout=180) as client:
                        response = await client.post(
                            f"{crawl_url}/crawl",
                            json=payload,
                            headers={"Content-Type": "application/json"}
                        )

                        if response.status_code == 200:
                            result = response.json()

                            # Extract the AI-parsed content
                            if 'result' in result and 'extracted_content' in result['result']:
                                ai_data = result['result']['extracted_content']

                                # Structure the response
                                details = {
                                    'basic_info': {
                                        'location_name': hotel['location_name'],
                                        'location_code': hotel['location_code'],
                                        'url': hotel['url'],
                                        'name': hotel['name']
                                    },
                                    'ai_extracted_data': ai_data,
                                    'extraction_method': 'ai_crawl4ai',
                                    'extraction_date': time.strftime('%Y-%m-%d %H:%M:%S'),
                                    'extraction_success': True,
                                    'crawl4ai_url': crawl_url
                                }

                                logger.info(f"Successfully extracted AI details for {hotel['name']}")
                                return details

                except Exception as e:
                    logger.warning(f"Failed with {crawl_url}: {e}")
                    continue

            # Fallback to basic extraction if AI fails
            logger.warning(f"AI extraction failed for {hotel['name']}, falling back to basic extraction")
            return await self.extract_hotel_details_basic(hotel)

        except Exception as e:
            logger.error(f"Error in AI extraction for {hotel['name']}: {e}")
            return await self.extract_hotel_details_basic(hotel)

    async def extract_hotel_details_basic(self, hotel: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback basic extraction without AI"""

        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            async with httpx.AsyncClient(headers=headers, timeout=30) as client:
                response = await client.get(hotel['url'])
                html = response.text

            # Basic parsing (simplified version)
            details = {
                'basic_info': {
                    'location_name': hotel['location_name'],
                    'location_code': hotel['location_code'],
                    'url': hotel['url'],
                    'name': hotel['name']
                },
                'ai_extracted_data': None,
                'extraction_method': 'basic_fallback',
                'extraction_date': time.strftime('%Y-%m-%d %H:%M:%S'),
                'extraction_success': True,
                'error': 'AI extraction failed, used basic fallback'
            }

            return details

        except Exception as e:
            logger.error(f"Basic extraction also failed for {hotel['name']}: {e}")
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

    async def process_hotels_batch(self, hotels: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process a batch of hotels using AI extraction"""

        logger.info(f"Processing {len(hotels)} hotels with AI extraction")

        # Add delay between requests to be respectful
        delay = random.uniform(*self.delay_range)

        tasks = []
        for hotel in hotels:
            tasks.append(self.extract_hotel_details_ai(hotel))
            await asyncio.sleep(delay)

        # Execute all tasks concurrently but with controlled concurrency
        semaphore = asyncio.Semaphore(3)  # Limit concurrent AI requests

        async def limited_extract(hotel):
            async with semaphore:
                return await self.extract_hotel_details_ai(hotel)

        results = []
        for hotel in hotels:
            result = await limited_extract(hotel)
            results.append(result)

        successful = sum(1 for r in results if r.get('extraction_success', False))
        logger.info(f"Successfully extracted {successful}/{len(hotels)} hotels using AI")

        return results

    def save_batch_details(self, details: List[Dict[str, Any]], batch_idx: int, output_dir: str):
        """Save hotel details batch to file"""

        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, f"ai_hotel_details_batch_{batch_idx}.json")

        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(details, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved {len(details)} AI-extracted hotel details to {output_file}")
        except Exception as e:
            logger.error(f"Error saving AI batch {batch_idx}: {e}")

async def process_hotels_with_ai(hotels_file: str, output_dir: str, start_idx: int = 0, batch_size: int = 10):
    """Process hotels using AI-powered extraction"""

    # Load hotels
    with open(hotels_file, 'r', encoding='utf-8') as f:
        hotels = json.load(f)

    extractor = AIHotelDetailsExtractor()

    total_hotels = len(hotels)
    end_idx = min(start_idx + batch_size, total_hotels)
    batch_hotels = hotels[start_idx:end_idx]

    logger.info(f"Processing AI hotel details {start_idx}-{end_idx-1} of {total_hotels}")

    # Process batch with AI
    details = await extractor.process_hotels_batch(batch_hotels)

    # Save results
    batch_idx = start_idx // batch_size
    extractor.save_batch_details(details, batch_idx, output_dir)

    return details

if __name__ == "__main__":
    # Example usage
    asyncio.run(process_hotels_with_ai(
        hotels_file="data/processed/vietnambooking/all_hotels_enhanced.json",
        output_dir="data/processed/vietnambooking/details",
        start_idx=0,
        batch_size=5
    ))