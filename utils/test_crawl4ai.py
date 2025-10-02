#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import httpx
import json
import logging
import os
from typing import Dict, Any

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_crawl4ai_connection():
    """Test Crawl4AI service connectivity"""

    crawl4ai_url = "http://localhost:11235"

    print("🔍 Testing Crawl4AI Service Connection...")
    print(f"URL: {crawl4ai_url}")

    try:
        # Test health endpoint
        print("\n1. Testing health endpoint...")
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"{crawl4ai_url}/health")
            print(f"Health check: {response.status_code}")
            if response.status_code == 200:
                print("✅ Crawl4AI service is healthy!")
            else:
                print(f"❌ Health check failed: {response.status_code}")

        # Test crawl endpoint with a simple URL
        print("\n2. Testing crawl endpoint...")
        test_payload = {
            "urls": ["https://httpbin.org/html"],
            "extraction_prompt": "Extract the main heading from this page.",
            "extraction_schema": {
                "type": "object",
                "properties": {
                    "heading": {"type": "string"}
                }
            }
        }

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{crawl4ai_url}/crawl",
                json=test_payload,
                headers={"Content-Type": "application/json"}
            )
            print(f"Crawl test: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print("✅ Crawl4AI AI extraction working!")
                print(f"Response: {json.dumps(result, indent=2)[:500]}...")
            else:
                print(f"❌ Crawl test failed: {response.status_code}")
                print(f"Response: {response.text[:500]}")

    except httpx.ConnectError:
        print("❌ Cannot connect to Crawl4AI service")
        print("💡 Make sure Crawl4AI container is running:")
        print("   docker-compose up crawl4ai -d")
        print("   OR")
        print("   docker-compose up -d  # if it's included in default services")

    except Exception as e:
        print(f"❌ Error testing Crawl4AI: {e}")

    print("\n🔧 Troubleshooting:")
    print("1. Check if container is running: docker-compose ps")
    print("2. Check container logs: docker-compose logs crawl4ai")
    print("3. Start Crawl4AI: docker-compose up crawl4ai -d")
    print("4. Check .env file has valid GEMINI_API_KEY")

if __name__ == "__main__":
    asyncio.run(test_crawl4ai_connection())