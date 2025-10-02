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

        AMENITIES & FACILITIES (IMPORTANT - extract all you can find):
        - Swimming pool (hồ bơi)
        - Restaurant (nhà hàng)
        - WiFi / Internet
        - Parking (đỗ xe)
        - Spa/Massage (spa/thư giãn)
        - Fitness center/Gym (phòng gym)
        - Airport shuttle (đưa đón sân bay)
        - Room service (phục vụ phòng)
        - Laundry service (giặt ủi)
        - Business center (trung tâm hội nghị)
        - Conference facilities (phòng họp)
        - Bar/Lounge (quầy bar)
        - Garden (vườn)
        - Elevator (thang máy)
        - 24-hour front desk (lễ tân 24h)
        - Air conditioning (điều hòa)
        - Safe deposit box (két sắt)
        - Currency exchange (đổi tiền)
        - Tour desk (quầy tour)
        - Car rental (thuê xe)
        - Babysitting (trông trẻ)
        - Pets allowed (cho phép thú cưng)
        - Non-smoking rooms (phòng không hút thuốc)
        - Family rooms (phòng gia đình)
        - Any other amenities mentioned

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

        Return as structured JSON with these exact keys. For amenities, return as array of strings.
        If information is not available, use null or empty array.
        """

    async def extract_hotel_details_ai(self, hotel: Dict[str, Any]) -> Dict[str, Any]:
        """Extract detailed hotel information using hybrid approach: BeautifulSoup + AI"""

        try:
            # First, try AI extraction
            ai_result = await self._try_ai_extraction(hotel)

            # Always do basic extraction as fallback/primary method
            basic_result = await self._extract_basic_info(hotel)

            # Combine results: prefer AI data where available, fallback to basic
            combined_data = basic_result.copy() if basic_result else {}

            if ai_result:
                # Merge amenities from AI extraction (prioritize AI)
                if ai_result.get('amenities') and len(ai_result['amenities']) > 0:
                    combined_data['basic_amenities'] = ai_result['amenities']
                    logger.info(f"Using {len(ai_result['amenities'])} amenities from AI extraction")
                elif ai_result.get('complex_amenities') and len(ai_result['complex_amenities']) > 0:
                    # Fallback to complex_amenities if amenities not available
                    combined_data['basic_amenities'] = ai_result['complex_amenities']
                    logger.info(f"Using {len(ai_result['complex_amenities'])} complex amenities from AI extraction")

                # Add other AI-extracted fields
                if ai_result.get('description'):
                    combined_data['description'] = ai_result['description']
                if ai_result.get('room_descriptions'):
                    combined_data['room_descriptions'] = ai_result['room_descriptions']
                if ai_result.get('policies'):
                    combined_data['policies'] = ai_result['policies']
                if ai_result.get('nearby_attractions'):
                    combined_data['nearby_attractions'] = ai_result['nearby_attractions']

            # Ensure amenities is always an array
            if 'basic_amenities' not in combined_data:
                combined_data['basic_amenities'] = []
            elif not isinstance(combined_data['basic_amenities'], list):
                combined_data['basic_amenities'] = [combined_data['basic_amenities']]

            details = {
                'basic_info': {
                    'location_name': hotel['location_name'],
                    'location_code': hotel['location_code'],
                    'url': hotel['url'],
                    'name': hotel['name']
                },
                'extracted_data': combined_data,
                'extraction_method': 'hybrid_ai_beautifulsoup',
                'extraction_date': time.strftime('%Y-%m-%d %H:%M:%S'),
                'extraction_success': True,
                'ai_extraction_success': ai_result is not None,
                'basic_extraction_success': basic_result is not None
            }

            logger.info(f"Successfully extracted hybrid data for {hotel['name']}")
            return details

        except Exception as e:
            logger.error(f"Error in hybrid extraction for {hotel['name']}: {e}")
            # Final fallback - return basic info only
            try:
                basic_result = await self._extract_basic_info(hotel)
                return {
                    'basic_info': {
                        'location_name': hotel['location_name'],
                        'location_code': hotel['location_code'],
                        'url': hotel['url'],
                        'name': hotel['name']
                    },
                    'extracted_data': basic_result or {},
                    'extraction_method': 'basic_fallback_only',
                    'extraction_date': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'extraction_success': True,
                    'error': str(e)
                }
            except Exception as final_e:
                logger.error(f"Even basic extraction failed for {hotel['name']}: {final_e}")
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

    async def _check_crawl4ai_health(self) -> bool:
        """Check if Crawl4AI service is healthy and available"""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(f"{self.crawl4ai_url}/health")
                return response.status_code == 200
        except Exception:
            return False

    async def _try_ai_extraction(self, hotel: Dict[str, Any]) -> Dict[str, Any]:
        """Try AI extraction, return None if it fails"""

        try:
            # Check if Crawl4AI service is available first
            crawl4ai_available = await self._check_crawl4ai_health()
            if not crawl4ai_available:
                logger.warning(f"Crawl4AI service not available for {hotel['name']}")
                return None

            # Enhanced AI extraction for comprehensive hotel data
            payload = {
                "urls": [hotel['url']],
                "extraction_prompt": """
                Extract ALL hotel amenities and facilities from this Vietnamese hotel page.
                Look for these specific amenities (tiện ích):

                HOTEL AMENITIES (extract as many as possible):
                - WiFi (internet)
                - Hồ bơi (swimming pool)
                - Nhà hàng (restaurant)
                - Đỗ xe (parking)
                - Spa/Massage (spa)
                - Phòng gym/Fitness (gym)
                - Đưa đón sân bay (airport shuttle)
                - Phục vụ phòng (room service)
                - Giặt ủi (laundry)
                - Trung tâm hội nghị (business center)
                - Phòng họp (conference room)
                - Quầy bar (bar/lounge)
                - Vườn (garden)
                - Thang máy (elevator)
                - Lễ tân 24h (24h front desk)
                - Điều hòa (air conditioning)
                - Két sắt (safe deposit)
                - Đổi tiền (currency exchange)
                - Quầy tour (tour desk)
                - Thuê xe (car rental)
                - Trông trẻ (babysitting)
                - Cho phép thú cưng (pets allowed)
                - Phòng không hút thuốc (non-smoking)
                - Phòng gia đình (family rooms)
                - Bữa sáng (breakfast)
                - Máy pha trà/cà phê (coffee/tea maker)
                - TV (television)
                - Minibar (minibar)
                - Ban công (balcony)
                - Phòng tắm riêng (private bathroom)
                - Any other amenities you find

                Also extract:
                - Hotel description (mô tả khách sạn)
                - Room descriptions (mô tả phòng)
                - Policies (quy định)
                - Nearby attractions (địa điểm gần đó)

                Return as JSON with 'amenities' as array of strings, and other fields as appropriate.
                Be thorough - look in sidebars, facility lists, and descriptive text.
                """,
                "extraction_schema": {
                    "type": "object",
                    "properties": {
                        "amenities": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of all hotel amenities found"
                        },
                        "description": {"type": "string"},
                        "room_descriptions": {"type": "array", "items": {"type": "string"}},
                        "policies": {"type": "object"},
                        "nearby_attractions": {"type": "array", "items": {"type": "string"}},
                        "additional_info": {"type": "object"}
                    },
                    "required": ["amenities"]
                },
                "wait_for": 5,  # Give more time for complex pages
                "remove_overlay_elements": True,
                "word_count_threshold": 5,
                "css_selector": ".hotel-facilities, .amenities, .facilities, .services, .features, .hotel-details, .property-highlights",
                "only_text": False
            }

            async with httpx.AsyncClient(timeout=120) as client:
                response = await client.post(
                    f"{self.crawl4ai_url}/crawl",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )

                if response.status_code == 200:
                    result = response.json()

                    if 'results' in result and len(result['results']) > 0:
                        crawl_result = result['results'][0]
                        if 'extracted_content' in crawl_result and crawl_result['extracted_content']:
                            ai_data = crawl_result['extracted_content']
                            logger.info(f"AI extraction successful for {hotel['name']}")
                            return ai_data

            logger.warning(f"AI extraction returned empty/null for {hotel['name']}")
            return None

        except Exception as e:
            logger.warning(f"AI extraction failed for {hotel['name']}: {e}")
            return None

    async def _extract_basic_info(self, hotel: Dict[str, Any]) -> Dict[str, Any]:
        """Extract basic hotel information using BeautifulSoup"""

        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'vi-VN,vi;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Cache-Control': 'max-age=0',
                'Connection': 'keep-alive',
            }

            async with httpx.AsyncClient(headers=headers, timeout=30) as client:
                response = await client.get(hotel['url'])

            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract basic information
            data = {}

            # Hotel name
            h1 = soup.find('h1')
            data['hotel_name'] = h1.get_text(strip=True) if h1 else None

            # Address
            address_elem = soup.select_one('.hotel-address, .address, [itemprop="address"]')
            data['address'] = address_elem.get_text(strip=True) if address_elem else None

            # Phone
            phone_elem = soup.select_one('.phone, .contact-phone, .hotel-phone, a[href^="tel:"]')
            if phone_elem:
                if phone_elem.name == 'a' and phone_elem.get('href', '').startswith('tel:'):
                    data['phone'] = phone_elem.get('href', '').replace('tel:', '')
                else:
                    data['phone'] = phone_elem.get_text(strip=True)

            # Price with detailed analysis
            price_elem = soup.select_one('.price, .hotel-price, .rate, .price-range')
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                data['price_range'] = price_text

                # Extract detailed pricing information
                import re
                price_pattern = re.compile(r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(VNĐ|VND|đ|₫)?', re.IGNORECASE)
                price_matches = price_pattern.findall(price_text)

                if price_matches:
                    prices = []
                    for match in price_matches:
                        price_str, currency = match
                        price_numeric = float(price_str.replace(',', ''))
                        prices.append(price_numeric)

                    if prices:
                        data['price_analysis'] = {
                            'min_price': min(prices),
                            'max_price': max(prices),
                            'avg_price': sum(prices) / len(prices),
                            'price_count': len(prices),
                            'currency': 'VND',
                            'formatted_range': f"{min(prices):,.0f} - {max(prices):,.0f} VND"
                        }

            # Star rating
            star_elem = soup.select_one('.star-rating, .rating, .stars, [itemprop="ratingValue"]')
            data['star_rating'] = star_elem.get_text(strip=True) or star_elem.get('content') if star_elem else None

            # Meta description
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            data['meta_description'] = meta_desc.get('content') if meta_desc else None

            # Enhanced amenities extraction (multiple selectors for VietnamBooking)
            amenities = []
            amenity_selectors = [
                '.amenities li', '.facilities li', '.services li', '.features li',
                '.hotel-amenities li', '.property-amenities li', '.facility-list li',
                '.amenities .item', '.facilities .item', '.services .item',
                '.amenity-item', '.facility-item', '.service-item',
                '.hotel-features li', '.property-features li',
                '.amenities ul li', '.facilities ul li',
                '[class*="amenit"]', '[class*="facilit"]', '[class*="service"]',
                '.highlight-item', '.feature-item'
            ]

            for selector in amenity_selectors:
                elements = soup.select(selector)
                for elem in elements:
                    amenity = elem.get_text(strip=True)
                    if amenity and len(amenity) > 1 and len(amenity) < 100:  # Reasonable length
                        # Clean up common prefixes/suffixes
                        amenity = re.sub(r'^(✓|•|\*|\-)\s*', '', amenity)
                        amenity = re.sub(r'\s*(✓|•|\*|\-)$', '', amenity)

                        # Skip invalid amenities (room listings, etc.)
                        if self._is_valid_amenity(amenity):
                            if amenity and amenity not in amenities:
                                amenities.append(amenity)

            # Also look for amenities in text content
            text_content = soup.get_text()
            common_amenities = [
                'WiFi', 'wifi', 'internet', 'hồ bơi', 'swimming pool', 'pool',
                'nhà hàng', 'restaurant', 'đỗ xe', 'parking', 'spa', 'massage',
                'gym', 'fitness', 'phòng gym', 'đưa đón sân bay', 'airport shuttle',
                'phục vụ phòng', 'room service', 'giặt ủi', 'laundry',
                'trung tâm hội nghị', 'business center', 'phòng họp', 'conference',
                'quầy bar', 'bar', 'lounge', 'vườn', 'garden', 'thang máy', 'elevator',
                'lễ tân 24h', '24h front desk', 'điều hòa', 'air conditioning',
                'két sắt', 'safe', 'đổi tiền', 'currency exchange', 'quầy tour', 'tour desk'
            ]

            for amenity in common_amenities:
                if amenity.lower() in text_content.lower() and amenity not in amenities:
                    amenities.append(amenity)

            # Remove duplicates and limit
            amenities = list(set(amenities))[:30]  # Allow more amenities
            data['basic_amenities'] = amenities

            logger.info(f"Basic extraction successful for {hotel['name']}: {len(data)} fields, {len(amenities)} cleaned amenities")
            return data

        except Exception as e:
            logger.error(f"Basic extraction failed for {hotel['name']}: {e}")
            return {}

    def _is_valid_amenity(self, amenity: str) -> bool:
        """Check if text is a valid amenity (not room listing, etc.)"""

        if not amenity or len(amenity) < 2:
            return False

        amenity_lower = amenity.lower()

        # Blacklist patterns that indicate room listings or invalid content
        blacklist_patterns = [
            r'\+.*',  # Contains + followed by numbers (room codes like +42)
            r'\d{2,3}$',  # Ends with 2-3 digits (room numbers)
            r'Wifi.*\+',  # Wifi followed by + (room listing format)
            r'Máy lạnh.*\+',  # Air conditioning followed by +
            r'Phòng.*\+',  # Room followed by +
            r'\d+\s*phòng',  # Contains room count
            r'giá.*vnd',  # Price information
            r'\d{4,}',  # Long numbers (likely prices or codes)
            r'^\d+',  # Starts with numbers
            r'https?://',  # URLs
            r'@',  # Email addresses
            r'\+?\d{8,}',  # Phone numbers
        ]

        # Check against blacklist
        if any(re.search(pattern, amenity, re.IGNORECASE) for pattern in blacklist_patterns):
            return False

        # Valid amenities keywords (to prioritize real amenities)
        valid_amenity_keywords = [
            'wifi', 'internet', 'hồ bơi', 'pool', 'swimming', 'nhà hàng', 'restaurant',
            'đỗ xe', 'parking', 'spa', 'massage', 'gym', 'fitness', 'phòng gym',
            'đưa đón', 'airport', 'shuttle', 'phục vụ phòng', 'room service',
            'giặt ủi', 'laundry', 'trung tâm hội nghị', 'business center',
            'conference', 'phòng họp', 'bar', 'lounge', 'vườn', 'garden',
            'thang máy', 'elevator', 'lễ tân', 'reception', 'front desk',
            'điều hòa', 'air conditioning', 'két sắt', 'safe', 'đổi tiền', 'currency',
            'quầy tour', 'tour desk', 'thuê xe', 'car rental', 'trông trẻ', 'babysitting',
            'pets', 'thú cưng', 'không hút thuốc', 'non-smoking', 'gia đình', 'family',
            'bữa sáng', 'breakfast', 'coffee', 'tea', 'tv', 'television',
            'minibar', 'ban công', 'balcony', 'phòng tắm', 'bathroom', 'private bathroom',
            'máy pha trà', 'coffee maker', 'điều hòa nhiệt độ', 'air conditioning',
            'wifi miễn phí', 'free wifi', 'hồ bơi vô cực', 'infinity pool'
        ]

        # Check if it's a valid amenity
        is_valid = (
            len(amenity) <= 50 or  # Short amenities are likely valid
            any(keyword in amenity_lower for keyword in valid_amenity_keywords)
        )

        return is_valid

    async def _extract_basic_info(self, hotel: Dict[str, Any]) -> Dict[str, Any]:
        """Extract basic hotel information using BeautifulSoup"""

        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'vi-VN,vi;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Cache-Control': 'max-age=0',
                'Connection': 'keep-alive',
            }

            async with httpx.AsyncClient(headers=headers, timeout=30) as client:
                response = await client.get(hotel['url'])

            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract basic information
            data = {}

            # Hotel name
            h1 = soup.find('h1')
            data['hotel_name'] = h1.get_text(strip=True) if h1 else None

            # Address
            address_elem = soup.select_one('.hotel-address, .address, [itemprop="address"]')
            data['address'] = address_elem.get_text(strip=True) if address_elem else None

            # Phone
            phone_elem = soup.select_one('.phone, .contact-phone, .hotel-phone, a[href^="tel:"]')
            if phone_elem:
                if phone_elem.name == 'a' and phone_elem.get('href', '').startswith('tel:'):
                    data['phone'] = phone_elem.get('href', '').replace('tel:', '')
                else:
                    data['phone'] = phone_elem.get_text(strip=True)

            # Price with detailed analysis
            price_elem = soup.select_one('.price, .hotel-price, .rate, .price-range')
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                data['price_range'] = price_text

                # Extract detailed pricing information
                import re
                price_pattern = re.compile(r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(VNĐ|VND|đ|₫)?', re.IGNORECASE)
                price_matches = price_pattern.findall(price_text)

                if price_matches:
                    prices = []
                    for match in price_matches:
                        price_str, currency = match
                        price_numeric = float(price_str.replace(',', ''))
                        prices.append(price_numeric)

                    if prices:
                        data['price_analysis'] = {
                            'min_price': min(prices),
                            'max_price': max(prices),
                            'avg_price': sum(prices) / len(prices),
                            'price_count': len(prices),
                            'currency': 'VND',
                            'formatted_range': f"{min(prices):,.0f} - {max(prices):,.0f} VND"
                        }

            # Star rating
            star_elem = soup.select_one('.star-rating, .rating, .stars, [itemprop="ratingValue"]')
            data['star_rating'] = star_elem.get_text(strip=True) or star_elem.get('content') if star_elem else None

            # Meta description
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            data['meta_description'] = meta_desc.get('content') if meta_desc else None

            # Enhanced amenities extraction (multiple selectors for VietnamBooking)
            amenities = []
            amenity_selectors = [
                '.amenities li', '.facilities li', '.services li', '.features li',
                '.hotel-amenities li', '.property-amenities li', '.facility-list li',
                '.amenities .item', '.facilities .item', '.services .item',
                '.amenity-item', '.facility-item', '.service-item',
                '.hotel-features li', '.property-features li',
                '.amenities ul li', '.facilities ul li',
                '[class*="amenit"]', '[class*="facilit"]', '[class*="service"]',
                '.highlight-item', '.feature-item',
                # VietnamBooking specific selectors
                '.hotel-facility-list li', '.property-facilities li',
                '.amenities-section li', '.facilities-section li'
            ]

            for selector in amenity_selectors:
                elements = soup.select(selector)
                for elem in elements:
                    amenity = elem.get_text(strip=True)
                    if amenity and len(amenity) > 1 and len(amenity) < 100:  # Reasonable length
                        # Clean up common prefixes/suffixes
                        amenity = re.sub(r'^(✓|•|\*|\-)\s*', '', amenity)
                        amenity = re.sub(r'\s*(✓|•|\*|\-)$', '', amenity)

                        # Skip invalid amenities (room listings, etc.)
                        if self._is_valid_amenity(amenity):
                            if amenity and amenity not in amenities:
                                amenities.append(amenity)

            # Also look for amenities in text content
            text_content = soup.get_text()
            common_amenities = [
                'WiFi', 'wifi', 'internet', 'hồ bơi', 'swimming pool', 'pool',
                'nhà hàng', 'restaurant', 'đỗ xe', 'parking', 'spa', 'massage',
                'gym', 'fitness', 'phòng gym', 'đưa đón sân bay', 'airport shuttle',
                'phục vụ phòng', 'room service', 'giặt ủi', 'laundry',
                'trung tâm hội nghị', 'business center', 'phòng họp', 'conference',
                'quầy bar', 'bar', 'lounge', 'vườn', 'garden', 'thang máy', 'elevator',
                'lễ tân 24h', '24h front desk', 'điều hòa', 'air conditioning',
                'két sắt', 'safe', 'đổi tiền', 'currency exchange', 'quầy tour', 'tour desk'
            ]

            for amenity in common_amenities:
                if amenity.lower() in text_content.lower() and amenity not in amenities:
                    amenities.append(amenity)

            # Remove duplicates and limit
            amenities = list(set(amenities))[:30]  # Allow more amenities
            data['basic_amenities'] = amenities

            logger.info(f"Basic extraction successful for {hotel['name']}: {len(data)} fields, {len(amenities)} cleaned amenities")
            return data

        except Exception as e:
            logger.error(f"Basic extraction failed for {hotel['name']}: {e}")
            return {}
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