#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from airflow import DAG # type: ignore
from airflow.operators.python import PythonOperator # type: ignore
from airflow.operators.bash import BashOperator # type: ignore
import os
import sys
import asyncio
import json
import logging

# Add src to path
sys.path.append('/opt/airflow/dags/src')

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
    schedule_interval=timedelta(days=1),  # Run daily
    catchup=False,
    tags=['crawling', 'vietnambooking', 'tourism'],
)

def extract_locations_task(**context):
    """Task 1: Extract all locations"""
    from src.etl.extract.vietnambooking.extract_locations import LocationExtractor
    
    extractor = LocationExtractor()
    locations = asyncio.run(extractor.extract_locations())
    
    # Save locations
    output_file = "/opt/airflow/data/raw/vietnambooking/locations.json"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(locations, f, ensure_ascii=False, indent=2)
    
    logging.info(f"Extracted {len(locations)} locations")
    return len(locations)

def extract_hotels_batch(**context):
    """Task 2: Extract hotels in batches"""
    from src.etl.extract.vietnambooking.enhanced_hotel_extractor import process_locations_batch_enhanced
    
    # Parameters
    locations_file = "/opt/airflow/data/raw/vietnambooking/locations.json"
    output_dir = "/opt/airflow/data/raw/vietnambooking/"
    batch_size = 10
    
    # Load locations to get total count
    with open(locations_file, 'r', encoding='utf-8') as f:
        locations = json.load(f)
    
    total_locations = len(locations)
    total_hotels = 0
    
    # Process in batches
    for start_idx in range(0, total_locations, batch_size):
        logging.info(f"Processing batch {start_idx}-{min(start_idx + batch_size, total_locations)}")
        
        hotels = asyncio.run(process_locations_batch_enhanced(
            locations_file, output_dir, start_idx, batch_size
        ))
        total_hotels += len(hotels)
        
        logging.info(f"Batch completed: {len(hotels)} hotels extracted")
    
    logging.info(f"Total hotels extracted: {total_hotels}")
    return total_hotels

