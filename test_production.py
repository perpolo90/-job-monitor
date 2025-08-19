#!/usr/bin/env python3
"""
Test script for production setup
"""

import os
import sys
import json
from pathlib import Path

def test_environment_variables():
    """Test environment variable loading"""
    print("Testing environment variable loading...")
    
    # Set test environment variables
    os.environ['SENDER_EMAIL'] = 'test@example.com'
    os.environ['SENDER_PASSWORD'] = 'test-password'
    os.environ['RECIPIENT_EMAIL'] = 'test@example.com'
    os.environ['TIMEZONE'] = 'Europe/Warsaw'
    os.environ['SCHEDULE_TIME'] = '09:00'
    
    try:
        from job_monitor_production import ProductionJobMonitor
        monitor = ProductionJobMonitor()
        print("✅ ProductionJobMonitor initialized successfully")
        print(f"   Timezone: {monitor.config['timezone']}")
        print(f"   Schedule time: {monitor.config['schedule_time']}")
        print(f"   Companies: {len(monitor.config['companies'])}")
        print(f"   Keywords: {monitor.config['keywords']}")
        return True
    except Exception as e:
        print(f"❌ Error initializing ProductionJobMonitor: {e}")
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

def test_config_file():
    """Test config.json file"""
    print("\nTesting config.json...")
    
    config_file = Path('config.json')
    if not config_file.exists():
        print("❌ config.json not found")
        return False
    
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        print("✅ config.json loaded successfully")
        print(f"   Companies: {len(config.get('companies', []))}")
        print(f"   Keywords: {config.get('keywords', [])}")
        print(f"   Timezone: {config.get('timezone', 'not set')}")
        
        return True
    except Exception as e:
        print(f"❌ Error loading config.json: {e}")
        return False

def test_database():
    """Test database functionality"""
    print("\nTesting database...")
    
    try:
        from job_monitor import JobDatabase
        db = JobDatabase('test.db')
        db.init_database()
        print("✅ Database initialized successfully")
        
        # Clean up test database
        import os
        if os.path.exists('test.db'):
            os.remove('test.db')
        
        return True
    except Exception as e:
        print(f"❌ Error testing database: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Testing Production Setup for Railway Deployment")
    print("=" * 50)
    
    tests = [
        test_config_file,
        test_environment_variables,
        test_web_server,
        test_database
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Ready for Railway deployment.")
        return 0
    else:
        print("❌ Some tests failed. Please fix issues before deployment.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
