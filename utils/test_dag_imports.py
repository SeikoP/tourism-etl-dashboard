#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to validate DAG imports and modules
"""

import sys
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_dag_imports():
    """Test if all DAG imports work correctly"""
    
    # Add src to path
    src_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src')
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
    
    logger.info(f"Added src path: {src_path}")
    logger.info(f"Python path: {sys.path[:3]}")
    
    # Test 1: Basic Airflow imports
    try:
        from airflow import DAG
        from airflow.providers.standard.operators.python import PythonOperator
        from airflow.providers.standard.operators.bash import BashOperator
        logger.info("✓ Airflow imports successful")
    except ImportError as e:
        logger.error(f"✗ Airflow imports failed: {e}")
        return False
    
    # Test 2: Extract modules
    modules_to_test = [
        ('src.etl.extract.vietnambooking.extract_locations', 'LocationExtractor'),
        ('src.etl.extract.vietnambooking.enhanced_hotel_extractor', 'process_locations_batch_enhanced'),
        ('src.etl.extract.vietnambooking.hotel_details_extractor', 'process_hotels_for_details')
    ]
    
    for module_name, class_or_func in modules_to_test:
        try:
            module = __import__(module_name, fromlist=[class_or_func])
            getattr(module, class_or_func)
            logger.info(f"✓ {module_name}.{class_or_func} import successful")
        except ImportError as e:
            logger.error(f"✗ {module_name}.{class_or_func} import failed: {e}")
            
            # Try alternative import method
            try:
                alt_module_path = module_name.replace('src.', '')
                sys.path.append(os.path.join(src_path, 'etl', 'extract', 'vietnambooking'))
                alt_module = __import__(alt_module_path.split('.')[-1], fromlist=[class_or_func])
                getattr(alt_module, class_or_func)
                logger.info(f"✓ {module_name}.{class_or_func} alternative import successful")
            except Exception as alt_e:
                logger.error(f"✗ {module_name}.{class_or_func} alternative import also failed: {alt_e}")
                return False
        except AttributeError as e:
            logger.error(f"✗ {class_or_func} not found in {module_name}: {e}")
            return False
    
    return True

def test_file_structure():
    """Test if required files and directories exist"""
    base_dir = os.path.dirname(os.path.dirname(__file__))
    
    required_files = [
        'src/etl/extract/vietnambooking/__init__.py',
        'src/etl/extract/vietnambooking/extract_locations.py',
        'src/etl/extract/vietnambooking/enhanced_hotel_extractor.py',
        'src/etl/extract/vietnambooking/hotel_details_extractor.py',
    ]
    
    for file_path in required_files:
        full_path = os.path.join(base_dir, file_path)
        if os.path.exists(full_path):
            logger.info(f"✓ {file_path} exists")
        else:
            logger.error(f"✗ {file_path} missing")
            return False
    
    return True

if __name__ == "__main__":
    logger.info("Testing DAG imports and file structure...")
    
    structure_ok = test_file_structure()
    imports_ok = test_dag_imports()
    
    if structure_ok and imports_ok:
        logger.info("✓ All tests passed!")
        sys.exit(0)
    else:
        logger.error("✗ Some tests failed!")
        sys.exit(1)