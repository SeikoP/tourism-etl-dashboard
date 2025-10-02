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

        # Try to import AI-powered hotel details extractor
        try:
            from etl.extract.vietnambooking.ai_hotel_details_extractor import process_hotels_with_ai
            logging.info("Successfully imported AI-powered hotel details extractor")
        except ImportError as e:
            logging.error(f"Failed to import AI hotel details extractor: {e}")
            logging.error(f"Available modules in etl.extract.vietnambooking: {os.listdir(os.path.join(src_path, 'etl/extract/vietnambooking'))}")
            raise
        
        # Parameters for AI extraction
        hotels_file = "/opt/airflow/data/raw/vietnambooking/all_hotels_enhanced.json"
        output_dir = "/opt/airflow/data/raw/vietnambooking/details/"
        batch_size = 10  # Smaller batches for AI processing
        
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
                details = asyncio.run(process_hotels_with_ai(
                    hotels_file, output_dir, start_idx, batch_size
                ))
                if details:
                    total_details += len(details)
                    logging.info(f"AI details batch completed: {len(details)} hotels processed")
                else:
                    logging.warning(f"No AI details extracted from batch {start_idx}")
            except Exception as batch_error:
                logging.error(f"Error processing AI details batch {start_idx}: {batch_error}")
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
        
        # Find all AI-generated details batch files
        pattern = os.path.join(data_dir, "ai_hotel_details_batch_*.json")
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

def transform_data_task(**context):
    """Task 6: Transform and validate extracted data"""
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

        # Try to import DataTransformer
        try:
            from etl.tranform.data_transformer import DataTransformer
            logging.info("Successfully imported DataTransformer")
        except ImportError as e:
            logging.error(f"Failed to import DataTransformer: {e}")
            logging.error(f"Available modules in etl.tranform: {os.listdir(os.path.join(src_path, 'etl/tranform'))}")
            raise

        transformer = DataTransformer()

        # Transform hotels data
        hotels_input = "/opt/airflow/data/raw/vietnambooking/all_hotels_enhanced.json"
        hotels_output = "/opt/airflow/data/processed/vietnambooking/hotels_transformed.json"

        if os.path.exists(hotels_input):
            hotels_stats = transformer.transform_hotels_data(hotels_input, hotels_output)
            logging.info(f"Hotels transformation stats: {hotels_stats}")
        else:
            logging.warning(f"Hotels input file not found: {hotels_input}")

        # Transform hotel details data
        details_input_dir = "/opt/airflow/data/raw/vietnambooking/details/"
        details_output = "/opt/airflow/data/processed/vietnambooking/hotel_details_transformed.json"

        if os.path.exists(details_input_dir):
            details_stats = transformer.transform_hotel_details_data(details_input_dir, details_output)
            logging.info(f"Hotel details transformation stats: {details_stats}")
        else:
            logging.warning(f"Hotel details input directory not found: {details_input_dir}")

        return {"hotels_stats": hotels_stats, "details_stats": details_stats}

    except Exception as e:
        logging.error(f"Error in transform_data_task: {e}")
        logging.error(f"Traceback: {traceback.format_exc()}")
        raise

def load_to_database_task(**context):
    """Task 7: Load transformed data into database"""
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

        # Try to import DataLoader
        try:
            from etl.load.data_loader import DataLoader
            logging.info("Successfully imported DataLoader")
        except ImportError as e:
            logging.error(f"Failed to import DataLoader: {e}")
            logging.error(f"Available modules in etl.load: {os.listdir(os.path.join(src_path, 'etl/load'))}")
            raise

        # Initialize data loader
        loader = DataLoader()

        # Create tables if they don't exist
        loader.create_tables()

        # Load locations
        locations_file = "/opt/airflow/data/raw/vietnambooking/locations.json"
        if os.path.exists(locations_file):
            locations_stats = loader.load_locations(locations_file)
            logging.info(f"Locations loading stats: {locations_stats}")
        else:
            logging.warning(f"Locations file not found: {locations_file}")
            locations_stats = {"error": "file not found"}

        # Load transformed hotels
        hotels_file = "/opt/airflow/data/processed/vietnambooking/hotels_transformed.json"
        if os.path.exists(hotels_file):
            hotels_stats = loader.load_hotels(hotels_file)
            logging.info(f"Hotels loading stats: {hotels_stats}")
        else:
            logging.warning(f"Transformed hotels file not found: {hotels_file}")
            hotels_stats = {"error": "file not found"}

        # Load transformed hotel details
        details_file = "/opt/airflow/data/processed/vietnambooking/hotel_details_transformed.json"
        if os.path.exists(details_file):
            details_stats = loader.load_hotel_details(details_file)
            logging.info(f"Hotel details loading stats: {details_stats}")
        else:
            logging.warning(f"Transformed hotel details file not found: {details_file}")
            details_stats = {"error": "file not found"}

        # Get final database stats
        db_stats = loader.get_database_stats()
        logging.info(f"Final database stats: {db_stats}")

        loader.close()

        return {
            "locations_stats": locations_stats,
            "hotels_stats": hotels_stats,
            "details_stats": details_stats,
            "database_stats": db_stats
        }

    except Exception as e:
        logging.error(f"Error in load_to_database_task: {e}")
        logging.error(f"Traceback: {traceback.format_exc()}")
        raise

