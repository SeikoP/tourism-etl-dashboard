#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import httpx
import json
import logging
from bs4 import BeautifulSoup
from typing import Dict, Any

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_basic_extraction():
    """Test basic extraction from VietnamBooking hotel page"""

    hotel_url = "https://www.vietnambooking.com/hotel/vietnam/khach-san-vias-vung-tau.html"

    print(f"🔍 Testing basic extraction for: {hotel_url}")

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'vi-VN,vi;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Cache-Control': 'max-age=0',
        'Connection': 'keep-alive',
    }

    try:
        print("📡 Fetching page...")
        async with httpx.AsyncClient(headers=headers, timeout=30) as client:
            response = await client.get(hotel_url)

        print(f"📊 Status: {response.status_code}")
        print(f"📏 Content length: {len(response.text)} characters")

        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract basic information
        extracted_data = {}

        # Title
        title = soup.find('title')
        extracted_data['page_title'] = title.text.strip() if title else None
        print(f"📄 Title: {extracted_data['page_title']}")

        # Meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        extracted_data['meta_description'] = meta_desc.get('content') if meta_desc else None

        # Hotel name from various possible locations
        hotel_name = None

        # Try h1
        h1 = soup.find('h1')
        if h1:
            hotel_name = h1.get_text(strip=True)
            print(f"🏨 Hotel name (h1): {hotel_name}")

        # Try specific classes that might contain hotel name
        name_selectors = [
            '.hotel-name',
            '.hotel-title',
            '.property-name',
            '[itemprop="name"]',
            '.hotel-header h1',
            '.page-title'
        ]

        for selector in name_selectors:
            if not hotel_name:
                element = soup.select_one(selector)
                if element:
                    hotel_name = element.get_text(strip=True)
                    print(f"🏨 Hotel name ({selector}): {hotel_name}")

        extracted_data['hotel_name'] = hotel_name

        # Address
        address_selectors = [
            '.hotel-address',
            '.address',
            '[itemprop="address"]',
            '.location-info'
        ]

        address = None
        for selector in address_selectors:
            if not address:
                element = soup.select_one(selector)
                if element:
                    address = element.get_text(strip=True)
                    print(f"📍 Address ({selector}): {address}")

        extracted_data['address'] = address

        # Phone
        phone_selectors = [
            '.phone',
            '.contact-phone',
            '.hotel-phone',
            'a[href^="tel:"]'
        ]

        phone = None
        for selector in phone_selectors:
            if not phone:
                element = soup.select_one(selector)
                if element:
                    if selector == 'a[href^="tel:"]':
                        phone = element.get('href', '').replace('tel:', '')
                    else:
                        phone = element.get_text(strip=True)
                    print(f"📞 Phone ({selector}): {phone}")

        extracted_data['phone'] = phone

        # Star rating
        star_selectors = [
            '.star-rating',
            '.rating',
            '.stars',
            '[itemprop="ratingValue"]'
        ]

        stars = None
        for selector in star_selectors:
            if not stars:
                element = soup.select_one(selector)
                if element:
                    stars = element.get_text(strip=True) or element.get('content')
                    print(f"⭐ Stars ({selector}): {stars}")

        extracted_data['stars'] = stars

        # Price information
        price_selectors = [
            '.price',
            '.hotel-price',
            '.rate',
            '.price-range'
        ]

        price = None
        for selector in price_selectors:
            if not price:
                element = soup.select_one(selector)
                if element:
                    price = element.get_text(strip=True)
                    print(f"💰 Price ({selector}): {price}")

        extracted_data['price'] = price

        # Amenities
        amenities_selectors = [
            '.amenities',
            '.facilities',
            '.services',
            '.features'
        ]

        amenities = []
        for selector in amenities_selectors:
            elements = soup.select(f'{selector} li, {selector} .item')
            if elements:
                for element in elements:
                    amenity = element.get_text(strip=True)
                    if amenity and len(amenity) > 1:
                        amenities.append(amenity)
                if amenities:
                    print(f"🏊 Amenities ({selector}): {amenities[:5]}...")  # Show first 5
                    break

        extracted_data['amenities'] = amenities

        # Room types
        room_selectors = [
            '.room-types',
            '.rooms',
            '.room-list',
            '.accommodation-types'
        ]

        rooms = []
        for selector in room_selectors:
            elements = soup.select(f'{selector} .room, {selector} .item, {selector} li')
            if elements:
                for element in elements:
                    room = element.get_text(strip=True)
                    if room and len(room) > 3:  # Avoid very short texts
                        rooms.append(room)
                if rooms:
                    print(f"🛏️  Rooms ({selector}): {rooms[:3]}...")  # Show first 3
                    break

        extracted_data['rooms'] = rooms

        print("\n📊 Extraction Summary:")
        print(f"✅ Hotel name: {'✓' if hotel_name else '✗'}")
        print(f"✅ Address: {'✓' if address else '✗'}")
        print(f"✅ Phone: {'✓' if phone else '✗'}")
        print(f"✅ Stars: {'✓' if stars else '✗'}")
        print(f"✅ Price: {'✓' if price else '✗'}")
        print(f"✅ Amenities: {'✓' if amenities else '✗'} ({len(amenities)} found)")
        print(f"✅ Rooms: {'✓' if rooms else '✗'} ({len(rooms)} found)")

        # Save to file for inspection
        result = {
            'url': hotel_url,
            'extraction_method': 'basic_beautifulsoup',
            'extracted_data': extracted_data,
            'extraction_success': True
        }

        with open('utils/vietnambooking_basic_extraction.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        print("\n💾 Saved results to: utils/vietnambooking_basic_extraction.json")

        return result

    except Exception as e:
        print(f"❌ Error during basic extraction: {e}")
        return None

if __name__ == "__main__":
    asyncio.run(test_basic_extraction())