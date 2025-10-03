#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Incremental ETL Pipeline cho VietnamBooking với Rate Limiting
Chạy hàng ngày để tránh quota limits của AI API
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from airflow.providers.standard.operators.bash import BashOperator
import os
import sys
import json
import logging

# Add src to path for imports
sys.path.append('/opt/airflow/src')

default_args = {
    'owner': 'tourism-team',
    'depends_on_past': False,
    'start_date': datetime(2025, 10, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=30),
    'max_active_runs': 1,
}

# DAG chạy hàng ngày với rate limiting
dag = DAG(
    'vietnambooking_incremental_pipeline',
    default_args=default_args,
    description='Incremental VietnamBooking pipeline with AI rate limiting',
    schedule='0 2 * * *',  # Chạy lúc 2:00 AM hàng ngày
    catchup=False,
    tags=['crawling', 'vietnambooking', 'incremental', 'rate-limited'],
)

def check_quota_and_proceed(**context):
    """Task 1: Check quota và quyết định có tiếp tục không"""
    from utils.ai_rate_limiter import ai_rate_limiter

    status = ai_rate_limiter.get_status()

    logging.info("=== AI API Quota Status ===")
    logging.info(f"Requests today: {status['quota']['requests_today']}/{status['quota']['daily_limit']}")
    logging.info(f"Remaining today: {status['quota']['remaining_today']}")
    logging.info(f"Minute remaining: {status['rate_limiting']['minute_remaining']}")
    logging.info(f"Hour remaining: {status['rate_limiting']['hour_remaining']}")

    if not status['can_proceed']:
        logging.warning("Daily quota exceeded, skipping today's run")
        return False

    if status['quota']['remaining_today'] < 50:  # Dưới 50 requests thì skip
        logging.warning("Low quota remaining, skipping today's run")
        return False

    logging.info("Quota OK, proceeding with incremental processing")
    return True

def incremental_extract_hotels(**context):
    """Task 2: Extract hotels incremental (chỉ hotels mới/chưa process)"""
    import sys
    import os
    import traceback
    import asyncio
    from datetime import datetime

    try:
        project_root = '/opt/airflow'
        src_path = os.path.join(project_root, 'src')
        sys.path.insert(0, src_path)

        # Import extractors
        from etl.extract.vietnambooking.extract_locations import extract_all_locations
        from etl.extract.vietnambooking.enhanced_hotel_extractor import EnhancedHotelExtractor

        # Check if we need to extract locations
        locations_file = "/opt/airflow/data/raw/vietnambooking/locations.json"
        if not os.path.exists(locations_file) or os.path.getsize(locations_file) == 0:
            logging.info("Extracting locations...")
            locations = asyncio.run(extract_all_locations())
            os.makedirs(os.path.dirname(locations_file), exist_ok=True)
            with open(locations_file, 'w', encoding='utf-8') as f:
                json.dump(locations, f, ensure_ascii=False, indent=2)
            logging.info(f"Extracted {len(locations)} locations")
        else:
            logging.info("Locations already exist, skipping extraction")

        # Extract hotels incremental
        extractor = EnhancedHotelExtractor()
        hotels_file = "/opt/airflow/data/raw/vietnambooking/all_hotels_enhanced.json"

        # Load existing hotels để check duplicates
        existing_hotels = []
        if os.path.exists(hotels_file):
            with open(hotels_file, 'r', encoding='utf-8') as f:
                existing_hotels = json.load(f)
            logging.info(f"Found {len(existing_hotels)} existing hotels")

        # Extract new hotels
        new_hotels = []
        locations = json.load(open(locations_file, 'r', encoding='utf-8'))

        for location in locations[:5]:  # Process 5 locations per day để tránh quota
            logging.info(f"Processing location: {location['location_name']}")
            try:
                # Use asyncio to run the async method
                hotels = asyncio.run(extractor.process_location(location))
                if hotels:
                    # Filter out existing hotels
                    existing_urls = {h['url'] for h in existing_hotels}
                    new_hotel_list = [h for h in hotels if h['url'] not in existing_urls]

                    if new_hotel_list:
                        new_hotels.extend(new_hotel_list)
                        logging.info(f"Found {len(new_hotel_list)} new hotels in {location['location_name']}")
                    else:
                        logging.info(f"No new hotels in {location['location_name']}")
                else:
                    logging.warning(f"No hotels found in {location['location_name']}")
            except Exception as e:
                logging.error(f"Error extracting hotels from {location['location_name']}: {e}")
                continue

        # Save new hotels
        if new_hotels:
            all_hotels = existing_hotels + new_hotels
            with open(hotels_file, 'w', encoding='utf-8') as f:
                json.dump(all_hotels, f, ensure_ascii=False, indent=2)
            logging.info(f"Added {len(new_hotels)} new hotels, total: {len(all_hotels)}")
            return len(new_hotels)
        else:
            logging.info("No new hotels found today")
            return 0

    except Exception as e:
        logging.error(f"Error in incremental_extract_hotels: {e}")
        raise

