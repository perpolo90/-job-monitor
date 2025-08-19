#!/usr/bin/env python3
"""
Railway-optimized Job Monitor with Playwright fallback to requests+beautifulsoup
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

class RailwayJobMonitor:
    """Railway-optimized job monitor with fallback scraping methods"""
    
    def __init__(self):
        """Initialize the Railway job monitor"""
        self.use_playwright = self._check_playwright_availability()
        self.config = self._load_config()
        self.monitor = JobMonitor(
            timezone_str=self.config['timezone']
        )
        
    def _check_playwright_availability(self):
        """Check if Playwright is available and working"""
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                browser.close()
            logger.info("Playwright is available and working")
            return True
        except Exception as e:
            logger.warning(f"Playwright not available, using requests+beautifulsoup fallback: {e}")
            return False
    
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
        logger.info(f"Scraping method: {'Playwright' if self.use_playwright else 'requests+beautifulsoup'}")
        
        return config
    
    def run_monitoring_cycle(self):
        """Run a single monitoring cycle with fallback scraping"""
        try:
            logger.info("Starting monitoring cycle...")
            
            # Update the monitor's config with current settings
            self.monitor.config = self.config
            
            # Override the scraping method if Playwright is not available
            if not self.use_playwright:
                self._patch_for_requests_scraping()
            
            # Run the monitoring cycle
            self.monitor.run_monitoring_cycle()
            
            logger.info("Monitoring cycle completed successfully")
            
        except Exception as e:
            logger.error(f"Error during monitoring cycle: {e}")
            # Don't exit, just log the error for Railway
    
    def _patch_for_requests_scraping(self):
        """Patch the job monitor to use requests+beautifulsoup instead of Playwright"""
        try:
            import requests
            from bs4 import BeautifulSoup
            from urllib.parse import urljoin
            import time
            
            def scrape_job_site_requests(company_config):
                """Scrape job site using requests and BeautifulSoup"""
                url = company_config['url']
                selectors = company_config.get('selectors', {})
                
                logger.info(f"Scraping {company_config['name']} using requests+beautifulsoup")
                
                try:
                    # Add headers to mimic a real browser
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                        'Accept-Language': 'en-US,en;q=0.5',
                        'Accept-Encoding': 'gzip, deflate',
                        'Connection': 'keep-alive',
                        'Upgrade-Insecure-Requests': '1',
                    }
                    
                    response = requests.get(url, headers=headers, timeout=30)
                    response.raise_for_status()
                    
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Find job containers
                    job_containers = []
                    for selector in selectors.get('job_container', '').split(','):
                        selector = selector.strip()
                        if selector:
                            containers = soup.select(selector)
                            if containers:
                                job_containers.extend(containers)
                                break
                    
                    if not job_containers:
                        # Try fallback selectors
                        fallback_selectors = [
                            '.job', '.position', '.opening', '.posting',
                            '[class*="job"]', '[class*="position"]',
                            'article', 'section', 'div[class*="job"]'
                        ]
                        for selector in fallback_selectors:
                            containers = soup.select(selector)
                            if containers:
                                job_containers = containers
                                break
                    
                    jobs = []
                    for container in job_containers:
                        try:
                            # Extract job title
                            title = ""
                            for title_selector in selectors.get('title', '').split(','):
                                title_selector = title_selector.strip()
                                if title_selector:
                                    title_elem = container.select_one(title_selector)
                                    if title_elem:
                                        title = title_elem.get_text(strip=True)
                                        break
                            
                            if not title:
                                # Try to find any text that looks like a job title
                                title_elem = container.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                                if title_elem:
                                    title = title_elem.get_text(strip=True)
                            
                            # Extract job link
                            link = ""
                            for link_selector in selectors.get('link', '').split(','):
                                link_selector = link_selector.strip()
                                if link_selector:
                                    link_elem = container.select_one(link_selector)
                                    if link_elem and link_elem.get('href'):
                                        link = link_elem.get('href')
                                        break
                            
                            if not link:
                                # Try to find any link in the container
                                link_elem = container.find('a')
                                if link_elem and link_elem.get('href'):
                                    link = link_elem.get('href')
                            
                            # Make link absolute if it's relative
                            if link and not link.startswith('http'):
                                link = urljoin(url, link)
                            
                            if title and link:
                                jobs.append({
                                    'title': title,
                                    'url': link,
                                    'company': company_config['name']
                                })
                                
                        except Exception as e:
                            logger.debug(f"Error parsing job container: {e}")
                            continue
                    
                    logger.info(f"Found {len(jobs)} jobs for {company_config['name']}")
                    return jobs
                    
                except Exception as e:
                    logger.error(f"Error scraping {company_config['name']}: {e}")
                    return []
            
            # Replace the scraping method in the monitor
            self.monitor.scrape_job_site = scrape_job_site_requests
            logger.info("Patched job monitor to use requests+beautifulsoup scraping")
            
        except ImportError as e:
            logger.error(f"Failed to import requests/beautifulsoup: {e}")
            logger.error("Please ensure requests and beautifulsoup4 are installed")
    
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
    """Main function for Railway job monitor"""
    parser = argparse.ArgumentParser(description='Railway Job Monitor with Fallback Scraping')
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
            monitor = RailwayJobMonitor()
            
            if args.test:
                # Run once immediately
                logger.info("Running in test mode (single execution)")
                monitor.run_monitoring_cycle()
            else:
                # Start scheduler
                logger.info("Starting Railway job monitor with scheduler")
                monitor.start_scheduler()
                
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully...")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
