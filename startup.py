#!/usr/bin/env python3
"""
Startup script for Railway deployment
Runs both web server and job monitor with enhanced error handling
"""

import os
import sys
import threading
import time
import logging
import traceback
from pathlib import Path

# Configure logging with more verbose startup information
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('startup.log')
    ]
)

logger = logging.getLogger(__name__)

def log_environment():
    """Log environment information for debugging"""
    logger.info("=== Environment Information ===")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Working directory: {os.getcwd()}")
    logger.info(f"Files in directory: {os.listdir('.')}")
    
    # Log environment variables (excluding passwords)
    logger.info("Environment variables:")
    for key, value in os.environ.items():
        if 'PASSWORD' not in key.upper():
            logger.info(f"  {key}: {value}")
        else:
            logger.info(f"  {key}: [HIDDEN]")
    
    logger.info("=== End Environment Information ===")

def run_web_server():
    """Run the web server in a separate thread with error handling"""
    try:
        logger.info("Starting web server thread...")
        from web_server import run_server
        logger.info("Web server module imported successfully")
        run_server()
    except ImportError as e:
        logger.error(f"Failed to import web server module: {e}")
        logger.error(traceback.format_exc())
    except Exception as e:
        logger.error(f"Web server error: {e}")
        logger.error(traceback.format_exc())

def run_job_monitor():
    """Run the job monitor in a separate thread with error handling"""
    try:
        logger.info("Starting job monitor thread...")
        from job_monitor_railway import RailwayJobMonitor
        logger.info("Railway job monitor module imported successfully")
        monitor = RailwayJobMonitor()
        logger.info("Railway job monitor initialized successfully")
        monitor.start_scheduler()
    except ImportError as e:
        logger.error(f"Failed to import job monitor module: {e}")
        logger.error(traceback.format_exc())
    except Exception as e:
        logger.error(f"Job monitor error: {e}")
        logger.error(traceback.format_exc())

def check_dependencies():
    """Check if all required dependencies are available"""
    logger.info("Checking dependencies...")
    
    required_modules = [
        'flask',
        'requests', 
        'beautifulsoup4',
        'schedule',
        'pytz',
        'sqlite3'
    ]
    
    missing_modules = []
    for module in required_modules:
        try:
            if module == 'beautifulsoup4':
                import bs4
            elif module == 'sqlite3':
                import sqlite3
            else:
                __import__(module)
            logger.info(f"✓ {module} available")
        except ImportError:
            logger.error(f"✗ {module} missing")
            missing_modules.append(module)
    
    if missing_modules:
        logger.error(f"Missing required modules: {missing_modules}")
        return False
    
    logger.info("All dependencies available")
    return True

def check_config_files():
    """Check if required configuration files exist"""
    logger.info("Checking configuration files...")
    
    required_files = ['config.json', 'requirements.txt']
    missing_files = []
    
    for file in required_files:
        if Path(file).exists():
            logger.info(f"✓ {file} exists")
        else:
            logger.error(f"✗ {file} missing")
            missing_files.append(file)
    
    if missing_files:
        logger.error(f"Missing required files: {missing_files}")
        return False
    
    logger.info("All configuration files present")
    return True

def main():
    """Main startup function with enhanced error handling"""
    logger.info("=== Job Monitor Startup ===")
    
    # Log environment information
    log_environment()
    
    # Check dependencies
    if not check_dependencies():
        logger.error("Dependency check failed - exiting")
        sys.exit(1)
    
    # Check configuration files
    if not check_config_files():
        logger.error("Configuration check failed - exiting")
        sys.exit(1)
    
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
    logger.info("Web server thread started")
    
    # Give web server time to start
    logger.info("Waiting for web server to start...")
    time.sleep(5)
    
    # Check if web server is responding
    try:
        import requests
        response = requests.get('http://localhost:8000/health', timeout=10)
        if response.status_code == 200:
            logger.info("Web server is responding to health checks")
        else:
            logger.warning(f"Web server health check returned status {response.status_code}")
    except Exception as e:
        logger.warning(f"Web server health check failed: {e}")
    
    # Start job monitor in main thread
    logger.info("Starting job monitor...")
    run_job_monitor()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt - shutting down gracefully")
    except Exception as e:
        logger.error(f"Fatal error in startup: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)
