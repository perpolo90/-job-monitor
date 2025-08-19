#!/usr/bin/env python3
"""
Web-only version for Railway testing
"""

import os
import sys
import logging
from web_server import run_server

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('web_only.log')
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Main function for web-only mode"""
    logger.info("Starting web-only mode for Railway testing")
    logger.info(f"PORT: {os.getenv('PORT', '8000')}")
    logger.info(f"TIMEZONE: {os.getenv('TIMEZONE', 'Europe/Warsaw')}")
    
    # Check environment variables
    required_vars = ['SENDER_EMAIL', 'SENDER_PASSWORD', 'RECIPIENT_EMAIL']
    for var in required_vars:
        value = os.getenv(var)
        if value:
            logger.info(f"{var}: [SET]")
        else:
            logger.warning(f"{var}: [NOT SET]")
    
    # Start web server
    run_server()

if __name__ == "__main__":
    main()
