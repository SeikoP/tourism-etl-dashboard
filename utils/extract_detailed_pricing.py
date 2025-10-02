#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import httpx
import json
import logging
import re
from bs4 import BeautifulSoup
from typing import Dict, Any, List

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def extract_detailed_pricing():
    """Extract detailed pricing information from VietnamBooking hotel page"""

    hotel_url = "https://www.vietnambooking.com/hotel/vietnam/khach-san-vias-vung-tau.html"

    print(f"💰 Extracting detailed pricing from: {hotel_url}")

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'vi-VN,vi;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Cache-Control': 'max-age=0',
        'Connection': 'keep-alive',
    }

    try:
        async with httpx.AsyncClient(headers=headers, timeout=30) as client:
            response = await client.get(hotel_url)

        soup = BeautifulSoup(response.text, 'html.parser')

        pricing_data = {
            'currency': 'VND',
            'price_ranges': [],
            'room_types': [],
            'raw_prices': []
        }

        # Extract all price-related elements
        price_selectors = [
            '.price',
            '.hotel-price',
            '.rate',
            '.price-range',
            '.room-price',
            '.pricing',
            '[data-price]',
            '[data-rate]',
            '.cost'
        ]

        all_prices = []

        for selector in price_selectors:
            elements = soup.select(selector)
            for elem in elements:
                text = elem.get_text(strip=True)
                data_price = elem.get('data-price')
                data_rate = elem.get('data-rate')

                if text:
                    all_prices.append({
                        'text': text,
                        'selector': selector,
                        'data_price': data_price,
                        'data_rate': data_rate
                    })

        print(f"📊 Found {len(all_prices)} price elements")

        # Extract numeric prices from text
        price_pattern = re.compile(r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(VNĐ|VND|đ|₫)?', re.IGNORECASE)

        for price_item in all_prices:
            text = price_item['text']
            matches = price_pattern.findall(text)

            for match in matches:
                price_str, currency = match
                # Remove commas and convert to float
                price_numeric = float(price_str.replace(',', ''))

                pricing_data['raw_prices'].append({
                    'price': price_numeric,
                    'currency': currency or 'VND',
                    'original_text': text,
                    'selector': price_item['selector']
                })

        # Analyze room types and pricing
        room_selectors = [
            '.room',
            '.room-type',
            '.accommodation',
            '.room-listing',
            '.room-item'
        ]

        rooms_data = []
        for selector in room_selectors:
            room_elements = soup.select(selector)
            for room_elem in room_elements:
                room_info = {}

                # Room name
                room_name_elem = room_elem.select_one('.room-name, .name, h3, h4, .title')
                if room_name_elem:
                    room_info['name'] = room_name_elem.get_text(strip=True)

                # Room price
                room_price_elem = room_elem.select_one('.price, .rate, .cost, [data-price]')
                if room_price_elem:
                    price_text = room_price_elem.get_text(strip=True)
                    room_info['price_text'] = price_text

                    # Extract numeric price
                    price_match = price_pattern.search(price_text)
                    if price_match:
                        price_str, currency = price_match.groups()
                        room_info['price'] = float(price_str.replace(',', ''))
                        room_info['currency'] = currency or 'VND'

                # Room description
                desc_elem = room_elem.select_one('.description, .desc, .details')
                if desc_elem:
                    room_info['description'] = desc_elem.get_text(strip=True)

                if room_info:
                    rooms_data.append(room_info)

        pricing_data['room_types'] = rooms_data

        # Calculate price ranges
        if pricing_data['raw_prices']:
            prices = [p['price'] for p in pricing_data['raw_prices']]
            pricing_data['price_ranges'] = {
                'min_price': min(prices),
                'max_price': max(prices),
                'avg_price': sum(prices) / len(prices),
                'price_count': len(prices),
                'currency': pricing_data['currency']
            }

            # Format for display
            pricing_data['formatted_range'] = f"{pricing_data['price_ranges']['min_price']:,.0f} - {pricing_data['price_ranges']['max_price']:,.0f} {pricing_data['currency']}"

        # Look for special pricing information
        special_pricing = []

        # Check for discount information
        discount_selectors = ['.discount', '.sale', '.offer', '.promotion']
        for selector in discount_selectors:
            discount_elems = soup.select(selector)
            for elem in discount_elems:
                discount_text = elem.get_text(strip=True)
                if discount_text:
                    special_pricing.append({
                        'type': 'discount',
                        'text': discount_text
                    })

        # Check for tax information
        tax_selectors = ['.tax', '.vat', '.fee']
        for selector in tax_selectors:
            tax_elems = soup.select(selector)
            for elem in tax_elems:
                tax_text = elem.get_text(strip=True)
                if tax_text:
                    special_pricing.append({
                        'type': 'tax',
                        'text': tax_text
                    })

        pricing_data['special_pricing'] = special_pricing

        # Summary
        print("\n💰 Pricing Analysis Summary:")
        print(f"   Currency: {pricing_data['currency']}")
        print(f"   Raw prices found: {len(pricing_data['raw_prices'])}")
        print(f"   Room types found: {len(pricing_data['room_types'])}")
        print(f"   Special pricing: {len(pricing_data['special_pricing'])}")

        if pricing_data['price_ranges']:
            pr = pricing_data['price_ranges']
            print(f"   Price range: {pr['min_price']:,.0f} - {pr['max_price']:,.0f} {pr['currency']}")
            print(f"   Average price: {pr['avg_price']:,.0f} {pr['currency']}")

        if pricing_data['room_types']:
            print("\n🛏️  Room Types:")
            for i, room in enumerate(pricing_data['room_types'][:5], 1):  # Show first 5
                name = room.get('name', 'Unknown')
                price = room.get('price', 'N/A')
                currency = room.get('currency', 'VND')
                print(f"   {i}. {name}: {price} {currency}")

        # Save detailed results
        result = {
            'hotel_url': hotel_url,
            'extraction_timestamp': json.dumps(None),  # Will be set by json.dumps with default=str
            'pricing_data': pricing_data
        }

        with open('utils/detailed_pricing_extraction.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2, default=str)

        print("\n💾 Saved detailed pricing to: utils/detailed_pricing_extraction.json")
        return pricing_data

    except Exception as e:
        print(f"❌ Error extracting pricing: {e}")
        return None

if __name__ == "__main__":
    asyncio.run(extract_detailed_pricing())