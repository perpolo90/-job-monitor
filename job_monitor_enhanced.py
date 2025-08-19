#!/usr/bin/env python3
"""
Enhanced Daily Job Monitor - A comprehensive job monitoring system that scrapes job sites
and sends email alerts for new positions matching your criteria.

This script will:
1. Scrape job listings from configured company websites
2. Filter jobs based on keywords in job titles
3. Send email alerts for new jobs
4. Store job data in SQLite database with application status tracking
5. Run daily with proper timezone handling
6. Support multiple job board platforms with generic selectors

Author: Enhanced Job Monitor System
"""

import requests
import json
import schedule
import time
import smtplib
import argparse
import logging
import sqlite3
from datetime import datetime, timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import os
import sys
import pytz
import hashlib
from playwright.sync_api import sync_playwright

# Set up logging for debugging and monitoring
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('job_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class JobDatabase:
    """
    SQLite database manager for job tracking and application status.
    """
    
    def __init__(self, db_file='jobs.db'):
        """
        Initialize the database and create tables if they don't exist.
        
        Args:
            db_file (str): Path to the SQLite database file
        """
        self.db_file = db_file
        self.init_database()
    
    def init_database(self):
        """Create database tables if they don't exist."""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            
            # Create jobs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_hash TEXT UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    company TEXT NOT NULL,
                    url TEXT NOT NULL,
                    location TEXT,
                    department TEXT,
                    employment_type TEXT,
                    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'new',
                    notes TEXT
                )
            ''')
            
            # Create job_status_history table for tracking status changes
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS job_status_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_hash TEXT NOT NULL,
                    status TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    notes TEXT,
                    FOREIGN KEY (job_hash) REFERENCES jobs (job_hash)
                )
            ''')
            
            conn.commit()
            logger.info(f"Database initialized: {self.db_file}")
    
    def job_exists(self, job_hash):
        """Check if a job already exists in the database."""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT 1 FROM jobs WHERE job_hash = ?', (job_hash,))
            return cursor.fetchone() is not None
    
    def add_job(self, job_data):
        """Add a new job to the database."""
        job_hash = self.generate_job_hash(job_data)
        
        if self.job_exists(job_hash):
            return False
        
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO jobs (job_hash, title, company, url, location, department, employment_type)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                job_hash,
                job_data.get('title', ''),
                job_data.get('company', ''),
                job_data.get('url', ''),
                job_data.get('location', ''),
                job_data.get('department', ''),
                job_data.get('employment_type', '')
            ))
            
            # Add initial status to history
            cursor.execute('''
                INSERT INTO job_status_history (job_hash, status, notes)
                VALUES (?, 'new', 'Job discovered by monitor')
            ''', (job_hash,))
            
            conn.commit()
            logger.debug(f"Added new job to database: {job_data.get('title', '')} at {job_data.get('company', '')}")
            return True
    
    def update_job_status(self, job_hash, status, notes=None):
        """Update the status of a job and add to history."""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            
            # Update job status
            cursor.execute('''
                UPDATE jobs SET status = ?, last_updated = CURRENT_TIMESTAMP
                WHERE job_hash = ?
            ''', (status, job_hash))
            
            # Add to history
            cursor.execute('''
                INSERT INTO job_status_history (job_hash, status, notes)
                VALUES (?, ?, ?)
            ''', (job_hash, status, notes))
            
            conn.commit()
            logger.debug(f"Updated job status: {job_hash} -> {status}")
    
    def get_jobs_by_status(self, status):
        """Get all jobs with a specific status."""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM jobs WHERE status = ? ORDER BY last_updated DESC
            ''', (status,))
            return cursor.fetchall()
    
    def generate_job_hash(self, job_data):
        """Generate a unique hash for a job based on title, company, and URL."""
        hash_string = f"{job_data.get('title', '')}{job_data.get('company', '')}{job_data.get('url', '')}"
        return hashlib.md5(hash_string.encode()).hexdigest()

class JobMonitor:
    """
    Enhanced job monitor with database tracking, timezone support, and platform-specific selectors.
    """
    
    def __init__(self, config_file='config.json', headless=True, timezone_str='Europe/Warsaw'):
        """
        Initialize the job monitor with configuration settings.
        
        Args:
            config_file (str): Path to the configuration JSON file
            headless (bool): Whether to run browser in headless mode
            timezone_str (str): Timezone string for scheduling
        """
        self.config_file = config_file
        self.config = self.load_config()
        self.headless = headless
        self.timezone_str = timezone_str
        self.timezone = pytz.timezone(timezone_str)
        
        # Initialize database
        self.db = JobDatabase()
        
        # Set up email configuration
        self.email_config = self.config.get('email', {})
        
        # Generic selectors for common job platforms
        self.generic_selectors = {
            'lever': {
                'job_container': '.posting',
                'title': '.posting-btn, .posting-name',
                'link': 'a.posting-btn'
            },
            'greenhouse': {
                'job_container': '.opening',
                'title': '.opening a, .opening h3',
                'link': '.opening a'
            },
            'ashby': {
                'job_container': '.job-posting',
                'title': '.job-posting h3, .job-posting a',
                'link': '.job-posting a'
            },
            'workday': {
                'job_container': '.job-result',
                'title': '.job-result h3, .job-result a',
                'link': '.job-result a'
            },
            'bamboo': {
                'job_container': '.job-listing',
                'title': '.job-listing h3, .job-listing a',
                'link': '.job-listing a'
            }
        }
        
        logger.info(f"Enhanced Job Monitor initialized successfully (Timezone: {timezone_str})")
    
    def load_config(self):
        """
        Load configuration from JSON file.
        
        Returns:
            dict: Configuration dictionary
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            json.JSONDecodeError: If config file is invalid JSON
        """
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            logger.info(f"Configuration loaded from {self.config_file}")
            return config
        except FileNotFoundError:
            logger.error(f"Configuration file {self.config_file} not found!")
            sys.exit(1)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {self.config_file}: {e}")
            sys.exit(1)
    
    def detect_job_platform(self, url):
        """
        Detect the job platform based on URL patterns.
        
        Args:
            url (str): The job site URL
            
        Returns:
            str: Platform name (lever, greenhouse, ashby, etc.) or 'custom'
        """
        url_lower = url.lower()
        
        if 'lever.co' in url_lower:
            return 'lever'
        elif 'boards.greenhouse.io' in url_lower or 'greenhouse' in url_lower:
            return 'greenhouse'
        elif 'jobs.ashbyhq.com' in url_lower:
            return 'ashby'
        elif 'workday' in url_lower:
            return 'workday'
        elif 'bamboohr' in url_lower:
            return 'bamboo'
        else:
            return 'custom'
    
    def get_selectors_for_company(self, company_config):
        """
        Get the appropriate selectors for a company, with fallback to generic selectors.
        
        Args:
            company_config (dict): Company configuration
            
        Returns:
            dict: Selectors to use for scraping
        """
        # First, use company-specific selectors if provided
        if 'selectors' in company_config and company_config['selectors']:
            return company_config['selectors']
        
        # Otherwise, try to detect platform and use generic selectors
        platform = self.detect_job_platform(company_config.get('url', ''))
        if platform in self.generic_selectors:
            logger.debug(f"Using {platform} generic selectors for {company_config.get('name', 'Unknown')}")
            return self.generic_selectors[platform]
        
        # Fallback to very generic selectors
        logger.warning(f"No specific selectors found for {company_config.get('name', 'Unknown')}, using fallback selectors")
        return {
            'job_container': '.job, .position, .opening, .posting, [class*="job"], [class*="position"]',
            'title': 'h1, h2, h3, h4, .title, .job-title, .position-title, a',
            'link': 'a'
        }
    
    def scrape_job_site(self, company_name, url, selectors):
        """
        Scrape job listings from a company website using Playwright.
        
        Args:
            company_name (str): Name of the company
            url (str): URL of the careers page
            selectors (dict): CSS selectors for job elements
            
        Returns:
            list: List of job dictionaries
        """
        jobs = []
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=self.headless)
                page = browser.new_page()
                
                logger.info(f"Scraping jobs from {company_name} at {url}")
                
                # Navigate to the page
                page.goto(url, wait_until='networkidle', timeout=30000)
                page.wait_for_timeout(3000)  # Wait for dynamic content
                
                # Get selectors
                job_container_selector = selectors.get('job_container', '')
                title_selector = selectors.get('title', '')
                link_selector = selectors.get('link', '')
                
                logger.debug(f"Using selectors for {company_name}: {selectors}")
                
                # Wait for job container elements to load
                try:
                    page.wait_for_selector(job_container_selector, timeout=10000)
                except Exception as e:
                    logger.warning(f"Timeout waiting for job containers on {company_name}: {e}")
                    # Continue anyway, might find jobs with different selectors
                
                # Find job elements
                job_elements = page.query_selector_all(job_container_selector)
                
                if not job_elements:
                    logger.warning(f"No job elements found for {company_name} with selector: {job_container_selector}")
                    self.print_html_debug_playwright(page, company_name, selectors)
                    return jobs
                
                logger.info(f"Found {len(job_elements)} job elements for {company_name}")
                
                # Extract job information from each element
                for elem in job_elements:
                    try:
                        # Extract title
                        title_elem = elem.query_selector(title_selector) if title_selector else elem
                        title = title_elem.inner_text().strip() if title_elem else "Unknown Title"
                        
                        # Extract link
                        link_elem = elem.query_selector(link_selector) if link_selector else elem
                        link = link_elem.get_attribute('href') if link_elem else ""
                        
                        # Make link absolute if it's relative
                        if link and not link.startswith(('http://', 'https://')):
                            link = urljoin(url, link)
                        
                        # Extract additional information if available
                        location = ""
                        department = ""
                        employment_type = ""
                        
                        # Try to extract location from common patterns
                        location_selectors = ['[class*="location"]', '[class*="place"]', '.location', '.place']
                        for loc_selector in location_selectors:
                            loc_elem = elem.query_selector(loc_selector)
                            if loc_elem:
                                location = loc_elem.inner_text().strip()
                                break
                        
                        # Try to extract department
                        dept_selectors = ['[class*="department"]', '[class*="team"]', '.department', '.team']
                        for dept_selector in dept_selectors:
                            dept_elem = elem.query_selector(dept_selector)
                            if dept_elem:
                                department = dept_elem.inner_text().strip()
                                break
                        
                        # Try to extract employment type
                        type_selectors = ['[class*="type"]', '[class*="employment"]', '.type', '.employment']
                        for type_selector in type_selectors:
                            type_elem = elem.query_selector(type_selector)
                            if type_elem:
                                employment_type = type_elem.inner_text().strip()
                                break
                        
                        if title and title != "Unknown Title":
                            job_data = {
                                'title': title,
                                'company': company_name,
                                'url': link,
                                'location': location,
                                'department': department,
                                'employment_type': employment_type
                            }
                            jobs.append(job_data)
                    
                    except Exception as e:
                        logger.warning(f"Failed to parse job element from {company_name}: {e}")
                        continue
                
                browser.close()
                
        except Exception as e:
            logger.error(f"Failed to scrape {company_name} at {url}: {e}")
            if hasattr(e, '__traceback__'):
                import traceback
                logger.debug(f"Traceback: {traceback.format_exc()}")
        
        return jobs
    
    def print_html_debug_playwright(self, page, company_name, selectors):
        """
        Print debug information about the HTML content when no jobs are found.
        
        Args:
            page: Playwright page object
            company_name (str): Name of the company
            selectors (dict): Selectors being used
        """
        try:
            html_content = page.content()
            
            # Save full HTML to file
            timestamp = int(time.time())
            filename = f"debug_{company_name.lower().replace(' ', '_')}_{timestamp}.html"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.debug(f"Saved full HTML to {filename}")
            logger.debug(f"First 1000 characters of HTML: {html_content[:1000]}")
            
            # Try to find potential job elements with common selectors
            potential_selectors = [
                'div[class*="job"]', 'div[class*="position"]', 'div[class*="opening"]',
                'li[class*="job"]', 'li[class*="position"]', 'li[class*="opening"]',
                '.job', '.position', '.opening', '.posting', '.career'
            ]
            
            for selector in potential_selectors:
                elements = page.query_selector_all(selector)
                if elements:
                    logger.debug(f"Found {len(elements)} elements with selector: {selector}")
                    for i, elem in enumerate(elements[:3]):  # Show first 3
                        try:
                            text = elem.inner_text()[:100]
                            logger.debug(f"  Element {i+1}: {text}...")
                        except:
                            pass
            
        except Exception as e:
            logger.error(f"Error in HTML debug: {e}")
    
    def filter_jobs_by_keywords(self, jobs, keywords):
        """
        Filter jobs based on keywords in the job title.
        
        Args:
            jobs (list): List of job dictionaries
            keywords (list): List of keywords to match
            
        Returns:
            list: Filtered list of jobs
        """
        if not keywords:
            return jobs
        
        filtered_jobs = []
        for job in jobs:
            title = job.get('title', '').lower()
            if any(keyword.lower() in title for keyword in keywords):
                filtered_jobs.append(job)
        
        logger.info(f"Filtered {len(jobs)} jobs to {len(filtered_jobs)} matching keywords")
        return filtered_jobs
    
    def get_new_jobs(self, jobs):
        """
        Get jobs that haven't been seen before using database.
        
        Args:
            jobs (list): List of job dictionaries
            
        Returns:
            list: List of new jobs
        """
        new_jobs = []
        for job in jobs:
            if self.db.add_job(job):
                new_jobs.append(job)
        
        logger.info(f"Found {len(new_jobs)} new jobs out of {len(jobs)} total")
        return new_jobs
    
    def send_email_alert(self, jobs):
        """
        Send email alert for new jobs.
        
        Args:
            jobs (list): List of new job dictionaries
        """
        if not jobs:
            return
        
        try:
            # Create email message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"New Job Alerts: {len(jobs)} positions found"
            msg['From'] = self.email_config.get('sender_email', '')
            msg['To'] = self.email_config.get('recipient_email', '')
            
            # Create HTML content
            html_content = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    .job {{ border: 1px solid #ddd; margin: 10px 0; padding: 15px; border-radius: 5px; }}
                    .title {{ font-size: 18px; font-weight: bold; color: #333; }}
                    .company {{ color: #666; font-size: 14px; }}
                    .location {{ color: #888; font-size: 12px; }}
                    .link {{ color: #007bff; text-decoration: none; }}
                    .link:hover {{ text-decoration: underline; }}
                </style>
            </head>
            <body>
                <h2>New Job Alerts</h2>
                <p>Found {len(jobs)} new positions matching your criteria:</p>
            """
            
            for job in jobs:
                html_content += f"""
                <div class="job">
                    <div class="title">{job.get('title', 'Unknown Title')}</div>
                    <div class="company">{job.get('company', 'Unknown Company')}</div>
                    <div class="location">{job.get('location', 'Location not specified')}</div>
                    <div class="department">{job.get('department', '')}</div>
                    <div class="employment_type">{job.get('employment_type', '')}</div>
                    <a href="{job.get('url', '#')}" class="link">View Job</a>
                </div>
                """
            
            html_content += """
            </body>
            </html>
            """
            
            msg.attach(MIMEText(html_content, 'html'))
            
            # Send email
            with smtplib.SMTP(self.email_config.get('smtp_server', ''), self.email_config.get('smtp_port', 587)) as server:
                server.starttls()
                server.login(
                    self.email_config.get('sender_email', ''),
                    self.email_config.get('sender_password', '')
                )
                server.send_message(msg)
            
            logger.info(f"Email alert sent successfully for {len(jobs)} new jobs")
            
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
    
    def run_monitoring_cycle(self):
        """
        Run a complete monitoring cycle: scrape, filter, and alert.
        
        Returns:
            list: List of new jobs found
        """
        logger.info("Starting job monitoring cycle")
        
        all_jobs = []
        
        # Scrape jobs from all configured companies
        companies = self.config.get('companies', [])
        for company in companies:
            company_name = company.get('name', 'Unknown Company')
            url = company.get('url')
            
            if not url:
                logger.warning(f"No URL configured for {company_name}, skipping")
                continue
            
            # Get appropriate selectors for this company
            selectors = self.get_selectors_for_company(company)
            
            jobs = self.scrape_job_site(company_name, url, selectors)
            all_jobs.extend(jobs)
        
        # Filter jobs by keywords
        keywords = self.config.get('keywords', [])
        filtered_jobs = self.filter_jobs_by_keywords(all_jobs, keywords)
        
        # Get new jobs
        new_jobs = self.get_new_jobs(filtered_jobs)
        
        # Send email alert if there are new jobs
        if new_jobs:
            self.send_email_alert(new_jobs)
        
        logger.info(f"Monitoring cycle completed. Found {len(new_jobs)} new jobs out of {len(all_jobs)} total")
        return new_jobs

def get_poland_time():
    """Get current time in Poland timezone."""
    warsaw_tz = pytz.timezone('Europe/Warsaw')
    return datetime.now(warsaw_tz)

def main():
    """
    Main function to run the enhanced job monitor.
    """
    parser = argparse.ArgumentParser(description='Enhanced Daily Job Monitor')
    parser.add_argument('--test', action='store_true', 
                       help='Run monitoring cycle immediately instead of scheduling')
    parser.add_argument('--config', default='config.json',
                       help='Path to configuration file (default: config.json)')
    parser.add_argument('--debug', action='store_true',
                       help='Enable verbose debugging output including HTML content')
    parser.add_argument('--browser', action='store_true',
                       help='Show browser window (disable headless mode) for debugging')
    parser.add_argument('--timezone', default='Europe/Warsaw',
                       help='Timezone for scheduling (default: Europe/Warsaw)')
    
    args = parser.parse_args()
    
    # Enable debug logging if --debug flag is used
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        print("DEBUG mode enabled - will show detailed HTML content and selector information")
    
    # Initialize job monitor with headless setting and timezone
    headless = not args.browser
    monitor = JobMonitor(args.config, headless=headless, timezone_str=args.timezone)
    
    if args.test:
        # Run immediately for testing
        logger.info("Running in test mode - executing immediately")
        new_jobs = monitor.run_monitoring_cycle()
        print(f"\nTest run completed! Found {len(new_jobs)} new jobs.")
        
        if new_jobs:
            print("\nNew jobs found:")
            for job in new_jobs:
                print(f"- {job['title']} at {job['company']}")
        else:
            print("\nNo new jobs found.")
            
    else:
        # Schedule daily runs with proper timezone handling
        schedule_time = monitor.config.get('schedule_time', '09:00')
        logger.info(f"Scheduling daily job monitoring at {schedule_time} ({args.timezone})")
        
        # Schedule the monitoring cycle
        schedule.every().day.at(schedule_time).do(monitor.run_monitoring_cycle)
        
        # Also run once immediately
        logger.info("Running initial monitoring cycle")
        monitor.run_monitoring_cycle()
        
        current_time = get_poland_time()
        print(f"Enhanced Job Monitor started!")
        print(f"Current time in Poland: {current_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print(f"Will run daily at {schedule_time} ({args.timezone})")
        print("Press Ctrl+C to stop")
        
        # Keep the script running
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            logger.info("Job monitor stopped by user")
            print("\nJob monitor stopped.")

if __name__ == "__main__":
    main()