def incremental_extract_details(**context):
    """Task 3: Extract details với rate limiting (chỉ 50 hotels/ngày)"""
    import sys
    import os
    import traceback
    import asyncio
    from datetime import datetime

    try:
        project_root = '/opt/airflow'
        src_path = os.path.join(project_root, 'src')
        sys.path.insert(0, src_path)

        from etl.extract.vietnambooking.ai_hotel_details_extractor import process_hotels_with_ai
        from utils.ai_rate_limiter import ai_rate_limiter

        # Check quota trước khi bắt đầu
        status = ai_rate_limiter.get_status()
        if not status['can_proceed'] or status['quota']['remaining_today'] < 10:
            logging.warning("Insufficient quota for details extraction")
            return 0

        hotels_file = "/opt/airflow/data/raw/vietnambooking/all_hotels_enhanced.json"
        output_dir = "/opt/airflow/data/raw/vietnambooking/details/"

        if not os.path.exists(hotels_file):
            logging.warning("Hotels file not found")
            return 0

        # Load hotels
        with open(hotels_file, 'r', encoding='utf-8') as f:
            hotels = json.load(f)

        # Find hotels chưa có details
        processed_files = os.listdir(output_dir) if os.path.exists(output_dir) else []
        processed_urls = set()

        for filename in processed_files:
            if filename.startswith('hotel_details_batch_') and filename.endswith('.json'):
                try:
                    batch_file = os.path.join(output_dir, filename)
                    with open(batch_file, 'r', encoding='utf-8') as f:
                        batch_data = json.load(f)
                        for hotel_data in batch_data:
                            if 'url' in hotel_data:
                                processed_urls.add(hotel_data['url'])
                except Exception as e:
                    logging.warning(f"Error reading batch file {filename}: {e}")

        # Filter hotels chưa process
        unprocessed_hotels = [h for h in hotels if h['url'] not in processed_urls]

        if not unprocessed_hotels:
            logging.info("All hotels have been processed")
            return 0

        # Process maximum 50 hotels per day
        batch_size = 10
        max_hotels_per_day = 50
        hotels_to_process = unprocessed_hotels[:max_hotels_per_day]

        logging.info(f"Processing {len(hotels_to_process)} hotels today (max {max_hotels_per_day})")

        total_processed = 0

        # Process in small batches
        for start_idx in range(0, len(hotels_to_process), batch_size):
            batch_hotels = hotels_to_process[start_idx:start_idx + batch_size]

            # Check quota trước mỗi batch
            status = ai_rate_limiter.get_status()
            if not status['can_proceed'] or status['rate_limiting']['minute_remaining'] < 2:
                logging.warning("Quota/rate limit reached, stopping for today")
                break

            logging.info(f"Processing details batch {start_idx}-{start_idx + len(batch_hotels)}")

            try:
                # Create temporary file cho batch này
                batch_data = [{'url': h['url'], 'name': h['name'], 'location_name': h.get('location_name', ''), 'location_code': h.get('location_code', '')} for h in batch_hotels]
                temp_file = f"/tmp/batch_{start_idx}.json"
                with open(temp_file, 'w', encoding='utf-8') as f:
                    json.dump(batch_data, f, ensure_ascii=False, indent=2)

                details = asyncio.run(process_hotels_with_ai(
                    temp_file, output_dir, 0, len(batch_hotels)
                ))

                if details:
                    total_processed += len(details)
                    logging.info(f"Batch completed: {len(details)} hotels processed")

                # Clean up temp file
                os.remove(temp_file)

            except Exception as batch_error:
                logging.error(f"Error processing batch {start_idx}: {batch_error}")
                continue

        logging.info(f"Total hotels processed today: {total_processed}")
        return total_processed

    except Exception as e:
        logging.error(f"Error in incremental_extract_details: {e}")
        raise

