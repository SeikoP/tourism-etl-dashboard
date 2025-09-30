#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from airflow import DAG  # type: ignore
from airflow.operators.python import PythonOperator  # type: ignore
from airflow.operators.bash import BashOperator  # type: ignore
import sys
import os

# Add src to path
sys.path.append('/opt/airflow/src')

from services.crawl4ai_integration import (
    test_crawl4ai_connection,
    crawl4ai_extract_sample,
    VietnamBookingCrawl4AI
)

default_args = {
    'owner': 'tourism-team',
    'depends_on_past': False,
    'start_date': datetime(2025, 10, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'crawl4ai_integration_test',
    default_args=default_args,
    description='Test Crawl4AI integration with Airflow',
    schedule_interval=None,  # Manual trigger only
    catchup=False,
    tags=['crawl4ai', 'test', 'integration'],
)

def check_crawl4ai_health():
    """Check if Crawl4AI service is running"""
    return test_crawl4ai_connection()

def run_crawl4ai_sample():
    """Run sample extraction with Crawl4AI"""
    return crawl4ai_extract_sample()

def compare_extraction_methods():
    """Compare traditional scraping vs Crawl4AI"""
    import json
    import asyncio
    from etl.extract.vietnambooking.enhanced_hotel_extractor import EnhancedHotelExtractor
    
    # Test URL
    test_url = "https://vietnambooking.com/hotel/ho-chi-minh-city"
    
    # Traditional method
    traditional_extractor = EnhancedHotelExtractor()
    
    # Crawl4AI method  
    crawl4ai_extractor = VietnamBookingCrawl4AI()
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        print("🔍 Running extraction comparison...")
        
        # Traditional extraction
        print("⚙️ Traditional extraction...")
        traditional_results = loop.run_until_complete(
            traditional_extractor.extract_hotels_from_location(test_url, max_pages=1)
        )
        
        # Crawl4AI extraction
        print("🤖 Crawl4AI extraction...")
        crawl4ai_results = loop.run_until_complete(
            crawl4ai_extractor.extract_hotels_with_crawl4ai(test_url)
        )
        
        # Compare results
        comparison = {
            "traditional": {
                "count": len(traditional_results),
                "sample": traditional_results[:2] if traditional_results else []
            },
            "crawl4ai": {
                "count": len(crawl4ai_results),
                "sample": crawl4ai_results[:2] if crawl4ai_results else []
            },
            "comparison": {
                "traditional_better": len(traditional_results) > len(crawl4ai_results),
                "difference": len(traditional_results) - len(crawl4ai_results)
            }
        }
        
        print(f"📊 Comparison Results:")
        print(f"   Traditional: {comparison['traditional']['count']} hotels")
        print(f"   Crawl4AI: {comparison['crawl4ai']['count']} hotels")
        print(f"   Difference: {comparison['comparison']['difference']}")
        
        return comparison
        
    finally:
        loop.close()

# Task 1: Health check
health_check_task = PythonOperator(
    task_id='check_crawl4ai_health',
    python_callable=check_crawl4ai_health,
    dag=dag,
)

# Task 2: Sample extraction
sample_extraction_task = PythonOperator(
    task_id='run_crawl4ai_sample',
    python_callable=run_crawl4ai_sample,
    dag=dag,
)

# Task 3: Method comparison
comparison_task = PythonOperator(
    task_id='compare_extraction_methods',
    python_callable=compare_extraction_methods,
    dag=dag,
)

# Task dependencies
health_check_task >> sample_extraction_task >> comparison_task