#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script để tự động tìm IP address của WSL có thể kết nối tới PostgreSQL
"""

import subprocess
import psycopg2
import sys

def get_wsl_ips():
    """Lấy danh sách IP addresses của WSL"""
    try:
        result = subprocess.run(['wsl', 'hostname', '-I'],
                              capture_output=True, text=True, shell=True)
        if result.returncode == 0:
            # Lấy IP đầu tiên (thường là IP chính)
            ips = result.stdout.strip().split()
            return ips
        else:
            print("❌ Không thể lấy WSL IP addresses")
            return []
    except Exception as e:
        print(f"❌ Lỗi khi lấy WSL IPs: {e}")
        return []

def test_postgres_connection(host, port=5433, user='airflow', password='airflow', dbname='airflow'):
    """Test kết nối tới PostgreSQL"""
    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            dbname=dbname,
            connect_timeout=5  # Timeout 5 giây
        )
        conn.close()
        return True
    except Exception as e:
        return False

def find_working_ip():
    """Tìm IP address hoạt động"""
    print("🔍 Đang tìm IP address WSL có thể kết nối tới PostgreSQL...")
    print()

    # Lấy danh sách IPs
    ips = get_wsl_ips()
    if not ips:
        print("❌ Không tìm thấy IP addresses nào")
        return None

    print(f"📋 Tìm thấy {len(ips)} IP addresses: {', '.join(ips)}")
    print()

    # Test từng IP
    working_ips = []
    for ip in ips:
        print(f"🔗 Testing {ip}...", end=" ")
        if test_postgres_connection(ip):
            print("✅ HOẠT ĐỘNG")
            working_ips.append(ip)
        else:
            print("❌ KHÔNG KẾT NỐI")

    print()
    return working_ips

def main():
    print("🚀 WSL PostgreSQL Connection Detector")
    print("=" * 40)

    working_ips = find_working_ip()

    if working_ips:
        print("🎉 Tìm thấy IP addresses hoạt động:")
        for ip in working_ips:
            print(f"   📍 {ip}:5433 (user: airflow, password: airflow, db: airflow)")

        print()
        print("💡 Copy IP này vào pgAdmin:")
        print(f"   Host: {working_ips[0]}")
        print("   Port: 5433")
        print("   Username: airflow")
        print("   Password: airflow")
        print("   Database: airflow")
    else:
        print("❌ Không tìm thấy IP address nào hoạt động")
        print()
        print("🔧 Kiểm tra:")
        print("   1. Docker containers có đang chạy không?")
        print("   2. PostgreSQL container healthy không?")
        print("   3. Firewall có block port 5433 không?")

if __name__ == "__main__":
    main()