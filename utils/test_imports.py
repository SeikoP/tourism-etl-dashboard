#!/usr/bin/env python3
"""
Test script to verify import paths work correctly in Airflow container
"""

import sys
import os

# Simulate Airflow container environment
sys.path.insert(0, '/opt/airflow/src')

def test_imports():
    """Test all import paths that DAGs will use"""
    
    try:
        print("Testing import paths...")
        print(f"Python path: {sys.path}")
        
        # Test 1: Extract locations import
        print("\n1. Testing extract_locations import...")
        from etl.extract.vietnambooking.extract_locations import LocationExtractor
        print("✅ extract_locations import successful")
        
        # Test 2: Enhanced hotel extractor import  
        print("\n2. Testing enhanced_hotel_extractor import...")
        from etl.extract.vietnambooking.enhanced_hotel_extractor import process_locations_batch_enhanced
        print("✅ enhanced_hotel_extractor import successful")
        
        # Test 3: Hotel details extractor import
        print("\n3. Testing hotel_details_extractor import...")
        from etl.extract.vietnambooking.hotel_details_extractor import process_hotels_for_details
        print("✅ hotel_details_extractor import successful")
        
        # Test 4: Services import (for crawl4ai DAG)
        print("\n4. Testing services import...")
        from services.crawl4ai_integration import test_crawl4ai_connection
        print("✅ services import successful")
        
        print("\n🎉 All imports working correctly!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    # Change to project root for testing
    if '/opt/airflow/src' not in sys.path:
        # Local testing - add src to path
        project_root = os.path.dirname(os.path.abspath(__file__))
        src_path = os.path.join(project_root, 'src')
        sys.path.insert(0, src_path)
        print(f"Added local src path: {src_path}")
    
    success = test_imports()
    exit(0 if success else 1)