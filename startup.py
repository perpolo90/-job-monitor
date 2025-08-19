#!/usr/bin/env python3
"""
Startup script for Railway deployment
Runs both web server and job monitor
"""

import os
import sys
import threading
import time
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('startup.log')
    ]
)

logger = logging.getLogger(__name__)

def run_web_server():
    """Run the web server in a separate thread"""
    try:
        from web_server import run_server
        logger.info("Starting web server...")
        run_server()
    except Exception as e:
        logger.error(f"Web server error: {e}")

def run_job_monitor():
    """Run the job monitor in a separate thread"""
    try:
        from job_monitor_railway import RailwayJobMonitor
        monitor = RailwayJobMonitor()
        logger.info("Starting Railway job monitor...")
        monitor.start_scheduler()
    except Exception as e:
        logger.error(f"Job monitor error: {e}")

def main():
    """Main startup function"""
    logger.info("Starting Job Monitor System for Railway...")
    
    # Check if we should run in web-only mode
    if os.getenv('WEB_ONLY', 'false').lower() == 'true':
        logger.info("Running in web-only mode")
        run_web_server()
        return
    
    # Check if we should run in monitor-only mode
    if os.getenv('MONITOR_ONLY', 'false').lower() == 'true':
        logger.info("Running in monitor-only mode")
        run_job_monitor()
        return
    
    # Default: run both web server and job monitor
    logger.info("Starting both web server and job monitor...")
    
    # Start web server in a separate thread
    web_thread = threading.Thread(target=run_web_server, daemon=True)
    web_thread.start()
    
    # Give web server time to start
    time.sleep(2)
    
    # Start job monitor in main thread
    run_job_monitor()

if __name__ == "__main__":
    main()
