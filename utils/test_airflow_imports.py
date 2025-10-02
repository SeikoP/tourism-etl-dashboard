#!/usr/bin/env python3
"""
Test DAG import paths directly trong Airflow worker container
Chạy script này trong container để test imports
"""

def test_airflow_imports():
    """Test imports exactly như trong Airflow tasks"""
    
    import sys
    import os
    import logging
    
    print("🧪 Testing Airflow DAG imports...")
    print(f"Python version: {sys.version}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Python path: {sys.path[:5]}")
    
    # Test 1: Basic path setup
    print("\n1️⃣ Testing basic path setup...")
    src_path = '/opt/airflow/src'
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
        print(f"✅ Added {src_path} to sys.path")
    
    # Test 2: Direct module path approach  
    print("\n2️⃣ Testing direct module path...")
    module_path = '/opt/airflow/src/etl/extract/vietnambooking'  
    sys.path.append(module_path)
    print(f"✅ Added {module_path} to sys.path")
    
    # Test 3: Import extract_locations
    print("\n3️⃣ Testing extract_locations import...")
    try:
        from extract_locations import LocationExtractor
        print("✅ extract_locations import successful")
        print(f"LocationExtractor class: {LocationExtractor}")
    except Exception as e:
        print(f"❌ extract_locations import failed: {e}")
        
    # Test 4: Import enhanced_hotel_extractor  
    print("\n4️⃣ Testing enhanced_hotel_extractor import...")
    try:
        from enhanced_hotel_extractor import process_locations_batch_enhanced
        print("✅ enhanced_hotel_extractor import successful")
        print(f"process_locations_batch_enhanced function: {process_locations_batch_enhanced}")
    except Exception as e:
        print(f"❌ enhanced_hotel_extractor import failed: {e}")
        
    # Test 5: Import ai_hotel_details_extractor
    print("\n5️⃣ Testing ai_hotel_details_extractor import...")
    try:
        from ai_hotel_details_extractor import process_hotels_with_ai
        print("✅ ai_hotel_details_extractor import successful") 
        print(f"process_hotels_with_ai function: {process_hotels_with_ai}")
    except Exception as e:
        print(f"❌ ai_hotel_details_extractor import failed: {e}")
        
    # Test 6: List available files
    print("\n6️⃣ Checking file system...")
    vietnambooking_path = '/opt/airflow/src/etl/extract/vietnambooking'
    if os.path.exists(vietnambooking_path):
        files = os.listdir(vietnambooking_path)
        print(f"✅ Files in {vietnambooking_path}: {files}")
    else:
        print(f"❌ Directory not found: {vietnambooking_path}")
        
    print("\n🎯 Test completed!")

if __name__ == "__main__":
    test_airflow_imports()