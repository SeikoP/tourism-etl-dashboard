from airflow import DAG # type: ignore
from airflow.operators.python_operator import PythonOperator # type: ignore
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add src directory to Python path
src_dir = Path(__file__).parents[2] / 'src'
sys.path.append(str(src_dir))

from etl.extract.vietnambooking.extract_locations import LocationExtractor
from etl.extract.vietnambooking.optimized_hotel_extractor import process_locations_batch
from etl.extract.vietnambooking.hotel_detail_extractor import process_hotel_details_batch
from etl.extract.vietnambooking.merge_results import merge_hotel_batches, merge_detail_batches, generate_summary_report
import asyncio
import json

# Default arguments for DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5)
}

# Create DAG
dag = DAG(
    'vietnambooking_hotels_crawler',
    default_args=default_args,
    description='Crawl hotel data from VietnamBooking.com',
    schedule_interval=timedelta(days=1),
    start_date=datetime(2025, 9, 30),
    catchup=False,
    tags=['crawler', 'hotels', 'vietnambooking'],
)

def extract_locations():
    """Extract danh sách địa điểm từ trang chủ"""
    async def run():
        extractor = LocationExtractor()
        locations = await extractor.extract_locations()
        if locations:
            output_dir = "data/raw/vietnambooking"
            extractor.save_locations(locations, output_dir)
    
    asyncio.run(run())

def extract_hotel_list():
    """Extract danh sách khách sạn từ mỗi địa điểm - batch processing"""
    async def run():
        locations_file = "data/raw/vietnambooking/locations.json"
        output_dir = "data/raw/vietnambooking"
        
        # Đọc tổng số locations
        with open(locations_file, 'r', encoding='utf-8') as f:
            locations = json.load(f)
        
        # Xử lý tất cả locations với batch processing
        batch_size = 10
        total_locations = len(locations)
        
        for start_idx in range(0, total_locations, batch_size):
            await process_locations_batch(locations_file, output_dir, start_idx, batch_size)
    
    asyncio.run(run())

def extract_hotel_details():
    """Extract chi tiết khách sạn - batch processing"""
    async def run():
        hotels_file = "data/raw/vietnambooking/hotels.json"
        output_dir = "data/raw/vietnambooking"
        
        # Đọc tổng số hotels
        with open(hotels_file, 'r', encoding='utf-8') as f:
            hotels = json.load(f)
        
        # Xử lý tất cả hotels với batch processing
        batch_size = 20
        total_hotels = len(hotels)
        
        for start_idx in range(0, total_hotels, batch_size):
            await process_hotel_details_batch(hotels_file, output_dir, start_idx, batch_size)
    
    asyncio.run(run())

def merge_and_report():
    """Merge các batch files và tạo báo cáo tổng hợp"""
    data_dir = "data/raw/vietnambooking"
    
    # Merge hotel batches
    merge_hotel_batches(data_dir)
    
    # Merge detail batches
    merge_detail_batches(data_dir)
    
    # Generate summary report
    generate_summary_report(data_dir)

# Task 1: Extract locations
extract_locations_task = PythonOperator(
    task_id='extract_locations',
    python_callable=extract_locations,
    dag=dag,
)

# Task 2: Extract hotel list
extract_hotels_task = PythonOperator(
    task_id='extract_hotels',
    python_callable=extract_hotel_list,
    dag=dag,
)

# Task 3: Extract hotel details
extract_details_task = PythonOperator(
    task_id='extract_details',
    python_callable=extract_hotel_details,
    dag=dag,
)

# Task 4: Merge results and generate report
merge_and_report_task = PythonOperator(
    task_id='merge_and_report',
    python_callable=merge_and_report,
    dag=dag,
)

# Set task dependencies
extract_locations_task >> extract_hotels_task >> extract_details_task >> merge_and_report_task