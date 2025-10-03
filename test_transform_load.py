#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test script để validate transform và load với cấu trúc dữ liệu mới
"""

import sys
import os
import json
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_transform_and_load():
    """Test transform và load với sample data"""

    from etl.transform.data_transformer import DataTransformer
    from etl.load.data_loader import DataLoader

    print("=== Testing Transform & Load với cấu trúc dữ liệu mới ===")

    # Sample hotel data (từ ai_hotel_details_extractor output)
    sample_hotel_detail = {
        'basic_info': {
            'location_name': 'Hà Nội',
            'location_code': 'HN',
            'url': 'https://www.vietnambooking.com/hotel/vietnam/sample-hotel.html',
            'name': 'Sample Hotel Hà Nội'
        },
        'extracted_data': {
            'address': '123 Đường ABC, Hà Nội',
            'phone': '+84 123 456 789',
            'star_rating': 4.5,
            'description': 'Khách sạn sang trọng ở trung tâm Hà Nội',
            'basic_amenities': ['WiFi miễn phí', 'Hồ bơi', 'Nhà hàng', 'Đỗ xe'],
            'room_descriptions': ['Phòng Superior với view thành phố', 'Phòng Deluxe với ban công'],
            'policies': ['Check-in từ 14:00', 'Check-out trước 12:00'],
            'nearby_attractions': ['Hoàn Kiếm Lake', 'Temple of Literature'],
            'price_analysis': {
                'min_price': 1500000,
                'max_price': 3000000,
                'avg_price': 2250000,
                'currency': 'VND'
            }
        },
        'extraction_method': 'hybrid_ai_beautifulsoup',
        'extraction_date': datetime.now().isoformat(),
        'extraction_success': True,
        'ai_extraction_success': True,
        'basic_extraction_success': True
    }

    # Test DataTransformer
    print("\n1. Testing DataTransformer...")
    transformer = DataTransformer()

    result = transformer._validate_and_clean_hotel_detail(sample_hotel_detail)

    if result.is_valid:
        print("✅ Transform successful!")
        print(f"   - Errors: {len(result.errors)}")
        print(f"   - Warnings: {len(result.warnings)}")
        print(f"   - Cleaned data keys: {list(result.cleaned_data.keys())}")
    else:
        print("❌ Transform failed!")
        print(f"   - Errors: {result.errors}")
        return False

    # Test DataLoader (nếu có database connection)
    print("\n2. Testing DataLoader...")
    try:
        loader = DataLoader()

        # Test database connection
        stats = loader.get_database_stats()
        print("✅ Database connection successful!")
        print(f"   - Locations: {stats.get('locations_count', 0)}")
        print(f"   - Hotels: {stats.get('hotels_count', 0)}")
        print(f"   - Details: {stats.get('details_count', 0)}")

        # Test loading sample data
        # Note: This would require actual location and hotel records in DB
        print("   - Note: Full load test requires existing location/hotel records")

    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("   - This is expected if PostgreSQL is not running")
        return False

    print("\n=== Test completed successfully! ===")
    return True

if __name__ == "__main__":
    test_transform_and_load()