def validate_results(**context):
    """Task 8: Validate extraction, transformation, and loading results"""
    import os

    try:
        # Try to import DataLoader for database validation
        try:
            from etl.load.data_loader import DataLoader
            db_available = True
        except ImportError:
            db_available = False
            logging.warning("DataLoader not available for database validation")

        data_dir = "/opt/airflow/data/raw/vietnambooking/"
        processed_dir = "/opt/airflow/data/processed/vietnambooking/"

        # Verify directories exist
        for dir_path in [data_dir, processed_dir]:
            if not os.path.exists(dir_path):
                logging.warning(f"Directory not found: {dir_path}")

        # Load results with error handling
        locations_file = os.path.join(data_dir, "locations.json")
        hotels_file = os.path.join(data_dir, "all_hotels_enhanced.json")
        transformed_hotels_file = os.path.join(processed_dir, "hotels_transformed.json")
        transformed_details_file = os.path.join(processed_dir, "hotel_details_transformed.json")

        # Check database stats if available
        db_stats = {}
        if db_available:
            try:
                loader = DataLoader()
                db_stats = loader.get_database_stats()
                loader.close()
                logging.info(f"Database stats: {db_stats}")
            except Exception as e:
                logging.warning(f"Could not get database stats: {e}")

        # Check if required files exist
        files_status = {
            'locations': os.path.exists(locations_file),
            'hotels': os.path.exists(hotels_file),
            'transformed_hotels': os.path.exists(transformed_hotels_file),
            'transformed_details': os.path.exists(transformed_details_file)
        }

        # Load data where available
        locations = []
        hotels = []
        transformed_hotels = []
        transformed_details = []

        if files_status['locations']:
            with open(locations_file, 'r', encoding='utf-8') as f:
                locations = json.load(f)

        if files_status['hotels']:
            with open(hotels_file, 'r', encoding='utf-8') as f:
                hotels = json.load(f)

        if files_status['transformed_hotels']:
            with open(transformed_hotels_file, 'r', encoding='utf-8') as f:
                transformed_hotels = json.load(f)

        if files_status['transformed_details']:
            with open(transformed_details_file, 'r', encoding='utf-8') as f:
                transformed_details = json.load(f)

        # Calculate metrics
        expected_hotels = sum(loc.get('hotel_count', 0) for loc in locations)
        raw_hotels_count = len(hotels)
        transformed_hotels_count = len(transformed_hotels)
        transformed_details_count = len(transformed_details)

        coverage = (raw_hotels_count / expected_hotels * 100) if expected_hotels > 0 else 0
        transform_success_rate = (transformed_hotels_count / raw_hotels_count * 100) if raw_hotels_count > 0 else 0
        details_coverage = (transformed_details_count / transformed_hotels_count * 100) if transformed_hotels_count > 0 else 0

        # Database validation
        db_hotels_count = db_stats.get('hotels_count', 0)
        db_details_count = db_stats.get('details_count', 0)
        db_load_success = (db_hotels_count / transformed_hotels_count * 100) if transformed_hotels_count > 0 else 0

        validation_result = {
            'validation_date': datetime.now().isoformat(),
            'files_status': files_status,
            'locations_count': len(locations),
            'expected_hotels': expected_hotels,
            'raw_hotels_count': raw_hotels_count,
            'transformed_hotels_count': transformed_hotels_count,
            'transformed_details_count': transformed_details_count,
            'database_hotels_count': db_hotels_count,
            'database_details_count': db_details_count,
            'coverage_percentage': coverage,
            'transform_success_rate': transform_success_rate,
            'details_coverage_percentage': details_coverage,
            'database_load_success_rate': db_load_success,
            'database_available': db_available,
            'status': 'PASS',
            'recommendations': []
        }

        # Determine overall status
        if coverage < 5:
            validation_result['status'] = 'FAIL'
            validation_result['recommendations'].append('Hotel extraction coverage too low')
        if transform_success_rate < 80:
            validation_result['status'] = 'WARN'
            validation_result['recommendations'].append('Data transformation success rate could be improved')
        if db_available and db_load_success < 80:
            validation_result['status'] = 'WARN'
            validation_result['recommendations'].append('Database loading success rate could be improved')

        # Generate recommendations
        if not files_status['transformed_hotels']:
            validation_result['recommendations'].append('Transform step did not produce expected output')
        if not files_status['transformed_details']:
            validation_result['recommendations'].append('Details transformation did not produce expected output')
        if db_available and db_hotels_count == 0:
            validation_result['recommendations'].append('No hotels loaded to database')

        # Save validation results
        validation_file = os.path.join(data_dir, "validation_results.json")
        with open(validation_file, 'w', encoding='utf-8') as f:
            json.dump(validation_result, f, ensure_ascii=False, indent=2)

        logging.info(f"Validation completed: {validation_result['status']}")
        logging.info(f"Coverage: {coverage:.1f}%, Transform: {transform_success_rate:.1f}%, DB Load: {db_load_success:.1f}%")

        return validation_result

    except Exception as e:
        logging.error(f"Error in validate_results: {e}")
        raise

# Define tasks
extract_locations = PythonOperator(
    task_id='extract_locations',
    python_callable=extract_locations_task,
    execution_timeout=timedelta(minutes=10),
    dag=dag,
)

extract_hotels = PythonOperator(
    task_id='extract_hotels',
    python_callable=extract_hotels_batch,
    execution_timeout=timedelta(minutes=30),
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
    execution_timeout=timedelta(minutes=60),  # Increased for AI processing
    dag=dag,
)

merge_details = PythonOperator(
    task_id='merge_hotel_details',
    python_callable=merge_hotel_details,
    dag=dag,
)

transform_data = PythonOperator(
    task_id='transform_data',
    python_callable=transform_data_task,
    dag=dag,
)

load_to_database = PythonOperator(
    task_id='load_to_database',
    python_callable=load_to_database_task,
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
create_dirs >> extract_locations >> extract_hotels >> merge_hotels >> extract_details >> merge_details >> transform_data >> load_to_database >> validate_pipeline >> cleanup