def merge_hotel_files(**context):
    """Task 3: Merge all hotel batch files"""
    import glob
    
    data_dir = "/opt/airflow/data/raw/vietnambooking/"
    all_hotels = []
    
    # Find all enhanced batch files
    pattern = os.path.join(data_dir, "enhanced_hotels_batch_*.json")
    batch_files = glob.glob(pattern)
    batch_files.sort()
    
    logging.info(f"Found {len(batch_files)} batch files to merge")
    
    for batch_file in batch_files:
        try:
            with open(batch_file, 'r', encoding='utf-8') as f:
                batch_data = json.load(f)
                all_hotels.extend(batch_data)
                logging.info(f"Merged {len(batch_data)} hotels from {batch_file}")
        except Exception as e:
            logging.error(f"Error merging {batch_file}: {e}")
    
    # Save merged file
    output_file = os.path.join(data_dir, "all_hotels_enhanced.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_hotels, f, ensure_ascii=False, indent=2)
    
    # Generate statistics
    location_stats = {}
    for hotel in all_hotels:
        location = hotel['location_name']
        if location not in location_stats:
            location_stats[location] = 0
        location_stats[location] += 1
    
    stats = {
        'total_hotels': len(all_hotels),
        'total_locations': len(location_stats),
        'extraction_date': datetime.now().isoformat(),
        'by_location': location_stats
    }
    
    stats_file = os.path.join(data_dir, "extraction_stats.json")
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    
    logging.info(f"Merged {len(all_hotels)} hotels from {len(location_stats)} locations")
    return len(all_hotels)

def extract_hotel_details(**context):
    """Task 4: Extract detailed information for each hotel"""
    from src.etl.extract.vietnambooking.hotel_details_extractor import process_hotels_for_details
    
    # Parameters
    hotels_file = "/opt/airflow/data/raw/vietnambooking/all_hotels_enhanced.json"
    output_dir = "/opt/airflow/data/raw/vietnambooking/details/"
    batch_size = 100  # Process 100 hotels per batch
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Load hotels to get total count
    with open(hotels_file, 'r', encoding='utf-8') as f:
        hotels = json.load(f)
    
    total_hotels = len(hotels)
    total_details = 0
    
    # Process in batches
    for start_idx in range(0, total_hotels, batch_size):
        logging.info(f"Processing details batch {start_idx}-{min(start_idx + batch_size, total_hotels)}")
        
        details = asyncio.run(process_hotels_for_details(
            hotels_file, output_dir, start_idx, batch_size
        ))
        total_details += len(details)
        
        logging.info(f"Details batch completed: {len(details)} hotels processed")
    
    logging.info(f"Total hotel details extracted: {total_details}")
    return total_details

def merge_hotel_details(**context):
    """Task 5: Merge all hotel details batch files"""
    import glob
    
    data_dir = "/opt/airflow/data/raw/vietnambooking/details/"
    all_details = []
    
    # Find all details batch files
    pattern = os.path.join(data_dir, "hotel_details_batch_*.json")
    batch_files = glob.glob(pattern)
    batch_files.sort()
    
    logging.info(f"Found {len(batch_files)} details batch files to merge")
    
    for batch_file in batch_files:
        try:
            with open(batch_file, 'r', encoding='utf-8') as f:
                batch_data = json.load(f)
                all_details.extend(batch_data)
                logging.info(f"Merged {len(batch_data)} hotel details from {batch_file}")
        except Exception as e:
            logging.error(f"Error merging {batch_file}: {e}")
    
    # Save merged details file
    output_file = os.path.join("/opt/airflow/data/raw/vietnambooking/", "all_hotel_details.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_details, f, ensure_ascii=False, indent=2)
    
    logging.info(f"Merged {len(all_details)} hotel details")
    return len(all_details)

def validate_results(**context):
    """Task 6: Validate extraction results"""
    data_dir = "/opt/airflow/data/raw/vietnambooking/"
    
    # Load results
    with open(os.path.join(data_dir, "locations.json"), 'r', encoding='utf-8') as f:
        locations = json.load(f)
    
    with open(os.path.join(data_dir, "all_hotels_enhanced.json"), 'r', encoding='utf-8') as f:
        hotels = json.load(f)
    
    with open(os.path.join(data_dir, "all_hotel_details.json"), 'r', encoding='utf-8') as f:
        hotel_details = json.load(f)
    
    with open(os.path.join(data_dir, "extraction_stats.json"), 'r', encoding='utf-8') as f:
        stats = json.load(f)
    
    # Calculate coverage
    expected_total = sum(loc['hotel_count'] for loc in locations)
    actual_total = len(hotels)
    details_total = len(hotel_details)
    coverage = actual_total / expected_total * 100
    details_coverage = details_total / actual_total * 100 if actual_total > 0 else 0
    
    # Calculate success rate for details extraction
    successful_details = sum(1 for detail in hotel_details if detail.get('extraction_success', False))
    details_success_rate = successful_details / details_total * 100 if details_total > 0 else 0
    
    validation_result = {
        'validation_date': datetime.now().isoformat(),
        'locations_expected': len(locations),
        'locations_actual': stats['total_locations'],
        'hotels_expected': expected_total,
        'hotels_actual': actual_total,
        'details_extracted': details_total,
        'coverage_percentage': coverage,
        'details_coverage_percentage': details_coverage,
        'details_success_rate': details_success_rate,
        'status': 'PASS' if coverage > 20 and details_success_rate > 80 else 'FAIL',
        'recommendations': []
    }
    
    if coverage < 50:
        validation_result['recommendations'].append('Consider improving extraction logic for better coverage')
    if stats['total_locations'] < len(locations):
        validation_result['recommendations'].append('Some locations were not processed successfully')
    if details_success_rate < 90:
        validation_result['recommendations'].append('Improve hotel details extraction logic - success rate too low')
    if details_coverage < 95:
        validation_result['recommendations'].append('Some hotels missing detailed information')
    
    # Save validation results
    validation_file = os.path.join(data_dir, "validation_results.json")
    with open(validation_file, 'w', encoding='utf-8') as f:
        json.dump(validation_result, f, ensure_ascii=False, indent=2)
    
    logging.info(f"Validation completed: {coverage:.1f}% hotels coverage, {details_success_rate:.1f}% details success rate")
    
    # Fail if coverage or success rate too low
    if coverage < 10:
        raise ValueError(f"Hotels coverage too low: {coverage:.1f}%. Please check extraction logic.")
    if details_success_rate < 70:
        raise ValueError(f"Details success rate too low: {details_success_rate:.1f}%. Please check details extraction logic.")
    
    return validation_result

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
    bash_command='mkdir -p /opt/airflow/data/raw/vietnambooking /opt/airflow/data/processed/vietnambooking',
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