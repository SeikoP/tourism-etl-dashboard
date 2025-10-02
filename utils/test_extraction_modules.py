#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple test script to validate extraction modules
"""

import sys
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_extraction_modules():
    """Test if extraction modules can be imported"""
    
    # Add src to path
    src_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src')
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
    
    logger.info(f"Added src path: {src_path}")
    
    # Test extraction modules
    try:
        # Add module path for direct imports
        vietnambooking_path = os.path.join(src_path, 'etl', 'extract', 'vietnambooking')
        sys.path.append(vietnambooking_path)
        
        from extract_locations import LocationExtractor
        logger.info("✓ LocationExtractor import successful")
        
        # Test basic instantiation
        extractor = LocationExtractor()
        logger.info("✓ LocationExtractor instantiation successful")
        
    except ImportError as e:
        logger.error(f"✗ LocationExtractor import failed: {e}")
        return False
    except Exception as e:
        logger.error(f"✗ LocationExtractor instantiation failed: {e}")
        return False
    
    try:
        # Add module path for direct imports
        sys.path.append(os.path.join(src_path, 'etl', 'extract', 'vietnambooking'))
        from enhanced_hotel_extractor import process_locations_batch_enhanced
        logger.info("✓ process_locations_batch_enhanced import successful")
        
    except ImportError as e:
        logger.error(f"✗ process_locations_batch_enhanced import failed: {e}")
        return False
    
    try:
        from ai_hotel_details_extractor import process_hotels_with_ai
        logger.info("✓ process_hotels_for_details import successful")
        
    except ImportError as e:
        logger.error(f"✗ process_hotels_for_details import failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    logger.info("Testing extraction modules...")
    
    if test_extraction_modules():
        logger.info("✓ All extraction modules imported successfully!")
        sys.exit(0)
    else:
        logger.error("✗ Some extraction modules failed to import!")
        sys.exit(1)