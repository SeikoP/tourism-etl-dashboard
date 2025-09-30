#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import asyncio
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class Crawl4AIClient:
    """Client để tương tác với Crawl4AI service"""
    
    def __init__(self, base_url: str = "http://crawl4ai:11235"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def health_check(self) -> bool:
        """Kiểm tra Crawl4AI service có hoạt động không"""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Crawl4AI health check failed: {e}")
            return False
    
    def crawl_url(self, 
                  url: str, 
                  extraction_strategy: str = "NoExtractionStrategy",
                  chunking_strategy: str = "RegexChunking",
                  **kwargs) -> Dict:
        """
        Crawl một URL sử dụng Crawl4AI
        
        Args:
            url: URL cần crawl
            extraction_strategy: Chiến lược trích xuất
            chunking_strategy: Chiến lược phân đoạn
            **kwargs: Các tham số bổ sung
        """
        payload = {
            "urls": [url],
            "extraction_strategy": extraction_strategy,
            "chunking_strategy": chunking_strategy,
            **kwargs
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/crawl",
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Crawl4AI request failed for {url}: {e}")
            raise
    
    def crawl_multiple_urls(self, 
                           urls: List[str],
                           extraction_strategy: str = "NoExtractionStrategy",
                           **kwargs) -> List[Dict]:
        """Crawl nhiều URLs cùng lúc"""
        payload = {
            "urls": urls,
            "extraction_strategy": extraction_strategy,
            **kwargs
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/crawl_multiple",
                json=payload,
                timeout=300  # 5 minutes for batch
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Crawl4AI batch request failed: {e}")
            raise
    
    def extract_with_llm(self, 
                        url: str, 
                        prompt: str,
                        model: str = "gpt-4o-mini") -> Dict:
        """Sử dụng LLM để trích xuất dữ liệu có cấu trúc"""
        payload = {
            "urls": [url],
            "extraction_strategy": "LLMExtractionStrategy",
            "extraction_strategy_args": {
                "provider": "openai",
                "model": model,
                "prompt": prompt,
                "schema": {}
            }
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/crawl",
                json=payload,
                timeout=120
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Crawl4AI LLM extraction failed for {url}: {e}")
            raise


class VietnamBookingCrawl4AI:
    """Sử dụng Crawl4AI để crawl VietnamBooking.com"""
    
    def __init__(self):
        self.client = Crawl4AIClient()
    
    async def extract_hotels_with_crawl4ai(self, location_url: str) -> List[Dict]:
        """Trích xuất danh sách hotels sử dụng Crawl4AI"""
        
        # CSS selectors cho VietnamBooking.com
        extraction_prompt = """
        Extract hotel information from this VietnamBooking.com page.
        For each hotel, extract:
        - name: Hotel name
        - price: Price information
        - rating: Rating score
        - location: Location/address
        - amenities: List of amenities
        - image_url: Main image URL
        - booking_url: Link to hotel page
        
        Return as JSON array of hotel objects.
        """
        
        try:
            # Sử dụng CSS extraction strategy thay vì LLM để tiết kiệm cost
            result = self.client.crawl_url(
                url=location_url,
                extraction_strategy="CSSExtractionStrategy",
                extraction_strategy_args={
                    "schema": {
                        "name": "hotel_listings",
                        "baseSelector": ".hotel-item, .accommodation-item",
                        "fields": [
                            {
                                "name": "name",
                                "selector": ".hotel-name, h3, .title",
                                "type": "text"
                            },
                            {
                                "name": "price", 
                                "selector": ".price, .rate",
                                "type": "text"
                            },
                            {
                                "name": "rating",
                                "selector": ".rating, .score",
                                "type": "text"
                            },
                            {
                                "name": "location",
                                "selector": ".location, .address",
                                "type": "text"
                            },
                            {
                                "name": "booking_url",
                                "selector": "a",
                                "type": "attribute",
                                "attribute": "href"
                            }
                        ]
                    }
                },
                js_code=[
                    "window.scrollTo(0, document.body.scrollHeight);",  # Scroll để load lazy content
                    "await new Promise(resolve => setTimeout(resolve, 3000));"  # Wait for dynamic content
                ],
                wait_for_selector=".hotel-item, .accommodation-item",
                timeout=30
            )
            
            if result and "results" in result:
                extracted_data = result["results"][0].get("extracted_content", [])
                logger.info(f"Crawl4AI extracted {len(extracted_data)} hotels from {location_url}")
                return extracted_data
            else:
                logger.warning(f"No data extracted from {location_url}")
                return []
                
        except Exception as e:
            logger.error(f"Crawl4AI extraction failed for {location_url}: {e}")
            return []
    
    async def extract_hotel_details_with_crawl4ai(self, hotel_url: str) -> Dict:
        """Trích xuất chi tiết hotel sử dụng Crawl4AI"""
        
        try:
            result = self.client.crawl_url(
                url=hotel_url,
                extraction_strategy="CSSExtractionStrategy", 
                extraction_strategy_args={
                    "schema": {
                        "name": "hotel_details",
                        "baseSelector": "body",
                        "fields": [
                            {
                                "name": "description",
                                "selector": ".description, .hotel-desc",
                                "type": "text"
                            },
                            {
                                "name": "amenities",
                                "selector": ".amenities li, .facilities li",
                                "type": "list"
                            },
                            {
                                "name": "images",
                                "selector": ".gallery img, .photos img",
                                "type": "attribute",
                                "attribute": "src"
                            },
                            {
                                "name": "policies",
                                "selector": ".policies, .terms",
                                "type": "text"
                            }
                        ]
                    }
                },
                timeout=20
            )
            
            if result and "results" in result:
                return result["results"][0].get("extracted_content", {})
            else:
                return {}
                
        except Exception as e:
            logger.error(f"Crawl4AI hotel details extraction failed for {hotel_url}: {e}")
            return {}


# Utility functions để tích hợp với Airflow DAGs
def test_crawl4ai_connection():
    """Test function cho Airflow task"""
    client = Crawl4AIClient()
    if client.health_check():
        print("✅ Crawl4AI service is healthy and ready!")
        return True
    else:
        print("❌ Crawl4AI service is not available!")
        return False

def crawl4ai_extract_sample():
    """Sample extraction task for Airflow"""
    crawler = VietnamBookingCrawl4AI()
    sample_url = "https://vietnambooking.com/hotel/ho-chi-minh-city"
    
    # Run async function in sync context for Airflow
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        hotels = loop.run_until_complete(
            crawler.extract_hotels_with_crawl4ai(sample_url)
        )
        print(f"✅ Extracted {len(hotels)} hotels using Crawl4AI")
        return hotels
    finally:
        loop.close()

if __name__ == "__main__":
    # Test the integration
    test_crawl4ai_connection()
    crawl4ai_extract_sample()