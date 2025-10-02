#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from airflow import DAG # type: ignore
from airflow.providers.standard.operators.python import PythonOperator # type: ignore
from airflow.providers.standard.operators.bash import BashOperator # type: ignore
import os
import sys
import asyncio
import json
import logging

# Add src to path for imports
sys.path.append('/opt/airflow/src')

default_args = {
    'owner': 'tourism-team',
    'depends_on_past': False,
    'start_date': datetime(2025, 9, 30),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'max_active_runs': 1,
}

dag = DAG(
    'vietnambooking_full_pipeline',
    default_args=default_args,
    description='Complete VietnamBooking crawling pipeline: locations -> hotels -> details',
    schedule=timedelta(days=1),  # Run daily - Updated for Airflow 2.4+
    catchup=False,
    tags=['crawling', 'vietnambooking', 'tourism'],
)

def extract_locations_task(**context):
    """Task 1: Extract all locations"""
    import sys
    import os
    import traceback

    try:
        # Simplified import path - use absolute path from project root
        project_root = '/opt/airflow'
        src_path = os.path.join(project_root, 'src')
        sys.path.insert(0, src_path)

        logging.info(f"Python path: {sys.path[:3]}")
        logging.info(f"Current working directory: {os.getcwd()}")

        # Try to import LocationExtractor
        try:
            from etl.extract.vietnambooking.extract_locations import LocationExtractor
            logging.info("Successfully imported LocationExtractor")
        except ImportError as e:
            logging.error(f"Failed to import LocationExtractor: {e}")
            logging.error(f"Available modules in etl.extract.vietnambooking: {os.listdir(os.path.join(src_path, 'etl/extract/vietnambooking'))}")
            raise

        extractor = LocationExtractor()
        locations = asyncio.run(extractor.extract_locations())

        if not locations:
            logging.warning("No locations extracted")
            return 0

        # Save locations
        output_file = "/opt/airflow/data/raw/vietnambooking/locations.json"
        os.makedirs(os.path.dirname(output_file), exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(locations, f, ensure_ascii=False, indent=2)

        logging.info(f"Successfully extracted {len(locations)} locations")
        return len(locations)

    except Exception as e:
        logging.error(f"Error in extract_locations_task: {e}")
        logging.error(f"Traceback: {traceback.format_exc()}")
        raise

def extract_hotels_batch(**context):
    """Task 2: Extract hotels in batches"""
    import sys
    import os
    import traceback

    try:
        # Simplified import path - use absolute path from project root
        project_root = '/opt/airflow'
        src_path = os.path.join(project_root, 'src')
        sys.path.insert(0, src_path)

        logging.info(f"Python path: {sys.path[:3]}")
        logging.info(f"Current working directory: {os.getcwd()}")

        # Try to import process_locations_batch_enhanced
        try:
            from etl.extract.vietnambooking.enhanced_hotel_extractor import process_locations_batch_enhanced
            logging.info("Successfully imported process_locations_batch_enhanced")
        except ImportError as e:
            logging.error(f"Failed to import process_locations_batch_enhanced: {e}")
            logging.error(f"Available modules in etl.extract.vietnambooking: {os.listdir(os.path.join(src_path, 'etl/extract/vietnambooking'))}")
            raise
        
        # Parameters
        locations_file = "/opt/airflow/data/raw/vietnambooking/locations.json"
        output_dir = "/opt/airflow/data/raw/vietnambooking/"
        batch_size = 10
        
        # Verify locations file exists
        if not os.path.exists(locations_file):
            raise FileNotFoundError(f"Locations file not found: {locations_file}")
        
        # Load locations to get total count
        with open(locations_file, 'r', encoding='utf-8') as f:
            locations = json.load(f)
        
        if not locations:
            logging.warning("No locations found to process")
            return 0
        
        total_locations = len(locations)
        total_hotels = 0
        
        # Process in batches
        for start_idx in range(0, total_locations, batch_size):
            logging.info(f"Processing batch {start_idx}-{min(start_idx + batch_size, total_locations)}")
            
            try:
                hotels = asyncio.run(process_locations_batch_enhanced(
                    locations_file, output_dir, start_idx, batch_size
                ))
                if hotels:
                    total_hotels += len(hotels)
                    logging.info(f"Batch completed: {len(hotels)} hotels extracted")
                else:
                    logging.warning(f"No hotels extracted from batch {start_idx}")
            except Exception as batch_error:
                logging.error(f"Error processing batch {start_idx}: {batch_error}")
                # Continue with next batch instead of failing completely
                continue
        
        logging.info(f"Total hotels extracted: {total_hotels}")
        return total_hotels
        
    except Exception as e:
        logging.error(f"Error in extract_hotels_batch: {e}")
        raise

def merge_hotel_files(**context):
    """Task 3: Merge all hotel batch files"""
    import glob
    import os
    
    try:
        data_dir = "/opt/airflow/data/raw/vietnambooking/"
        
        # Verify data directory exists
        if not os.path.exists(data_dir):
            raise FileNotFoundError(f"Data directory not found: {data_dir}")
        
        all_hotels = []
        
        # Find all enhanced batch files
        pattern = os.path.join(data_dir, "enhanced_hotels_batch_*.json")
        batch_files = glob.glob(pattern)
        batch_files.sort()
        
        logging.info(f"Found {len(batch_files)} batch files to merge")
        
        if not batch_files:
            logging.warning("No batch files found to merge")
            return 0
        
        for batch_file in batch_files:
            try:
                with open(batch_file, 'r', encoding='utf-8') as f:
                    batch_data = json.load(f)
                    if batch_data:  # Only extend if data is not empty
                        all_hotels.extend(batch_data)
                        logging.info(f"Merged {len(batch_data)} hotels from {batch_file}")
                    else:
                        logging.warning(f"Empty batch file: {batch_file}")
            except Exception as e:
                logging.error(f"Error merging {batch_file}: {e}")
                # Continue processing other files
                continue
        
        if not all_hotels:
            logging.error("No hotels found after merging all batch files")
            raise ValueError("No hotels data to process")
        
        # Save merged file
        output_file = os.path.join(data_dir, "all_hotels_enhanced.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_hotels, f, ensure_ascii=False, indent=2)
        
        # Generate statistics
        location_stats = {}
        for hotel in all_hotels:
            try:
                location = hotel.get('location_name', 'Unknown')
                if location not in location_stats:
                    location_stats[location] = 0
                location_stats[location] += 1
            except Exception as e:
                logging.warning(f"Error processing hotel stats: {e}")
                continue
        
        stats = {
            'total_hotels': len(all_hotels),
            'total_locations': len(location_stats),
            'extraction_date': datetime.now().isoformat(),
            'by_location': location_stats
        }
        
        stats_file = os.path.join(data_dir, "extraction_stats.json")
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        
        logging.info(f"Successfully merged {len(all_hotels)} hotels from {len(location_stats)} locations")
        return len(all_hotels)
        
    except Exception as e:
        logging.error(f"Error in merge_hotel_files: {e}")
        raise

def extract_hotel_details(**context):
    """Task 4: Extract detailed information for each hotel"""
    import sys
    import os
    import traceback

    try:
        # Simplified import path - use absolute path from project root
        project_root = '/opt/airflow'
        src_path = os.path.join(project_root, 'src')
        sys.path.insert(0, src_path)

        logging.info(f"Python path: {sys.path[:3]}")
        logging.info(f"Current working directory: {os.getcwd()}")

        # Try to import process_hotels_for_details
        try:
            from etl.extract.vietnambooking.hotel_details_extractor import process_hotels_for_details
            logging.info("Successfully imported process_hotels_for_details")
        except ImportError as e:
            logging.error(f"Failed to import process_hotels_for_details: {e}")
            logging.error(f"Available modules in etl.extract.vietnambooking: {os.listdir(os.path.join(src_path, 'etl/extract/vietnambooking'))}")
            raise
        
        # Parameters
        hotels_file = "/opt/airflow/data/raw/vietnambooking/all_hotels_enhanced.json"
        output_dir = "/opt/airflow/data/raw/vietnambooking/details/"
        batch_size = 100  # Process 100 hotels per batch
        
        # Verify hotels file exists
        if not os.path.exists(hotels_file):
            raise FileNotFoundError(f"Hotels file not found: {hotels_file}")
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Load hotels to get total count
        with open(hotels_file, 'r', encoding='utf-8') as f:
            hotels = json.load(f)
        
        if not hotels:
            logging.warning("No hotels found to process details")
            return 0
        
        total_hotels = len(hotels)
        total_details = 0
        
        # Process in batches
        for start_idx in range(0, total_hotels, batch_size):
            logging.info(f"Processing details batch {start_idx}-{min(start_idx + batch_size, total_hotels)}")
            
            try:
                details = asyncio.run(process_hotels_for_details(
                    hotels_file, output_dir, start_idx, batch_size
                ))
                if details:
                    total_details += len(details)
                    logging.info(f"Details batch completed: {len(details)} hotels processed")
                else:
                    logging.warning(f"No details extracted from batch {start_idx}")
            except Exception as batch_error:
                logging.error(f"Error processing details batch {start_idx}: {batch_error}")
                # Continue with next batch instead of failing completely
                continue
        
        logging.info(f"Total hotel details extracted: {total_details}")
        return total_details
        
    except Exception as e:
        logging.error(f"Error in extract_hotel_details: {e}")
        raise

def merge_hotel_details(**context):
    """Task 5: Merge all hotel details batch files"""
    import glob
    import os
    
    try:
        data_dir = "/opt/airflow/data/raw/vietnambooking/details/"
        
        # Verify details directory exists
        if not os.path.exists(data_dir):
            logging.warning(f"Details directory not found: {data_dir}")
            return 0
        
        all_details = []
        
        # Find all details batch files
        pattern = os.path.join(data_dir, "hotel_details_batch_*.json")
        batch_files = glob.glob(pattern)
        batch_files.sort()
        
        logging.info(f"Found {len(batch_files)} details batch files to merge")
        
        if not batch_files:
            logging.warning("No details batch files found to merge")
            return 0
        
        for batch_file in batch_files:
            try:
                with open(batch_file, 'r', encoding='utf-8') as f:
                    batch_data = json.load(f)
                    if batch_data:  # Only extend if data is not empty
                        all_details.extend(batch_data)
                        logging.info(f"Merged {len(batch_data)} hotel details from {batch_file}")
                    else:
                        logging.warning(f"Empty details batch file: {batch_file}")
            except Exception as e:
                logging.error(f"Error merging {batch_file}: {e}")
                # Continue processing other files
                continue
        
        # Save merged details file
        output_file = os.path.join("/opt/airflow/data/raw/vietnambooking/", "all_hotel_details.json")
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_details, f, ensure_ascii=False, indent=2)
        
        logging.info(f"Successfully merged {len(all_details)} hotel details")
        return len(all_details)
        
    except Exception as e:
        logging.error(f"Error in merge_hotel_details: {e}")
        raise

def validate_results(**context):
    """Task 6: Validate extraction results"""
    import os
    
    try:
        data_dir = "/opt/airflow/data/raw/vietnambooking/"
        
        # Verify data directory exists
        if not os.path.exists(data_dir):
            raise FileNotFoundError(f"Data directory not found: {data_dir}")
        
        # Load results with error handling
        locations_file = os.path.join(data_dir, "locations.json")
        hotels_file = os.path.join(data_dir, "all_hotels_enhanced.json")
        details_file = os.path.join(data_dir, "all_hotel_details.json")
        stats_file = os.path.join(data_dir, "extraction_stats.json")
        
        # Check if required files exist
        required_files = {
            'locations': locations_file,
            'hotels': hotels_file,
            'stats': stats_file
        }
        
        for name, file_path in required_files.items():
            if not os.path.exists(file_path):
                logging.error(f"Required file missing: {name} at {file_path}")
                raise FileNotFoundError(f"Required file missing: {name}")
        
        # Load locations
        with open(locations_file, 'r', encoding='utf-8') as f:
            locations = json.load(f)
        
        # Load hotels
        with open(hotels_file, 'r', encoding='utf-8') as f:
            hotels = json.load(f)
        
        # Load stats
        with open(stats_file, 'r', encoding='utf-8') as f:
            stats = json.load(f)
        
        # Load hotel details (optional)
        hotel_details = []
        details_total = 0
        details_success_rate = 0
        
        if os.path.exists(details_file):
            try:
                with open(details_file, 'r', encoding='utf-8') as f:
                    hotel_details = json.load(f)
                details_total = len(hotel_details)
                
                # Calculate success rate for details extraction
                successful_details = sum(1 for detail in hotel_details if detail.get('extraction_success', False))
                details_success_rate = successful_details / details_total * 100 if details_total > 0 else 0
            except Exception as e:
                logging.warning(f"Could not load hotel details: {e}")
        
        # Calculate coverage
        expected_total = sum(loc.get('hotel_count', 0) for loc in locations)
        actual_total = len(hotels)
        coverage = (actual_total / expected_total * 100) if expected_total > 0 else 0
        details_coverage = (details_total / actual_total * 100) if actual_total > 0 else 0
        
        validation_result = {
            'validation_date': datetime.now().isoformat(),
            'locations_expected': len(locations),
            'locations_actual': stats.get('total_locations', 0),
            'hotels_expected': expected_total,
            'hotels_actual': actual_total,
            'details_extracted': details_total,
            'coverage_percentage': coverage,
            'details_coverage_percentage': details_coverage,
            'details_success_rate': details_success_rate,
            'status': 'PASS' if coverage > 5 and (details_total == 0 or details_success_rate > 50) else 'FAIL',
            'recommendations': []
        }
        
        # Generate recommendations based on results
        if coverage < 30:
            validation_result['recommendations'].append('Consider improving extraction logic for better coverage')
        if stats.get('total_locations', 0) < len(locations):
            validation_result['recommendations'].append('Some locations were not processed successfully')
        if details_total > 0 and details_success_rate < 70:
            validation_result['recommendations'].append('Improve hotel details extraction logic - success rate too low')
        if details_total > 0 and details_coverage < 80:
            validation_result['recommendations'].append('Some hotels missing detailed information')
        
        # Save validation results
        validation_file = os.path.join(data_dir, "validation_results.json")
        with open(validation_file, 'w', encoding='utf-8') as f:
            json.dump(validation_result, f, ensure_ascii=False, indent=2)
        
        logging.info(f"Validation completed: {coverage:.1f}% hotels coverage, {details_success_rate:.1f}% details success rate")
        
        # More lenient failure conditions for initial testing
        if coverage < 1:
            raise ValueError(f"Hotels coverage too low: {coverage:.1f}%. Please check extraction logic.")
        if details_total > 0 and details_success_rate < 30:
            raise ValueError(f"Details success rate too low: {details_success_rate:.1f}%. Please check details extraction logic.")
        
        return validation_result
        
    except Exception as e:
        logging.error(f"Error in validate_results: {e}")
        raise

# Define tasks
extract_locations = PythonOperator(
    task_id='extract_locations',
    python_callable=extract_locations_task,
    dag=dag,
)

extract_hotels = PythonOperator(
    task_id='extract_hotels',
    python_callable=extract_hotels_batch,
    dag=dag,
)

merge_hotels = PythonOperator(
    task_id='merge_hotels',
    python_callable=merge_hotel_files,
    dag=dag,
)

extract_details = PythonOperator(
    task_id='extract_hotel_details',
    python_callable=extract_hotel_details,
    dag=dag,
)

merge_details = PythonOperator(
    task_id='merge_hotel_details',
    python_callable=merge_hotel_details,
    dag=dag,
)

validate_pipeline = PythonOperator(
    task_id='validate_results',
    python_callable=validate_results,
    dag=dag,
)

# Create data directories
create_dirs = BashOperator(
    task_id='create_directories',
    bash_command='''
        echo "Creating directories..."
        mkdir -p /opt/airflow/data/raw/vietnambooking /opt/airflow/data/processed/vietnambooking
        echo "Directories created successfully"
        ls -la /opt/airflow/data/
        echo "Task completed"
    ''',
    dag=dag,
)

# Cleanup old files
cleanup = BashOperator(
    task_id='cleanup_old_files',
    bash_command='''
        cd /opt/airflow/data/raw/vietnambooking
        find . -name "enhanced_hotels_batch_*.json" -mtime +7 -delete
        find . -name "hotels_batch_*.json" -mtime +7 -delete
    ''',
    dag=dag,
)

# Set task dependencies  
create_dirs >> extract_locations >> extract_hotels >> merge_hotels >> extract_details >> merge_details >> validate_pipeline >> cleanup