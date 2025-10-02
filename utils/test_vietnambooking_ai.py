#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import httpx
import json
import logging
import time
from typing import Dict, Any

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_vietnambooking_ai_extraction():
    """Test AI extraction on VietnamBooking hotel page"""

    crawl4ai_url = "http://localhost:11235"

    # Sample hotel data
    hotel = {
        "location_name": "Vũng Tàu",
        "location_code": "vung-tau",
        "url": "https://www.vietnambooking.com/hotel/vietnam/khach-san-vias-vung-tau.html",
        "name": "Khách sạn Vias Vũng Tàu"
    }

    print(f"🏨 Testing AI extraction for: {hotel['name']}")
    print(f"🌐 URL: {hotel['url']}")
    print()

    # AI extraction prompt for hotel details (simplified)
    extraction_prompt = """
    Extract basic hotel information from this VietnamBooking page:

    1. Hotel name (tên khách sạn)
    2. Address/location (địa chỉ)
    3. Star rating if visible (số sao)
    4. Phone number (số điện thoại)
    5. Price range (khoảng giá)
    6. Main amenities (tiện ích chính)

    Return as simple JSON object.
    """

    # Prepare AI extraction request
    payload = {
        "urls": [hotel['url']],
        "extraction_prompt": extraction_prompt,
        "extraction_schema": {
            "type": "object",
            "properties": {
                "hotel_name": {"type": "string"},
                "address": {"type": "string"},
                "star_rating": {"type": ["number", "string", "null"]},
                "phone": {"type": "string"},
                "price_range": {"type": "string"},
                "amenities": {"type": "array", "items": {"type": "string"}}
            },
            "required": []
        },
        "wait_for": 5,  # Wait for dynamic content
        "remove_overlay_elements": True,  # Remove popups/modals
        "bypass_css": True,  # Better content extraction
        "word_count_threshold": 10  # Minimum content length
    }

    try:
        print("🤖 Sending AI extraction request...")
        start_time = time.time()

        async with httpx.AsyncClient(timeout=180) as client:
            response = await client.post(
                f"{crawl4ai_url}/crawl",
                json=payload,
                headers={"Content-Type": "application/json"}
            )

        end_time = time.time()
        duration = end_time - start_time

        print(f"⏱️  Response time: {duration:.2f} seconds")
        print(f"📊 Status code: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print("✅ AI extraction successful!")

            # Debug: Show full response structure
            print("\n🔍 Full Response Structure:")
            print(f"Keys: {list(result.keys())}")
            if 'results' in result:
                print(f"Number of results: {len(result['results'])}")
                if len(result['results']) > 0:
                    crawl_result = result['results'][0]
                    print(f"Result keys: {list(crawl_result.keys())}")
                    print(f"Success: {crawl_result.get('success', 'N/A')}")
                    print(f"URL: {crawl_result.get('url', 'N/A')}")

            # Extract the AI-parsed content
            if 'results' in result and len(result['results']) > 0:
                crawl_result = result['results'][0]

                if 'extracted_content' in crawl_result:
                    ai_data = crawl_result['extracted_content']
                    print("\n🎯 AI Extracted Data:")
                    if ai_data:
                        print(json.dumps(ai_data, indent=2, ensure_ascii=False))
                    else:
                        print("⚠️  AI returned null/empty data")
                        print("💡 This might indicate:")
                        print("   - Page blocked anti-scraping")
                        print("   - AI couldn't find structured data")
                        print("   - Page requires JavaScript rendering")
                        print("   - Extraction schema too complex")

                        # Show some raw HTML to debug
                        if 'html' in crawl_result:
                            html_preview = crawl_result['html'][:500] + "..." if len(crawl_result['html']) > 500 else crawl_result['html']
                            print(f"\n📄 Raw HTML preview: {html_preview}")

                    # Structure the final response
                    final_result = {
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
                        'extraction_time_seconds': duration,
                        'debug_info': {
                            'crawl_success': crawl_result.get('success'),
                            'has_extracted_content': 'extracted_content' in crawl_result,
                            'html_length': len(crawl_result.get('html', ''))
                        }
                    }

                    print("\n📄 Complete Result Structure:")
                    print(json.dumps(final_result, indent=2, ensure_ascii=False)[:1500] + "...")

                    return final_result
                else:
                    print("❌ No extracted_content in response")
                    print(f"Available keys: {list(crawl_result.keys())}")
            else:
                print("❌ No results in response")
                print(f"Response keys: {list(result.keys())}")
        else:
            print(f"❌ AI extraction failed: {response.status_code}")
            print(f"Response: {response.text[:1000]}")

    except Exception as e:
        print(f"❌ Error during AI extraction: {e}")

    return None

if __name__ == "__main__":
    asyncio.run(test_vietnambooking_ai_extraction())