#!/usr/bin/env python3
"""
Railway startup script - starts basic server first, then job monitor
"""

import os
import sys
import time
import threading
import subprocess
from basic_server import run_server

def start_job_monitor():
    """Start the job monitor in a separate process"""
    try:
        print("Starting job monitor...")
        # Start job monitor as a separate process
        subprocess.run([sys.executable, "job_monitor_railway.py"], check=True)
    except Exception as e:
        print(f"Job monitor error: {e}")

def main():
    """Main startup function"""
    print("=== Railway Job Monitor Startup ===")
    print(f"PORT: {os.getenv('PORT', '8000')}")
    print(f"TIMEZONE: {os.getenv('TIMEZONE', 'Europe/Warsaw')}")
    
    # Check environment variables
    required_vars = ['SENDER_EMAIL', 'SENDER_PASSWORD', 'RECIPIENT_EMAIL']
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"{var}: [SET]")
        else:
            print(f"{var}: [NOT SET]")
    
    # Start job monitor in a separate thread
    monitor_thread = threading.Thread(target=start_job_monitor, daemon=True)
    monitor_thread.start()
    print("Job monitor thread started")
    
    # Start the basic HTTP server (this will block)
    print("Starting basic HTTP server...")
    run_server()

if __name__ == "__main__":
    main()
