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

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Import Groq client
from groq import Groq

# Import BeautifulSoup for HTML parsing
from bs4 import BeautifulSoup

# Import rate limiter
from src.utils.ai_rate_limiter import make_ai_request_with_rate_limit

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIHotelDetailsExtractor:
    def __init__(self):
        # Detect if running inside Docker or external
        self.is_in_docker = os.path.exists('/.dockerenv') or os.environ.get('CRAWL4AI_IN_DOCKER') == 'true'

        if self.is_in_docker:
            self.crawl4ai_url = "http://crawl4ai:11234"  # Internal Docker network
        else:
            self.crawl4ai_url = "http://localhost:11235"  # External access

        logger.info(f"AIHotelDetailsExtractor initialized - Docker: {self.is_in_docker}, URL: {self.crawl4ai_url}")

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

            # Extract nearby places from the same HTML content used for basic info
            # We need to re-fetch since _extract_basic_info doesn't return soup
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'vi-VN,vi;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Cache-Control': 'max-age=0',
                'Connection': 'keep-alive',
            }

            try:
                async with httpx.AsyncClient(headers=headers, timeout=30, follow_redirects=True) as client:
                    response = await client.get(hotel['url'])

                soup = BeautifulSoup(response.text, 'html.parser')
                nearby_places = self._extract_nearby_places(soup)
                if nearby_places:
                    logger.info(f"Extracted {len(nearby_places)} nearby places for {hotel['name']}")
            except Exception as e:
                logger.error(f"Error fetching HTML for nearby places: {e}")
                nearby_places = []

            # Combine results: prefer AI data where available, fallback to basic
            combined_data = basic_result.copy() if basic_result else {}

            # Add nearby places to combined data
            if nearby_places:
                combined_data['nearby_places'] = nearby_places

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
        """Try AI extraction using direct Groq API, return None if it fails"""

        try:
            # Get Groq API key from environment
            api_key = os.getenv('GROQ_API_KEY')
            if not api_key:
                logger.warning(f"Groq API key not found for {hotel['name']}")
                return None

            # First, fetch the HTML content of the hotel page
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'vi-VN,vi;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Cache-Control': 'max-age=0',
                'Connection': 'keep-alive',
            }

            async with httpx.AsyncClient(headers=headers, timeout=30, follow_redirects=True) as client:
                response = await client.get(hotel['url'])
                if response.status_code != 200:
                    logger.warning(f"Failed to fetch HTML for {hotel['name']}: {response.status_code}")
                    return None

                html_content = response.text
                logger.info(f"Fetched HTML content for {hotel['name']}: {len(html_content)} characters")

            # Initialize Groq client
            client = Groq(api_key=api_key)

            # Create extraction prompt with HTML content
            extraction_prompt = f"""
            Extract ALL hotel amenities and facilities from this Vietnamese hotel page HTML content.
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

            HTML CONTENT:
            {html_content[:8000]}  # Limit content to avoid token limits

            Return ONLY valid JSON with this exact structure:
            {{
                "amenities": ["amenity1", "amenity2", ...],
                "description": "hotel description text",
                "room_descriptions": ["room desc 1", "room desc 2"],
                "policies": ["policy 1", "policy 2"],
                "nearby_attractions": ["attraction 1", "attraction 2"]
            }}

            Return ONLY valid JSON without any markdown formatting, code blocks, or additional text.
            """ + "Start your response directly with { and end with }."

            # Use rate limiter for AI API calls
            async def make_groq_request():
                return client.chat.completions.create(
                    model="gemma2-9b-it",
                    messages=[
                        {
                            "role": "user",
                            "content": extraction_prompt
                        }
                    ],
                    temperature=0.1,
                    max_completion_tokens=1024,
                    top_p=1,
                    stream=False
                )

            # Apply rate limiting
            completion = await make_ai_request_with_rate_limit(make_groq_request)

            response_content = completion.choices[0].message.content
            logger.info(f"Groq AI response received for {hotel['name']}: {len(response_content)} characters")
            logger.info(f"Raw AI response: {response_content[:500]}...")

            # Try to parse JSON response
            try:
                ai_data = json.loads(response_content)
                logger.info(f"AI extraction successful for {hotel['name']}: {type(ai_data)} - amenities: {len(ai_data.get('amenities', []))}")
                return ai_data
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse AI response as JSON for {hotel['name']}: {e}")
                logger.warning(f"Raw response: {response_content[:200]}...")
                return None

        except Exception as e:
            logger.warning(f"AI extraction failed for {hotel['name']}: {e}")
            return None

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

            async with httpx.AsyncClient(headers=headers, timeout=30, follow_redirects=True) as client:
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

            # Price with detailed analysis - improved logic for VietnamBooking
            price_elem = soup.select_one('.price, .hotel-price, .rate, .price-range, .price-info')
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                data['price_range'] = price_text

                # Extract detailed pricing information - improved logic for VietnamBooking
                import re

                # Clean up the price text - remove Vietnamese text separators
                price_text_clean = re.sub(r'Giá trung bình mỗi đêm', ' ', price_text, flags=re.IGNORECASE)
                price_text_clean = re.sub(r'Tiết kiệm tới', ' ', price_text_clean, flags=re.IGNORECASE)
                price_text_clean = re.sub(r'VNĐ|VND|đ|₫', ' VND ', price_text_clean, flags=re.IGNORECASE)

                # Extract prices - look for VND amounts specifically, but exclude percentages
                price_pattern = re.compile(r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*VND', re.IGNORECASE)
                price_matches = price_pattern.findall(price_text_clean)

                prices = []

                # Extract and clean prices
                for match in price_matches:
                    price_str = match.strip()
                    # Skip if it's a percentage (usually single or double digits)
                    try:
                        price_numeric = float(price_str.replace(',', ''))
                        # Skip prices that are too low (likely percentages)
                        if price_numeric >= 1000:  # Minimum reasonable hotel price in VND
                            prices.append(price_numeric)
                    except ValueError:
                        continue

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

            # Extract room details - NEW FUNCTIONALITY
            room_details = self._extract_room_details(soup, hotel['url'])
            if room_details:
                data['room_details'] = room_details
                logger.info(f"Extracted {len(room_details)} room types for {hotel['name']}")

            logger.info(f"Basic extraction successful for {hotel['name']}: {len(data)} fields, {len(amenities)} cleaned amenities")
            return data

        except Exception as e:
            logger.error(f"Basic extraction failed for {hotel['name']}: {e}")
            return {}

    def _extract_room_details(self, soup: BeautifulSoup, hotel_url: str) -> List[Dict[str, Any]]:
        """Extract detailed room information from hotel page using enhanced extraction"""

        try:
            # Use the enhanced detailed room extraction
            detailed_rooms = self._extract_detailed_room_info(soup)

            if detailed_rooms:
                logger.info(f"Extracted {len(detailed_rooms)} detailed rooms using enhanced extraction")
                return detailed_rooms

            # Fallback to basic room extraction if enhanced extraction fails
            logger.warning("Enhanced room extraction failed, falling back to basic extraction")

            # Basic fallback: extract room types from text content
            text_content = soup.get_text()
            room_keywords = [
                'phòng đơn', 'phòng đôi', 'phòng gia đình', 'phòng suite',
                'single room', 'double room', 'family room', 'suite',
                'deluxe room', 'superior room', 'standard room',
                'villa', 'bungalow', 'cottage', 'penthouse'
            ]

            found_rooms = []
            for keyword in room_keywords:
                if keyword.lower() in text_content.lower():
                    found_rooms.append({
                        'room_type': keyword,
                        'source': 'basic_fallback'
                    })

            logger.info(f"Basic fallback found {len(found_rooms)} room types")
            return found_rooms[:6]  # Limit to 6 rooms

        except Exception as e:
            logger.error(f"Error extracting room details: {e}")
            return []

    def _extract_price_info(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract price information from hotel page"""

        try:
            # Look for price elements
            price_selectors = [
                '.price-room-from', '[class*="price"]', '.rate', '.cost',
                '.room-rate', '.price', '.gia-phong'
            ]

            for selector in price_selectors:
                price_elements = soup.select(selector)
                for elem in price_elements:
                    text = elem.get_text(strip=True)
                    # Look for VND prices
                    import re
                    price_match = re.search(r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(VND|VNĐ|đ)', text, re.IGNORECASE)
                    if price_match:
                        price_str = price_match.group(1).replace(',', '')
                        try:
                            price = float(price_str)
                            currency = price_match.group(2).upper()
                            return {
                                'price': price,
                                'currency': currency,
                                'formatted': f"{price:,.0f} {currency}"
                            }
                        except ValueError:
                            continue

            # Try to extract from text content with room context
            text_content = soup.get_text()

            # Look for prices that appear near room-related content
            lines = text_content.split('\n')
            for line in lines:
                if any(kw in line.lower() for kw in ['phòng', 'room', 'đêm', 'night']):
                    price_match = re.search(r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:VND|VNĐ|đ|/đêm)', line, re.IGNORECASE)
                    if price_match:
                        price_str = price_match.group(1).replace(',', '')
                        try:
                            price = float(price_str)
                            return {
                                'price': price,
                                'currency': 'VND',
                                'formatted': f"{price:,.0f} VND"
                            }
                        except ValueError:
                            continue

            # Fallback to any VND price in the content
            price_match = re.search(r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:VND|VNĐ|đ)', text_content, re.IGNORECASE)
            if price_match:
                price_str = price_match.group(1).replace(',', '')
                try:
                    price = float(price_str)
                    return {
                        'price': price,
                        'currency': 'VND',
                        'formatted': f"{price:,.0f} VND"
                    }
                except ValueError:
                    pass

            return None

        except Exception as e:
            logger.error(f"Error extracting price info: {e}")
            return None

    def _extract_occupancy_info(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract occupancy information from hotel page"""

        try:
            # Look for form inputs with adult/child counts
            adult_inputs = soup.select('input[name*="adult"], select[name*="adult"]')
            child_inputs = soup.select('input[name*="child"], select[name*="child"]')

            max_adults = 2  # Default
            max_children = 0  # Default

            for inp in adult_inputs:
                value = inp.get('value') or inp.get('placeholder') or inp.get('max')
                if value and value.isdigit():
                    max_adults = max(max_adults, int(value))

            for inp in child_inputs:
                value = inp.get('value') or inp.get('placeholder') or inp.get('max')
                if value and value.isdigit():
                    max_children = max(max_children, int(value))

            total_occupancy = max_adults + max_children

            return {
                'max_adults': max_adults,
                'max_children': max_children,
                'max_occupancy': total_occupancy
            }

        except Exception as e:
            logger.error(f"Error extracting occupancy info: {e}")
            return None

    def _extract_nearby_places(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract nearby places information from hotel page"""

        try:
            nearby_places = []

            # Look for distance/time information in text
            distance_elements = soup.find_all(text=lambda text: text and ('km' in text.lower() or 'phút' in text.lower() or 'mét' in text.lower()))

            for elem in distance_elements:
                text = elem.strip()
                if text and len(text) > 10:  # Filter out very short texts
                    # Parse place name and distance
                    place_info = self._parse_nearby_place(text)
                    if place_info:
                        nearby_places.append(place_info)

            # Remove duplicates based on place name
            unique_places = []
            seen_names = set()
            for place in nearby_places:
                name = place.get('name', '').lower().strip()
                if name and name not in seen_names:
                    seen_names.add(name)
                    unique_places.append(place)

            logger.info(f"Extracted {len(unique_places)} nearby places")
            return unique_places[:10]  # Limit to 10 places

        except Exception as e:
            logger.error(f"Error extracting nearby places: {e}")
            return []

    def _parse_nearby_place(self, text: str) -> Dict[str, Any]:
        """Parse individual nearby place information"""

        try:
            import re

            # Patterns for Vietnamese distance expressions
            patterns = [
                r'Cách\s+(.+?)\s+(\d+(?:,\d+)?(?:\.\d+)?)\s*(km|mét|phút)',
                r'(.+?)\s+(\d+(?:,\d+)?(?:\.\d+)?)\s*(km|mét|phút)',
                r'(.+?)\s*cách\s*(\d+(?:,\d+)?(?:\.\d+)?)\s*(km|mét|phút)'
            ]

            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    place_name = match.group(1).strip()
                    distance_value = match.group(2).strip()
                    distance_unit = match.group(3).strip()

                    # Clean up place name
                    place_name = re.sub(r'^[•\-\s]*', '', place_name)  # Remove bullets/dashes
                    place_name = re.sub(r'[•\-\s]*$', '', place_name)

                    # Convert distance to float
                    try:
                        distance = float(distance_value.replace(',', '.'))
                    except ValueError:
                        distance = None

                    # Categorize place type
                    place_type = self._categorize_place_type(place_name)

                    return {
                        'name': place_name,
                        'distance': distance,
                        'distance_unit': distance_unit,
                        'distance_text': f"{distance_value} {distance_unit}",
                        'type': place_type,
                        'source': 'html_parsing'
                    }

            return None

        except Exception as e:
            logger.error(f"Error parsing nearby place '{text}': {e}")
            return None

    def _categorize_place_type(self, place_name: str) -> str:
        """Categorize nearby place by type"""

        name_lower = place_name.lower()

        # Religious sites
        if any(kw in name_lower for kw in ['phật', 'đài', 'chùa', 'temple', 'pagoda']):
            return 'religious_site'

        # Landmarks
        if any(kw in name_lower for kw in ['bạch dinh', 'palace', 'dinh', 'tượng', 'statue', 'kito']):
            return 'landmark'

        # Beaches
        if any(kw in name_lower for kw in ['bãi biển', 'beach', 'biển']):
            return 'beach'

        # Transportation
        if any(kw in name_lower for kw in ['bến tàu', 'cảng', 'sân bay', 'port', 'airport', 'ga']):
            return 'transportation'

        # Restaurants
        if any(kw in name_lower for kw in ['nhà hàng', 'restaurant', 'quán', 'cafe']):
            return 'restaurant'

        # Shopping
        if any(kw in name_lower for kw in ['chợ', 'market', 'mall', 'center']):
            return 'shopping'

        # Default
        return 'attraction'

    def _extract_room_specific_amenities(self, text_content: str, room_type: str) -> List[str]:
        """Extract amenities specific to a room type from text content"""

        try:
            amenities = []
            text_lower = text_content.lower()
            room_lower = room_type.lower()

            # Common room amenities
            amenity_keywords = {
                'wifi': ['wifi', 'internet', 'wi-fi'],
                'tv': ['tv', 'television', 'truyền hình'],
                'ac': ['điều hòa', 'air conditioning', 'máy lạnh'],
                'balcony': ['ban công', 'balcony', 'terrace'],
                'bathroom': ['phòng tắm', 'bathroom', 'shower'],
                'minibar': ['minibar', 'tủ lạnh nhỏ'],
                'safe': ['két sắt', 'safe', 'safe box'],
                'view': ['view', 'tầm nhìn', 'biển', 'sea view'],
                'jacuzzi': ['jacuzzi', 'bồn spa'],
                'bathtub': ['bồn tắm', 'bathtub']
            }

            # Look for amenities that appear near the room type
            lines = text_content.split('\n')
            room_context = []

            # Find lines that contain the room type
            for line in lines:
                if room_lower in line.lower():
                    room_context.append(line)

            # Extract amenities from room context
            for line in room_context:
                line_lower = line.lower()
                for amenity, keywords in amenity_keywords.items():
                    for keyword in keywords:
                        if keyword in line_lower and amenity not in amenities:
                            amenities.append(amenity)
                            break

            return amenities[:8]  # Limit to 8 amenities per room

        except Exception as e:
            logger.error(f"Error extracting room amenities for {room_type}: {e}")
            return []

    def _extract_detailed_room_info(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract detailed room information from structured HTML content"""

        try:
            detailed_rooms = []

            # Look for JavaScript data that might contain room information
            scripts = soup.find_all('script')
            room_data_found = False

            for script in scripts:
                if script.string and ('phòng' in script.string.lower() or 'room' in script.string.lower() or 'roomData' in script.string):
                    # Try to extract room data from JavaScript
                    js_rooms = self._parse_room_data_from_javascript(script.string)
                    if js_rooms:
                        detailed_rooms.extend(js_rooms)
                        room_data_found = True
                        logger.info(f"Extracted {len(js_rooms)} rooms from JavaScript data")
                        break

            # If no JavaScript data found, try to extract from structured HTML
            if not room_data_found:
                # Look for room description sections with detailed info
                room_sections = soup.find_all(['div', 'section'], class_=lambda x: x and any(kw in ' '.join(x).lower() for kw in ['room', 'phong', 'suite', 'deluxe']))

                for section in room_sections[:6]:  # Limit to 6 rooms
                    room_data = self._parse_room_section(section)
                    if room_data:
                        detailed_rooms.append(room_data)

                # Also try to extract from text content with structured parsing
                text_rooms = self._parse_rooms_from_text_content(soup.get_text())
                if text_rooms:
                    # Merge with existing rooms, avoiding duplicates
                    existing_types = {room['room_type'] for room in detailed_rooms}
                    for room in text_rooms:
                        if room['room_type'] not in existing_types:
                            detailed_rooms.append(room)

            return detailed_rooms[:8]  # Limit to 8 rooms max

        except Exception as e:
            logger.error(f"Error extracting detailed room info: {e}")
            return []

    def _identify_room_type_from_text(self, text: str) -> str:
        """Identify room type from descriptive text"""

        text_lower = text.lower()

        # Priority order for room type identification (expanded list)
        # Put specific room types first, generic ones last
        room_type_patterns = [
            ('chic wing', ['chic wing', 'phòng chic wing']),
            ('superior', ['superior', 'phòng superior']),
            ('classic', ['classic', 'phòng classic']),
            ('premier', ['premier', 'phòng premier']),
            ('deluxe', ['deluxe', 'phòng deluxe']),
            ('suite', ['suite', 'phòng suite']),
            ('executive', ['executive', 'phòng executive']),
            ('presidential', ['presidential', 'phòng presidential']),
            ('grand', ['grand', 'phòng grand']),
            ('standard', ['standard', 'phòng standard']),
            ('family', ['family', 'gia đình', 'phòng gia đình', 'phòng family']),
            ('double', ['double', 'phòng đôi', 'phòng double']),
            ('single', ['single', 'phòng đơn', 'phòng single']),
            ('villa', ['villa', 'phòng villa']),
            ('bungalow', ['bungalow', 'phòng bungalow']),
            ('penthouse', ['penthouse', 'phòng penthouse'])
        ]

        for room_type, keywords in room_type_patterns:
            for keyword in keywords:
                if keyword in text_lower:
                    return keyword

        return None

    def _parse_room_element(self, elem) -> Dict[str, Any]:

        try:
            room_data = {
                'room_type': None,
                'description': None,
                'price': None,
                'max_occupancy': None,
                'bed_type': None,
                'size': None,
                'view': None,
                'amenities': [],
                'source': 'html_parsing'
            }

            # Extract room type/name
            name_selectors = ['.room-name', '.room-title', '.room-type', 'h3', 'h4', '.title', '.name']
            for selector in name_selectors:
                name_elem = elem.select_one(selector)
                if name_elem:
                    room_data['room_type'] = name_elem.get_text(strip=True)
                    break

            # Extract description
            desc_selectors = ['.room-description', '.description', '.room-desc', '.details', 'p']
            for selector in desc_selectors:
                desc_elem = elem.select_one(selector)
                if desc_elem:
                    room_data['description'] = desc_elem.get_text(strip=True)
                    break

            # Extract price
            price_selectors = ['.room-price', '.price', '.rate', '.cost', '.room-rate']
            for selector in price_selectors:
                price_elem = elem.select_one(selector)
                if price_elem:
                    price_text = price_elem.get_text(strip=True)
                    # Try to extract numeric price
                    price_match = re.search(r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?)', price_text)
                    if price_match:
                        try:
                            room_data['price'] = float(price_match.group(1).replace(',', ''))
                        except ValueError:
                            pass
                    break

            # Extract occupancy info
            occupancy_patterns = [
                r'(\d+)\s*(?:người|person|guest|occupancy)',
                r'max\s*(\d+)',
                r'(\d+)\s*adult',
                r'(\d+)\s*pax'
            ]

            text_content = elem.get_text()
            for pattern in occupancy_patterns:
                match = re.search(pattern, text_content, re.IGNORECASE)
                if match:
                    try:
                        room_data['max_occupancy'] = int(match.group(1))
                        break
                    except ValueError:
                        continue

            # Extract bed type
            bed_keywords = ['single', 'double', 'queen', 'king', 'twin', 'single bed', 'double bed', 'queen bed', 'king bed']
            for keyword in bed_keywords:
                if keyword.lower() in text_content.lower():
                    room_data['bed_type'] = keyword
                    break

            # Extract room size
            size_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:m²|m2|sqm|square meter)', text_content, re.IGNORECASE)
            if size_match:
                try:
                    room_data['size'] = float(size_match.group(1))
                except ValueError:
                    pass

            # Extract view information
            view_keywords = ['sea view', 'ocean view', 'city view', 'mountain view', 'garden view', 'pool view', 'view biển', 'view thành phố']
            for keyword in view_keywords:
                if keyword.lower() in text_content.lower():
                    room_data['view'] = keyword
                    break

            # Extract room amenities
            room_amenities = []
            amenity_keywords = [
                'wifi', 'internet', 'tv', 'air conditioning', 'balcony', 'terrace',
                'minibar', 'safe', 'bathroom', 'shower', 'bathtub', 'jacuzzi',
                'Điều hòa', 'WiFi', 'TV', 'Ban công', 'Minibar', 'két sắt'
            ]

            for amenity in amenity_keywords:
                if amenity.lower() in text_content.lower() and amenity not in room_amenities:
                    room_amenities.append(amenity)

            room_data['amenities'] = room_amenities[:10]  # Limit to 10 amenities

            # Only return if we have at least a room type
            if room_data['room_type']:
                return room_data
            else:
                return None

        except Exception as e:
            logger.error(f"Error parsing room element: {e}")
            return None

    def _parse_room_data_from_javascript(self, js_content: str) -> List[Dict[str, Any]]:
        """Parse room data from JavaScript content"""
        rooms = []

        try:
            # Try to extract JSON array directly from JavaScript
            import json

            # Look for array assignments like var roomData = [...];
            array_match = re.search(r'var\s+roomData\s*=\s*(\[.*?\]);', js_content, re.DOTALL)
            if array_match:
                try:
                    room_array = json.loads(array_match.group(1))
                    logger.info(f"Successfully parsed {len(room_array)} rooms from JavaScript JSON")
                    for room in room_array:
                        if isinstance(room, dict):
                            parsed_room = self._parse_room_from_js_object(room)
                            if parsed_room:
                                rooms.append(parsed_room)
                    return rooms
                except json.JSONDecodeError as e:
                    logger.warning(f"Direct JSON parsing failed: {e}")

            # If direct parsing fails, fall back to text parsing
            logger.info("Falling back to text parsing for JavaScript content")
            text_rooms = self._parse_rooms_from_text_content(js_content)
            rooms.extend(text_rooms)

            return rooms[:6]  # Limit to 6 rooms

        except Exception as e:
            logger.error(f"Error parsing room data from JavaScript: {e}")
            return []

    def _parse_room_from_js_object(self, room_obj: Dict[str, Any]) -> Dict[str, Any]:
        """Parse a single room object from JavaScript"""
        try:
            room_data = {
                'room_type': room_obj.get('name') or room_obj.get('type') or room_obj.get('title'),
                'description': room_obj.get('description') or room_obj.get('desc'),
                'price': None,
                'max_occupancy': room_obj.get('occupancy') or room_obj.get('max_guests') or room_obj.get('capacity'),
                'bed_type': room_obj.get('bed_type') or room_obj.get('bed'),
                'size': room_obj.get('size') or room_obj.get('area'),
                'view': room_obj.get('view'),
                'amenities': room_obj.get('amenities', []) or room_obj.get('features', []),
                'source': 'javascript_parsing'
            }

            # Process price
            if 'price' in room_obj:
                price = room_obj['price']
                if isinstance(price, (int, float)):
                    room_data['price'] = price
                elif isinstance(price, str):
                    price_match = re.search(r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?)', price)
                    if price_match:
                        room_data['price'] = float(price_match.group(1).replace(',', ''))

            # Ensure amenities is a list
            if isinstance(room_data['amenities'], str):
                room_data['amenities'] = [room_data['amenities']]

            return room_data if room_data['room_type'] else None

        except Exception as e:
            logger.error(f"Error parsing room from JS object: {e}")
            return None

    def _parse_room_section(self, section) -> Dict[str, Any]:
        """Parse a room section from HTML"""
        try:
            room_data = {
                'room_type': None,
                'description': None,
                'price': None,
                'max_occupancy': None,
                'bed_type': None,
                'size': None,
                'view': None,
                'amenities': [],
                'source': 'html_section_parsing'
            }

            # Get all text content
            text_content = section.get_text()

            # Extract room type from heading or strong text
            headings = section.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'strong', 'b'])
            for heading in headings:
                heading_text = heading.get_text(strip=True)
                if len(heading_text) > 3 and len(heading_text) < 50:
                    room_type = self._identify_room_type_from_text(heading_text)
                    if room_type:
                        room_data['room_type'] = room_type
                        break

            # If no room type found, try from text content
            if not room_data['room_type']:
                room_data['room_type'] = self._identify_room_type_from_text(text_content)

            # Extract price
            price_match = re.search(r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(?:VND|VNĐ|đ|₫)', text_content, re.IGNORECASE)
            if price_match:
                try:
                    room_data['price'] = float(price_match.group(1).replace(',', ''))
                except ValueError:
                    pass

            # Extract occupancy
            occupancy_match = re.search(r'(\d+)\s*(?:người|person|guest|max)', text_content, re.IGNORECASE)
            if occupancy_match:
                try:
                    room_data['max_occupancy'] = int(occupancy_match.group(1))
                except ValueError:
                    pass

            # Extract bed type
            bed_keywords = ['giường đơn', 'giường đôi', 'single bed', 'double bed', 'king bed', 'queen bed']
            for bed_type in bed_keywords:
                if bed_type.lower() in text_content.lower():
                    room_data['bed_type'] = bed_type
                    break

            # Extract size
            size_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:m²|m2|met|mét)', text_content, re.IGNORECASE)
            if size_match:
                room_data['size'] = f"{size_match.group(1)} m²"

            # Extract view
            view_keywords = ['view biển', 'view thành phố', 'view núi', 'view vườn', 'sea view', 'city view', 'mountain view', 'garden view']
            for view in view_keywords:
                if view.lower() in text_content.lower():
                    room_data['view'] = view
                    break

            # Extract amenities
            room_data['amenities'] = self._extract_room_specific_amenities(text_content, room_data['room_type'] or '')

            # Set description
            room_data['description'] = text_content[:200] if len(text_content) > 10 else None

            return room_data if room_data['room_type'] else None

        except Exception as e:
            logger.error(f"Error parsing room section: {e}")
            return None

    def _parse_rooms_from_text_content(self, text_content: str) -> List[Dict[str, Any]]:
        """Parse multiple rooms from text content with structured format"""
        rooms = []

        try:
            # First, try to parse structured room blocks (like the user's example)
            structured_rooms = self._parse_structured_room_blocks(text_content)
            if structured_rooms:
                rooms.extend(structured_rooms)
                logger.info(f"Parsed {len(structured_rooms)} rooms from structured blocks")
                return rooms[:6]  # Limit to 6 rooms

            # Split text into sections that might contain room information
            # Look for patterns like "Room Type: ..." or numbered lists
            room_sections = re.split(r'(?:\d+\.|\*\s*|-\s*|•\s*)(phòng|room)', text_content, flags=re.IGNORECASE)

            for i in range(1, len(room_sections), 2):  # Skip first part, take pairs
                if i + 1 < len(room_sections):
                    section_text = room_sections[i] + room_sections[i + 1]

                    room_data = self._parse_room_from_text_section(section_text)
                    if room_data:
                        rooms.append(room_data)

            # If no structured sections found, try to find room patterns in the whole text
            if not rooms:
                # Look for multiple room mentions with improved patterns
                room_patterns = [
                    r'(phòng\s+(?:superior|classic|chic\s+wing|premier|deluxe|suite|family|gia\s+đình|đơn|đôi|standard|executive|presidential|grand).*?)(?=(phòng\s+(?:superior|classic|chic\s+wing|premier|deluxe|suite|family|gia\s+đình|đơn|đôi|standard|executive|presidential|grand)|$))',
                    r'(phòng\s+\w+(?:\s+\w+)*.*?)(?=(phòng\s+\w+|$))',
                    r'(room\s+\w+(?:\s+\w+)*.*?)(?=(room\s+\w+|$))',
                    r'((?:superior|classic|chic\s+wing|premier|deluxe|suite|family|standard|executive|presidential|grand)\s+room.*?)(?=((?:superior|classic|chic\s+wing|premier|deluxe|suite|family|standard|executive|presidential|grand)\s+room|$))'
                ]

                for pattern in room_patterns:
                    matches = re.findall(pattern, text_content, re.IGNORECASE | re.DOTALL)
                    for match in matches:
                        # Ensure match is a string
                        if isinstance(match, tuple):
                            match = match[0]
                        room_data = self._parse_room_from_text_section(match)
                        if room_data:
                            rooms.append(room_data)

                # Remove duplicates based on room_type
                unique_rooms = []
                seen_types = set()
                for room in rooms:
                    room_type = room.get('room_type')
                    if room_type and room_type not in seen_types:
                        unique_rooms.append(room)
                        seen_types.add(room_type)

                rooms = unique_rooms

            return rooms[:4]  # Limit to 4 rooms

        except Exception as e:
            logger.error(f"Error parsing rooms from text content: {e}")
            return []

    def _parse_structured_room_blocks(self, text_content: str) -> List[Dict[str, Any]]:
        """Parse structured room blocks like the user's example format"""
        rooms = []

        try:
            # Split text by "Phòng " or "Room " to find room blocks
            # Pattern to match room headers
            room_header_pattern = r'(?:^|\n)(Phòng\s+\w+(?:\s+\w+)*|Room\s+\w+(?:\s+\w+)*)'
            headers = re.findall(room_header_pattern, text_content, re.MULTILINE | re.IGNORECASE)

            if not headers:
                return []

            # For each header, extract the room block
            for i, header in enumerate(headers):
                # Find the start position of this header
                start_pos = text_content.find(header)

                # Find the end position (next header or end of text)
                if i + 1 < len(headers):
                    next_header = headers[i + 1]
                    end_pos = text_content.find(next_header, start_pos + len(header))
                else:
                    end_pos = len(text_content)

                # Extract the room block
                room_block = text_content[start_pos:end_pos].strip()

                # Parse this room block
                room_data = self._parse_room_block(room_block)
                if room_data:
                    rooms.append(room_data)

            return rooms

        except Exception as e:
            logger.error(f"Error parsing structured room blocks: {e}")
            return []

    def _parse_room_block(self, room_block: str) -> Dict[str, Any]:
        """Parse a single room block with detailed information"""
        try:
            lines = room_block.strip().split('\n')
            lines = [line.strip() for line in lines if line.strip()]

            if not lines:
                return None

            room_data = {
                'room_type': None,
                'description': room_block[:300],  # Store full block as description
                'price': None,
                'max_occupancy': None,
                'bed_type': None,
                'size': None,
                'view': None,
                'amenities': [],
                'source': 'structured_parsing'
            }

            # First line should be room type
            first_line = lines[0]
            room_data['room_type'] = self._identify_room_type_from_text(first_line)

            # Parse each line for specific information
            for line in lines[1:]:
                line_lower = line.lower()

                # Size (e.g., "25 m2")
                if 'm2' in line_lower or 'm²' in line_lower:
                    size_match = re.search(r'(\d+(?:\.\d+)?)\s*m[²2]', line, re.IGNORECASE)
                    if size_match:
                        room_data['size'] = f"{size_match.group(1)} m²"

                # Bed type (e.g., "Giường Đôi")
                elif 'giường' in line_lower or 'bed' in line_lower:
                    if 'đôi' in line_lower or 'double' in line_lower:
                        room_data['bed_type'] = 'giường đôi'
                    elif 'đơn' in line_lower or 'single' in line_lower:
                        room_data['bed_type'] = 'giường đơn'
                    elif 'king' in line_lower:
                        room_data['bed_type'] = 'king bed'
                    elif 'queen' in line_lower:
                        room_data['bed_type'] = 'queen bed'
                    else:
                        room_data['bed_type'] = line.strip()

                # View (e.g., "Hướng phố", "Hướng không cảnh quan")
                elif 'hướng' in line_lower or 'view' in line_lower:
                    if 'phố' in line_lower or 'city' in line_lower:
                        room_data['view'] = 'city view'
                    elif 'biển' in line_lower or 'sea' in line_lower:
                        room_data['view'] = 'sea view'
                    elif 'núi' in line_lower or 'mountain' in line_lower:
                        room_data['view'] = 'mountain view'
                    elif 'vườn' in line_lower or 'garden' in line_lower:
                        room_data['view'] = 'garden view'
                    elif 'hồ' in line_lower or 'pool' in line_lower:
                        room_data['view'] = 'pool view'
                    elif 'không cảnh quan' in line_lower:
                        room_data['view'] = 'no view'
                    else:
                        room_data['view'] = line.strip()

                # Occupancy (e.g., "x 2 người lớn", "x 1 em bé")
                elif 'người lớn' in line_lower or 'adult' in line_lower:
                    adult_match = re.search(r'x\s*(\d+)\s*người lớn', line, re.IGNORECASE)
                    if adult_match:
                        adults = int(adult_match.group(1))
                        current_occupancy = room_data.get('max_occupancy', 0) or 0
                        room_data['max_occupancy'] = current_occupancy + adults

                elif 'em bé' in line_lower or 'child' in line_lower:
                    child_match = re.search(r'x\s*(\d+)\s*em bé', line, re.IGNORECASE)
                    if child_match:
                        children = int(child_match.group(1))
                        current_occupancy = room_data.get('max_occupancy', 0) or 0
                        room_data['max_occupancy'] = current_occupancy + children

                # Amenities
                elif any(keyword in line_lower for keyword in ['wifi', 'không hút thuốc', 'phòng tắm', 'tắm']):
                    if 'wifi' in line_lower:
                        room_data['amenities'].append('wifi')
                    if 'không hút thuốc' in line_lower:
                        room_data['amenities'].append('không hút thuốc')
                    if 'phòng tắm' in line_lower or 'tắm' in line_lower:
                        if 'vòi sen' in line_lower and 'bồn tắm' in line_lower:
                            room_data['amenities'].append('phòng tắm vòi sen & bồn tắm')
                        elif 'vòi sen' in line_lower:
                            room_data['amenities'].append('phòng tắm vòi sen')
                        elif 'bồn tắm' in line_lower:
                            room_data['amenities'].append('bồn tắm')

                # Price (look for VND amounts, prefer discounted price)
                elif 'vnd' in line_lower or 'vnđ' in line_lower or 'đ' in line_lower:
                    price_matches = re.findall(r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(?:VND|VNĐ|đ)', line, re.IGNORECASE)
                    if price_matches:
                        try:
                            # Take the last price found in the line (usually the discounted price)
                            price = float(price_matches[-1].replace(',', ''))
                            # Only update if we haven't set a price yet, or if this is a lower price (discounted)
                            if room_data['price'] is None or price < room_data['price']:
                                room_data['price'] = price
                        except ValueError:
                            pass

            # Remove duplicates from amenities
            room_data['amenities'] = list(set(room_data['amenities']))

            # Only return if we have a room type
            return room_data if room_data['room_type'] else None

        except Exception as e:
            logger.error(f"Error parsing room block: {e}")
            return None

    def _parse_room_from_text_section(self, text) -> Dict[str, Any]:
        """Parse a single room from text section"""
        try:
            # Ensure text is a string
            if not isinstance(text, str):
                text = str(text)

            room_data = {
                'room_type': None,
                'description': text.strip()[:200] if text.strip() else None,
                'price': None,
                'max_occupancy': None,
                'bed_type': None,
                'size': None,
                'view': None,
                'amenities': [],
                'source': 'text_parsing'
            }

            # Extract room type
            room_data['room_type'] = self._identify_room_type_from_text(text)

            # Extract price (look for VND amounts, prefer the last one which might be discounted)
            price_matches = re.findall(r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(?:VND|VNĐ|đ|₫)', text, re.IGNORECASE)
            if price_matches:
                try:
                    # Take the last price found (usually the discounted price)
                    room_data['price'] = float(price_matches[-1].replace(',', ''))
                except ValueError:
                    pass

            # Extract occupancy (look for patterns like "x 2 người lớn", "x 1 em bé")
            adult_match = re.search(r'x\s*(\d+)\s*(?:người lớn|adult)', text, re.IGNORECASE)
            child_match = re.search(r'x\s*(\d+)\s*(?:em bé|child)', text, re.IGNORECASE)

            total_occupancy = 0
            if adult_match:
                total_occupancy += int(adult_match.group(1))
            if child_match:
                total_occupancy += int(child_match.group(1))

            if total_occupancy > 0:
                room_data['max_occupancy'] = total_occupancy

            # Extract bed type
            bed_keywords = ['giường đơn', 'giường đôi', 'single bed', 'double bed', 'king bed', 'queen bed', 'twin bed']
            for bed_type in bed_keywords:
                if bed_type.lower() in text.lower():
                    room_data['bed_type'] = bed_type
                    break

            # Extract size
            size_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:m²|m2|met|mét)', text, re.IGNORECASE)
            if size_match:
                room_data['size'] = f"{size_match.group(1)} m²"

            # Extract view
            view_keywords = ['view biển', 'view thành phố', 'view núi', 'view vườn', 'sea view', 'city view', 'mountain view', 'garden view', 'hướng phố', 'hướng biển', 'hướng không cảnh quan']
            for view in view_keywords:
                if view.lower() in text.lower():
                    room_data['view'] = view
                    break

            # Extract amenities
            room_data['amenities'] = self._extract_room_specific_amenities(text, room_data['room_type'] or '')

            return room_data if room_data['room_type'] else None

        except Exception as e:
            logger.error(f"Error parsing room from text section: {e}")
            return None

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