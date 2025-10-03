#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Rate Limiter và Quota Manager cho AI API calls
"""

import asyncio
import time
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import json
import os

logger = logging.getLogger(__name__)

class RateLimiter:
    """Rate limiter cho AI API calls"""

    def __init__(self, requests_per_minute: int = 30, requests_per_hour: int = 500):
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour

        # Tracking requests
        self.minute_requests = []
        self.hour_requests = []

        # Semaphore để limit concurrent requests
        self.semaphore = asyncio.Semaphore(3)

    async def acquire(self) -> bool:
        """Acquire permission to make a request"""
        async with self.semaphore:
            now = time.time()

            # Clean old requests
            self.minute_requests = [t for t in self.minute_requests if now - t < 60]
            self.hour_requests = [t for t in self.hour_requests if now - t < 3600]

            # Check limits
            if len(self.minute_requests) >= self.requests_per_minute:
                return False
            if len(self.hour_requests) >= self.requests_per_hour:
                return False

            # Record request
            self.minute_requests.append(now)
            self.hour_requests.append(now)

            return True

    def get_remaining_quota(self) -> Dict[str, int]:
        """Get remaining quota"""
        now = time.time()
        minute_remaining = self.requests_per_minute - len([t for t in self.minute_requests if now - t < 60])
        hour_remaining = self.requests_per_hour - len([t for t in self.hour_requests if now - t < 3600])

        return {
            'minute_remaining': max(0, minute_remaining),
            'hour_remaining': max(0, hour_remaining)
        }

class QuotaManager:
    """Quản lý quota usage và persistence"""

    def __init__(self, quota_file: str = "/opt/airflow/logs/quota_usage.json"):
        self.quota_file = quota_file
        self.daily_limit = 1000  # Max requests per day
        self.usage_data = self._load_usage()

    def _load_usage(self) -> Dict[str, Any]:
        """Load usage data from file"""
        try:
            if os.path.exists(self.quota_file):
                with open(self.quota_file, 'r') as f:
                    data = json.load(f)
                    # Reset if it's a new day
                    today = datetime.now().strftime('%Y-%m-%d')
                    if data.get('date') != today:
                        data = {'date': today, 'requests': 0, 'errors': 0}
                    return data
        except Exception as e:
            logger.warning(f"Could not load quota data: {e}")

        # Default data
        return {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'requests': 0,
            'errors': 0
        }

    def _save_usage(self):
        """Save usage data to file"""
        try:
            os.makedirs(os.path.dirname(self.quota_file), exist_ok=True)
            with open(self.quota_file, 'w') as f:
                json.dump(self.usage_data, f, indent=2)
        except Exception as e:
            logger.error(f"Could not save quota data: {e}")

    def record_request(self, success: bool = True):
        """Record a request"""
        self.usage_data['requests'] += 1
        if not success:
            self.usage_data['errors'] += 1
        self._save_usage()

    def can_make_request(self) -> bool:
        """Check if we can make more requests today"""
        return self.usage_data['requests'] < self.daily_limit

    def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics"""
        return {
            'date': self.usage_data['date'],
            'requests_today': self.usage_data['requests'],
            'errors_today': self.usage_data['errors'],
            'remaining_today': max(0, self.daily_limit - self.usage_data['requests']),
            'daily_limit': self.daily_limit
        }

class AIRateLimiter:
    """Combined rate limiter và quota manager cho AI API"""

    def __init__(self):
        self.rate_limiter = RateLimiter(requests_per_minute=30, requests_per_hour=500)
        self.quota_manager = QuotaManager()

    async def wait_for_slot(self) -> bool:
        """Wait for an available slot to make a request"""
        while True:
            # Check daily quota
            if not self.quota_manager.can_make_request():
                logger.warning("Daily quota exceeded, stopping for today")
                return False

            # Try to acquire rate limit slot
            if await self.rate_limiter.acquire():
                return True

            # Wait before retrying
            wait_time = 60  # Wait 1 minute
            logger.info(f"Rate limit reached, waiting {wait_time} seconds...")
            await asyncio.sleep(wait_time)

    def record_request(self, success: bool = True):
        """Record a completed request"""
        self.quota_manager.record_request(success)

    def get_status(self) -> Dict[str, Any]:
        """Get current status"""
        rate_status = self.rate_limiter.get_remaining_quota()
        quota_status = self.quota_manager.get_usage_stats()

        return {
            'rate_limiting': rate_status,
            'quota': quota_status,
            'can_proceed': quota_status['remaining_today'] > 0
        }

# Global instance
ai_rate_limiter = AIRateLimiter()

async def make_ai_request_with_rate_limit(func, *args, **kwargs):
    """Wrapper function để make AI requests với rate limiting"""
    # Wait for available slot
    if not await ai_rate_limiter.wait_for_slot():
        raise Exception("Daily quota exceeded")

    try:
        # Make the request
        result = await func(*args, **kwargs)

        # Record success
        ai_rate_limiter.record_request(success=True)
        return result

    except Exception as e:
        # Record failure
        ai_rate_limiter.record_request(success=False)

        # Check if it's a rate limit error
        if "rate limit" in str(e).lower() or "quota" in str(e).lower():
            logger.warning(f"Rate limit error: {e}, will retry later")
            raise e
        else:
            # Other error, re-raise
            raise e