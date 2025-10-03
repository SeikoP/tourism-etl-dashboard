#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script để monitor và manage AI API quota usage
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

def get_quota_status():
    """Get current quota status"""
    from src.utils.ai_rate_limiter import ai_rate_limiter

    try:
        status = ai_rate_limiter.get_status()
        return status
    except Exception as e:
        print(f"❌ Error getting quota status: {e}")
        return None

def reset_quota():
    """Reset quota for testing (use with caution)"""
    quota_file = "/opt/airflow/logs/quota_usage.json"
    try:
        if os.path.exists(quota_file):
            os.remove(quota_file)
            print("✅ Quota reset successfully")
        else:
            print("ℹ️  No quota file found")
    except Exception as e:
        print(f"❌ Error resetting quota: {e}")

def show_quota_history():
    """Show quota usage history"""
    logs_dir = "/opt/airflow/logs"
    try:
        if os.path.exists(logs_dir):
            report_files = [f for f in os.listdir(logs_dir) if f.startswith('quota_report_')]
            if report_files:
                print("📊 Quota History:")
                for filename in sorted(report_files, reverse=True)[:7]:  # Last 7 days
                    filepath = os.path.join(logs_dir, filename)
                    with open(filepath, 'r', encoding='utf-8') as f:
                        print(f"\n--- {filename} ---")
                        print(f.read().strip())
            else:
                print("ℹ️  No quota reports found")
        else:
            print("ℹ️  Logs directory not found")
    except Exception as e:
        print(f"❌ Error reading quota history: {e}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python quota_manager.py <command>")
        print("Commands:")
        print("  status    - Show current quota status")
        print("  reset     - Reset quota (use with caution)")
        print("  history   - Show quota usage history")
        return

    command = sys.argv[1].lower()

    if command == 'status':
        print("🔍 Checking AI API Quota Status...")
        status = get_quota_status()
        if status:
            print(f"""
=== AI API Quota Status ===

DAILY USAGE:
- Requests Today: {status['quota']['requests_today']}/{status['quota']['daily_limit']}
- Remaining Today: {status['quota']['remaining_today']}
- Errors Today: {status['quota']['errors_today']}

RATE LIMITING:
- Minute Remaining: {status['rate_limiting']['minute_remaining']}/30
- Hour Remaining: {status['rate_limiting']['hour_remaining']}/500

STATUS: {'✅ OK - Can proceed' if status['can_proceed'] else '❌ QUOTA EXCEEDED - Stop processing'}
""")
        else:
            print("❌ Could not get quota status")

    elif command == 'reset':
        print("⚠️  WARNING: This will reset quota counters!")
        confirm = input("Are you sure? (type 'yes' to confirm): ")
        if confirm.lower() == 'yes':
            reset_quota()
        else:
            print("❌ Reset cancelled")

    elif command == 'history':
        show_quota_history()

    else:
        print(f"❌ Unknown command: {command}")

if __name__ == "__main__":
    main()