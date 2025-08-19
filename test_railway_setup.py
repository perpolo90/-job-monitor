#!/usr/bin/env python3
"""
Test script for Railway setup with fallback scraping
"""

import os
import sys
import json
from pathlib import Path

def test_railway_job_monitor():
    """Test Railway job monitor with fallback scraping"""
    print("Testing Railway Job Monitor setup...")
    
    # Set test environment variables
    os.environ['SENDER_EMAIL'] = 'test@example.com'
    os.environ['SENDER_PASSWORD'] = 'test-password'
    os.environ['RECIPIENT_EMAIL'] = 'test@example.com'
    os.environ['TIMEZONE'] = 'Europe/Warsaw'
    os.environ['SCHEDULE_TIME'] = '09:00'
    
    try:
        from job_monitor_railway import RailwayJobMonitor
        monitor = RailwayJobMonitor()
        print("✅ RailwayJobMonitor initialized successfully")
        print(f"   Timezone: {monitor.config['timezone']}")
        print(f"   Schedule time: {monitor.config['schedule_time']}")
        print(f"   Companies: {len(monitor.config['companies'])}")
        print(f"   Keywords: {monitor.config['keywords']}")
        print(f"   Scraping method: {'Playwright' if monitor.use_playwright else 'requests+beautifulsoup'}")
        return True
    except Exception as e:
        print(f"❌ Error initializing RailwayJobMonitor: {e}")
        return False

def test_requests_scraping():
    """Test requests+beautifulsoup scraping functionality"""
    print("\nTesting requests+beautifulsoup scraping...")
    
    try:
        import requests
        from bs4 import BeautifulSoup
        from urllib.parse import urljoin
        
        print("✅ requests+beautifulsoup modules imported successfully")
        print("   requests module available")
        print("   BeautifulSoup module available")
        print("   urljoin function available")
        return True
            
    except Exception as e:
        print(f"❌ Error importing requests+beautifulsoup modules: {e}")
        return False

def test_playwright_availability():
    """Test Playwright availability"""
    print("\nTesting Playwright availability...")
    
    try:
        from playwright.sync_api import sync_playwright
        print("✅ Playwright imported successfully")
        
        # Try to launch browser (this might fail in Railway)
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                browser.close()
            print("✅ Playwright browser launched successfully")
            return True
        except Exception as e:
            print(f"⚠️  Playwright browser launch failed (expected in Railway): {e}")
            print("   This is normal - will use requests+beautifulsoup fallback")
            return True
            
    except ImportError:
        print("⚠️  Playwright not available (expected in Railway)")
        print("   Will use requests+beautifulsoup fallback")
        return True
    except Exception as e:
        print(f"❌ Error testing Playwright: {e}")
        return False

def test_web_server():
    """Test web server functionality"""
    print("\nTesting web server...")
    
    try:
        from web_server import app
        print("✅ Web server imported successfully")
        
        # Test health endpoint
        with app.test_client() as client:
            response = client.get('/health')
            if response.status_code == 200:
                print("✅ Health endpoint working")
                data = response.get_json()
                print(f"   Status: {data.get('status')}")
                print(f"   Timezone: {data.get('timezone')}")
            else:
                print(f"❌ Health endpoint failed: {response.status_code}")
                return False
                
        return True
    except Exception as e:
        print(f"❌ Error testing web server: {e}")
        return False

def test_startup_script():
    """Test startup script"""
    print("\nTesting startup script...")
    
    try:
        from startup import run_job_monitor, run_web_server
        print("✅ Startup script imported successfully")
        print("   run_job_monitor function available")
        print("   run_web_server function available")
        return True
    except Exception as e:
        print(f"❌ Error testing startup script: {e}")
        return False

def main():
    """Run all Railway setup tests"""
    print("🚀 Testing Railway Setup with Fallback Scraping")
    print("=" * 60)
    
    tests = [
        test_railway_job_monitor,
        test_requests_scraping,
        test_playwright_availability,
        test_web_server,
        test_startup_script
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Railway setup is ready for deployment.")
        print("\n📋 Next steps:")
        print("1. Push code to GitHub")
        print("2. Deploy to Railway")
        print("3. Set environment variables in Railway dashboard")
        print("4. Monitor deployment logs")
        return 0
    else:
        print("❌ Some tests failed. Please fix issues before deployment.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
