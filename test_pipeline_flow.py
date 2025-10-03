#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test script để chạy luồng transform và load với data thật
"""

import sys
import os
import json
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_transform_load_pipeline():
    """Test toàn bộ luồng transform và load với data thật"""

    from etl.transform.data_transformer import DataTransformer
    from etl.load.data_loader import DataLoader

    print("🚀 Testing Transform & Load Pipeline với data thật")
    print("=" * 60)

    # Khởi tạo components
    transformer = DataTransformer()
    loader = DataLoader()

    # Kiểm tra database connection
    print("\n1. Kiểm tra database connection...")
    try:
        db_stats = loader.get_database_stats()
        print("✅ Database connected!")
        print(f"   - Locations: {db_stats['locations_count']}")
        print(f"   - Hotels: {db_stats['hotels_count']}")
        print(f"   - Details: {db_stats['details_count']}")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

    # Load raw data
    print("\n2. Loading raw data...")
    hotels_file = "data/raw/vietnambooking/all_hotels_enhanced.json"
    details_file = "data/raw/vietnambooking/details/ai_hotel_details_batch_0.json"

    if not os.path.exists(hotels_file):
        print(f"❌ Hotels file not found: {hotels_file}")
        return False

    if not os.path.exists(details_file):
        print(f"❌ Details file not found: {details_file}")
        return False

    # Load hotels data
    with open(hotels_file, 'r', encoding='utf-8') as f:
        hotels_data = json.load(f)

    # Load details data
    with open(details_file, 'r', encoding='utf-8') as f:
        details_data = json.load(f)

    print(f"✅ Loaded {len(hotels_data)} hotels và {len(details_data)} details")

    # Transform hotels (chỉ lấy 5 hotels đầu để test)
    print("\n3. Transforming hotels data...")
    transformed_hotels = []
    hotels_to_process = hotels_data[:5]  # Test với 5 hotels đầu

    for i, hotel in enumerate(hotels_to_process):
        try:
            result = transformer._validate_and_clean_hotel(hotel)
            if result.is_valid:
                transformed_hotels.append(result.cleaned_data)
                logger.info(f"✅ Hotel {i+1}: {hotel['name']} - transformed successfully")
                if result.warnings:
                    logger.warning(f"⚠️  Warnings: {result.warnings}")
            else:
                logger.error(f"❌ Hotel {i+1}: {hotel['name']} - validation failed: {result.errors}")
        except Exception as e:
            logger.error(f"❌ Error transforming hotel {i+1}: {e}")

    print(f"✅ Transformed {len(transformed_hotels)}/{len(hotels_to_process)} hotels")

    # Transform details
    print("\n4. Transforming details data...")
    transformed_details = []

    for i, detail in enumerate(details_data):
        try:
            result = transformer._validate_and_clean_hotel_detail(detail)
            if result.is_valid:
                transformed_details.append(result.cleaned_data)
                logger.info(f"✅ Detail {i+1}: {detail['basic_info']['name']} - transformed successfully")
                if result.warnings:
                    logger.warning(f"⚠️  Warnings: {result.warnings}")
            else:
                logger.error(f"❌ Detail {i+1}: {detail['basic_info']['name']} - validation failed: {result.errors}")
        except Exception as e:
            logger.error(f"❌ Error transforming detail {i+1}: {e}")

    print(f"✅ Transformed {len(transformed_details)}/{len(details_data)} details")

    # Load to database
    print("\n5. Loading to database...")

    # Load hotels
    hotels_loaded = 0
    if transformed_hotels:
        try:
            result = loader.load_hotels_batch(transformed_hotels)
            hotels_loaded = result if isinstance(result, int) else len(transformed_hotels)
            print(f"✅ Loaded {hotels_loaded} hotels to database")
        except Exception as e:
            logger.error(f"❌ Error loading hotels: {e}")

    # Load details
    details_loaded = 0
    if transformed_details:
        try:
            # Save to temp file for loading
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
                json.dump(transformed_details, f, ensure_ascii=False, indent=2)
                temp_file = f.name

            result = loader.load_hotel_details(temp_file)
            details_loaded = result['inserted'] + result['updated']

            # Clean up
            os.unlink(temp_file)

            print(f"✅ Loaded {details_loaded} details to database")
            print(f"   - Inserted: {result['inserted']}")
            print(f"   - Updated: {result['updated']}")
            print(f"   - Errors: {result['errors']}")

        except Exception as e:
            logger.error(f"❌ Error loading details: {e}")

    # Final stats
    print("\n6. Final database stats...")
    try:
        final_stats = loader.get_database_stats()
        print("✅ Final state:")
        print(f"   - Locations: {final_stats['locations_count']}")
        print(f"   - Hotels: {final_stats['hotels_count']}")
        print(f"   - Details: {final_stats['details_count']}")
    except Exception as e:
        logger.error(f"❌ Error getting final stats: {e}")

    print("\n" + "=" * 60)
    print("🎉 Transform & Load Pipeline Test Completed!")
    print(f"📊 Results: {hotels_loaded} hotels, {details_loaded} details loaded")
    print("=" * 60)

    return hotels_loaded > 0 or details_loaded > 0

if __name__ == "__main__":
    success = test_transform_load_pipeline()
    exit(0 if success else 1)