def transform_and_load_incremental(**context):
    """Task 4: Transform và Load data đã extract"""
    import sys
    import os
    import traceback

    try:
        project_root = '/opt/airflow'
        src_path = os.path.join(project_root, 'src')
        sys.path.insert(0, src_path)

        from etl.tranform.data_transformer import DataTransformer
        from etl.load.data_loader import DataLoader

        # Transform new data
        transformer = DataTransformer()
        hotels_file = "/opt/airflow/data/raw/vietnambooking/all_hotels_enhanced.json"
        details_dir = "/opt/airflow/data/raw/vietnambooking/details/"

        if not os.path.exists(hotels_file):
            logging.warning("Hotels file not found for transformation")
            return 0

        # Load và transform hotels
        with open(hotels_file, 'r', encoding='utf-8') as f:
            hotels = json.load(f)

        transformed_hotels = []
        for hotel in hotels[-100:]:  # Chỉ process 100 hotels gần nhất
            try:
                transformed = transformer._validate_and_clean_hotel(hotel)
                if transformed:
                    transformed_hotels.append(transformed)
            except Exception as e:
                logging.warning(f"Error transforming hotel {hotel.get('name', 'unknown')}: {e}")
                continue

        if not transformed_hotels:
            logging.info("No hotels to transform")
            return 0

        # Load to database
        loader = DataLoader()
        hotels_loaded = loader.load_hotels_batch(transformed_hotels)

        # Transform và load details nếu có
        details_loaded = 0
        if os.path.exists(details_dir):
            details_files = [f for f in os.listdir(details_dir) if f.startswith('hotel_details_batch_')]
            if details_files:
                # Process latest details file
                latest_file = max(details_files, key=lambda x: os.path.getctime(os.path.join(details_dir, x)))
                details_file = os.path.join(details_dir, latest_file)

                with open(details_file, 'r', encoding='utf-8') as f:
                    details = json.load(f)

                transformed_details = []
                for detail in details:
                    try:
                        transformed = transformer._validate_and_clean_hotel_detail(detail)
                        if transformed:
                            transformed_details.append(transformed)
                    except Exception as e:
                        logging.warning(f"Error transforming detail: {e}")
                        continue

                if transformed_details:
                    details_loaded = loader.load_hotel_details_batch(transformed_details)

        logging.info(f"Transformed and loaded: {hotels_loaded} hotels, {details_loaded} details")
        return hotels_loaded + details_loaded

    except Exception as e:
        logging.error(f"Error in transform_and_load_incremental: {e}")
        raise

def generate_quota_report(**context):
    """Task 5: Generate quota usage report"""
    from utils.ai_rate_limiter import ai_rate_limiter

    status = ai_rate_limiter.get_status()

    report = f"""
=== AI API Quota Report - {datetime.now().strftime('%Y-%m-%d')} ===

DAILY USAGE:
- Requests Today: {status['quota']['requests_today']}/{status['quota']['daily_limit']}
- Remaining Today: {status['quota']['remaining_today']}
- Errors Today: {status['quota']['errors_today']}

RATE LIMITING:
- Minute Remaining: {status['rate_limiting']['minute_remaining']}/30
- Hour Remaining: {status['rate_limiting']['hour_remaining']}/500

STATUS: {'✅ OK' if status['can_proceed'] else '❌ QUOTA EXCEEDED'}
"""

    logging.info(report)

    # Save report to file
    report_file = f"/opt/airflow/logs/quota_report_{datetime.now().strftime('%Y%m%d')}.txt"
    os.makedirs(os.path.dirname(report_file), exist_ok=True)
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)

    return report

# Define tasks
check_quota_task = PythonOperator(
    task_id='check_quota',
    python_callable=check_quota_and_proceed,
    dag=dag,
)

extract_hotels_task = PythonOperator(
    task_id='incremental_extract_hotels',
    python_callable=incremental_extract_hotels,
    dag=dag,
)

extract_details_task = PythonOperator(
    task_id='incremental_extract_details',
    python_callable=incremental_extract_details,
    dag=dag,
)

transform_load_task = PythonOperator(
    task_id='transform_and_load',
    python_callable=transform_and_load_incremental,
    dag=dag,
)

report_task = PythonOperator(
    task_id='generate_quota_report',
    python_callable=generate_quota_report,
    dag=dag,
)

# Set dependencies
check_quota_task >> extract_hotels_task >> extract_details_task >> transform_load_task >> report_task