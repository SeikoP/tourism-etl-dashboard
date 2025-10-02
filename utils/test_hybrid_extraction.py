#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import json
import time
import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from etl.extract.vietnambooking.ai_hotel_details_extractor import AIHotelDetailsExtractor

async def test_hybrid_extraction():
    """Test the hybrid AI + BeautifulSoup extraction"""

    # Sample hotel data
    hotel = {
        "location_name": "Vũng Tàu",
        "location_code": "vung-tau",
        "url": "https://www.vietnambooking.com/hotel/vietnam/khach-san-vias-vung-tau.html",
        "name": "Khách sạn Vias Vũng Tàu"
    }

    print(f"🔬 Testing hybrid extraction for: {hotel['name']}")
    print(f"🌐 URL: {hotel['url']}")
    print()

    extractor = AIHotelDetailsExtractor()

    start_time = time.time()
    result = await extractor.extract_hotel_details_ai(hotel)
    end_time = time.time()

    print(f"⏱️  Total extraction time: {end_time - start_time:.2f} seconds")
    print(f"📊 Extraction method: {result.get('extraction_method', 'unknown')}")
    print(f"✅ Success: {result.get('extraction_success', False)}")
    print(f"🤖 AI success: {result.get('ai_extraction_success', False)}")
    print(f"🧽 Basic success: {result.get('basic_extraction_success', False)}")
    print()

    if result.get('extraction_success'):
        extracted_data = result.get('extracted_data', {})

        print("📋 Extracted Data Summary:")
        print(f"🏨 Hotel name: {extracted_data.get('hotel_name', 'N/A')}")
        print(f"📍 Address: {extracted_data.get('address', 'N/A')}")
        print(f"📞 Phone: {extracted_data.get('phone', 'N/A')}")
        print(f"💰 Price range: {extracted_data.get('price_range', 'N/A')}")
        print(f"⭐ Star rating: {extracted_data.get('star_rating', 'N/A')}")

        amenities = extracted_data.get('basic_amenities', [])
        print(f"🏊 Basic amenities: {len(amenities)} found")
        if amenities:
            print(f"   {amenities[:3]}...")  # Show first 3

        # Check for AI-enhanced data
        if result.get('ai_extraction_success'):
            print("🎯 AI-enhanced data available!")
            ai_fields = ['description', 'room_descriptions', 'complex_amenities', 'policies', 'nearby_attractions']
            for field in ai_fields:
                if field in extracted_data and extracted_data[field]:
                    if isinstance(extracted_data[field], list):
                        print(f"   {field}: {len(extracted_data[field])} items")
                    else:
                        preview = str(extracted_data[field])[:100] + "..." if len(str(extracted_data[field])) > 100 else str(extracted_data[field])
                        print(f"   {field}: {preview}")
        else:
            print("⚠️  AI extraction failed, using basic data only")

        print("\n📄 Full Result Structure:")
        print(json.dumps(result, indent=2, ensure_ascii=False)[:2000] + "...")

        # Save to file
        output_file = f"utils/hybrid_extraction_test_{int(time.time())}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n💾 Saved full results to: {output_file}")

    else:
        print("❌ Extraction failed!")
        print(f"Error: {result.get('error', 'Unknown error')}")

    return result

if __name__ == "__main__":
    asyncio.run(test_hybrid_extraction())