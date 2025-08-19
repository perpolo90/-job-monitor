#!/usr/bin/env python3
"""
Production-ready Job Monitor for Railway deployment
Uses environment variables for sensitive configuration
"""

import os
import sys
import json
import logging
import argparse
import schedule
import time
import pytz
from datetime import datetime
from pathlib import Path

# Import the existing job monitor classes
from job_monitor import JobMonitor, JobDatabase

# Configure logging for Railway
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Log to stdout for Railway
        logging.FileHandler('job_monitor.log')  # Also log to file
    ]
)

logger = logging.getLogger(__name__)

class ProductionJobMonitor:
    """Production-ready job monitor with environment variable configuration"""
    
    def __init__(self):
        """Initialize the production job monitor"""
        self.config = self._load_config()
        self.monitor = JobMonitor(
            timezone_str=self.config['timezone']
        )
        
    def _load_config(self):
        """Load configuration from environment variables and config.json"""
        # Load non-sensitive config from config.json
        config_file = Path('config.json')
        if config_file.exists():
            with open(config_file, 'r') as f:
                file_config = json.load(f)
        else:
            logger.error("config.json not found!")
            sys.exit(1)
        
        # Override with environment variables for sensitive data
        config = {
            'schedule_time': os.getenv('SCHEDULE_TIME', file_config.get('schedule_time', '09:00')),
            'keywords': file_config.get('keywords', ['operation', 'project', 'support']),
            'companies': file_config.get('companies', []),
            'timezone': os.getenv('TIMEZONE', file_config.get('timezone', 'Europe/Warsaw')),
            'database_url': os.getenv('DATABASE_URL', 'jobs.db'),
            'email': {
                'smtp_server': os.getenv('SMTP_SERVER', file_config.get('email', {}).get('smtp_server', 'smtp.gmail.com')),
                'smtp_port': int(os.getenv('SMTP_PORT', file_config.get('email', {}).get('smtp_port', 587))),
                'sender_email': os.getenv('SENDER_EMAIL'),
                'sender_password': os.getenv('SENDER_PASSWORD'),
                'recipient_email': os.getenv('RECIPIENT_EMAIL')
            }
        }
        
        # Validate required environment variables
        required_env_vars = ['SENDER_EMAIL', 'SENDER_PASSWORD', 'RECIPIENT_EMAIL']
        missing_vars = [var for var in required_env_vars if not config['email'].get(var.lower().replace('_', '_'))]
        
        if missing_vars:
            logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
            logger.error("Please set these in your Railway environment variables")
            sys.exit(1)
        
        logger.info(f"Configuration loaded successfully")
        logger.info(f"Timezone: {config['timezone']}")
        logger.info(f"Schedule time: {config['schedule_time']}")
        logger.info(f"Companies: {len(config['companies'])}")
        logger.info(f"Keywords: {config['keywords']}")
        
        return config
    
    def run_monitoring_cycle(self):
        """Run a single monitoring cycle"""
        try:
            logger.info("Starting monitoring cycle...")
            
            # Update the monitor's config with current settings
            self.monitor.config = self.config
            
            # Run the monitoring cycle
            self.monitor.run_monitoring_cycle()
            
            logger.info("Monitoring cycle completed successfully")
            
        except Exception as e:
            logger.error(f"Error during monitoring cycle: {e}")
            # Don't exit, just log the error for Railway
    
    def start_scheduler(self):
        """Start the scheduled job monitor"""
        schedule_time = self.config['schedule_time']
        timezone_str = self.config['timezone']
        
        logger.info(f"Setting up daily schedule at {schedule_time} {timezone_str}")
        
        # Schedule the job
        schedule.every().day.at(schedule_time).do(self.run_monitoring_cycle)
        
        # Run once immediately
        logger.info("Running initial monitoring cycle...")
        self.run_monitoring_cycle()
        
        # Keep the scheduler running
        logger.info("Scheduler started. Waiting for next scheduled run...")
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute

def main():
    """Main function for production job monitor"""
    parser = argparse.ArgumentParser(description='Production Job Monitor for Railway')
    parser.add_argument('--test', action='store_true', help='Run once immediately instead of scheduling')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    parser.add_argument('--browser', action='store_true', help='Show browser window (disable headless mode)')
    parser.add_argument('--timezone', help='Override timezone setting')
    parser.add_argument('--web', action='store_true', help='Start web server instead of job monitor')
    
    args = parser.parse_args()
    
    # Set debug logging if requested
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)
    
    # Override timezone if provided
    if args.timezone:
        os.environ['TIMEZONE'] = args.timezone
    
    try:
        if args.web:
            # Start web server
            from web_server import run_server
            logger.info("Starting web server...")
            run_server()
        else:
            # Start job monitor
            monitor = ProductionJobMonitor()
            
            if args.test:
                # Run once immediately
                logger.info("Running in test mode (single execution)")
                monitor.run_monitoring_cycle()
            else:
                # Start scheduler
                logger.info("Starting production job monitor with scheduler")
                monitor.start_scheduler()
                
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully...")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
