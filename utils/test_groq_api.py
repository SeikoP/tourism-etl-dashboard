#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test script để kiểm tra Groq API trực tiếp
"""

import os
from groq import Groq

def test_groq_api():
    """Test Groq API với một prompt đơn giản"""

    # Lấy API key từ environment variable
    api_key = os.getenv('GROQ_API_KEY')
    if not api_key:
        print("❌ GROQ_API_KEY not found in environment variables")
        print("   Please set GROQ_API_KEY in your .env file or environment")
        return

    print("🔍 Testing Groq API...")
    print(f"   API Key: {api_key[:10]}...{api_key[-4:] if len(api_key) > 14 else api_key}")
    print()

    try:
        # Khởi tạo Groq client
        client = Groq(api_key=api_key)

        # Test với một prompt đơn giản
        print("📤 Sending test request...")
        completion = client.chat.completions.create(
            model="gemma2-9b-it",
            messages=[
                {
                    "role": "user",
                    "content": "Xin chào! Hãy giới thiệu về bạn bằng tiếng Việt."
                }
            ],
            temperature=1,
            max_completion_tokens=1024,
            top_p=1,
            stream=True,
            stop=None
        )

        print("📥 Response:")
        print("-" * 40)

        # Stream response
        full_response = ""
        for chunk in completion:
            content = chunk.choices[0].delta.content or ""
            print(content, end="", flush=True)
            full_response += content

        print("\n" + "=" * 40)
        print("✅ Groq API test successful!")
        print(f"   Response length: {len(full_response)} characters")

    except Exception as e:
        print(f"❌ Groq API test failed: {str(e)}")
        print("   Possible issues:")
        print("   - Invalid API key")
        print("   - Network connectivity")
        print("   - Model not available")
        print("   - Rate limiting")

def test_hotel_extraction_prompt():
    """Test với prompt extraction hotel"""

    api_key = os.getenv('GROQ_API_KEY')
    if not api_key:
        print("❌ GROQ_API_KEY not found")
        return

    print("\n🏨 Testing Hotel Extraction Prompt...")
    print("=" * 50)

    try:
        client = Groq(api_key=api_key)

        hotel_prompt = """
        Trích xuất thông tin từ trang web khách sạn Việt Nam này:

        **Khách sạn Sài Gòn Hà Nội – Trương Định**

        Địa chỉ: 19 Trương Định, Bến Thành, Quận 1, Hồ Chí Minh

        Giá: 880,000 - 1,466,666 VND

        Tiện ích:
        - WiFi
        - Hồ bơi
        - Nhà hàng
        - Điều hòa
        - Lễ tân 24h
        - Đưa đón sân bay

        Hãy trích xuất thành JSON với format:
        {
            "hotel_name": "tên khách sạn",
            "address": "địa chỉ",
            "price_range": "khoảng giá",
            "amenities": ["tiện ích 1", "tiện ích 2", ...]
        }
        """

        completion = client.chat.completions.create(
            model="gemma2-9b-it",
            messages=[
                {
                    "role": "user",
                    "content": hotel_prompt
                }
            ],
            temperature=0.1,
            max_completion_tokens=1024,
            top_p=1,
            stream=False
        )

        response = completion.choices[0].message.content
        print("📥 AI Response:")
        print(response)

        # Try to parse JSON
        try:
            import json
            parsed = json.loads(response)
            print("\n✅ JSON parsing successful!")
            print(f"   Hotel: {parsed.get('hotel_name', 'N/A')}")
            print(f"   Amenities: {len(parsed.get('amenities', []))} items")
        except json.JSONDecodeError:
            print("\n⚠️  Response is not valid JSON")

    except Exception as e:
        print(f"❌ Hotel extraction test failed: {str(e)}")

if __name__ == "__main__":
    # Load environment variables from .env file
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("📄 Loaded environment from .env file")
    except ImportError:
        print("⚠️  python-dotenv not installed, using system environment")

    test_groq_api()
    test_hotel_extraction_prompt()