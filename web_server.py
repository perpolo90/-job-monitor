#!/usr/bin/env python3
"""
Simple web server with health check endpoint for Railway deployment
"""

import os
import sys
import logging
import traceback
from flask import Flask, jsonify
from datetime import datetime
import pytz

# Configure logging for Railway - more verbose startup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Log to stdout for Railway
        logging.FileHandler('web_server.log')  # Also log to file
    ]
)

logger = logging.getLogger(__name__)

# Create Flask app with error handling
try:
    app = Flask(__name__)
    logger.info("Flask app created successfully")
except Exception as e:
    logger.error(f"Failed to create Flask app: {e}")
    sys.exit(1)

@app.route('/health')
def health_check():
    """Health check endpoint for Railway"""
    try:
        logger.info("Health check endpoint called")
        
        # Get current time in Poland timezone
        timezone_str = os.getenv('TIMEZONE', 'Europe/Warsaw')
        tz = pytz.timezone(timezone_str)
        current_time = datetime.now(tz)
        
        response_data = {
            'status': 'healthy',
            'timestamp': current_time.isoformat(),
            'timezone': timezone_str,
            'service': 'job-monitor',
            'version': '2.0.0',
            'port': os.getenv('PORT', '8000')
        }
        
        logger.info(f"Health check successful: {response_data}")
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@app.route('/')
def home():
    """Home endpoint"""
    try:
        logger.info("Home endpoint called")
        return jsonify({
            'service': 'Job Monitor',
            'version': '2.0.0',
            'description': 'Automated job monitoring system for fintech and AI companies',
            'endpoints': {
                'health': '/health',
                'home': '/',
                'status': '/status'
            },
            'status': 'running'
        }), 200
    except Exception as e:
        logger.error(f"Home endpoint failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/status')
def status():
    """Status endpoint showing current configuration"""
    try:
        logger.info("Status endpoint called")
        
        # Check environment variables
        env_vars = {
            'timezone': os.getenv('TIMEZONE', 'Europe/Warsaw'),
            'schedule_time': os.getenv('SCHEDULE_TIME', '09:00'),
            'log_level': os.getenv('LOG_LEVEL', 'INFO'),
            'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
            'sender_email': os.getenv('SENDER_EMAIL', 'not-set'),
            'recipient_email': os.getenv('RECIPIENT_EMAIL', 'not-set'),
            'database_url': os.getenv('DATABASE_URL', 'jobs.db'),
            'port': os.getenv('PORT', '8000')
        }
        
        # Check if required variables are set
        missing_vars = []
        for var in ['SENDER_EMAIL', 'SENDER_PASSWORD', 'RECIPIENT_EMAIL']:
            if not os.getenv(var):
                missing_vars.append(var)
        
        status_info = {
            'environment': env_vars,
            'missing_variables': missing_vars,
            'config_loaded': len(missing_vars) == 0
        }
        
        logger.info(f"Status check successful: {status_info}")
        return jsonify(status_info), 200
        
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/ready')
def ready():
    """Readiness probe endpoint"""
    try:
        logger.info("Readiness probe called")
        
        # Check if all required environment variables are set
        required_vars = ['SENDER_EMAIL', 'SENDER_PASSWORD', 'RECIPIENT_EMAIL']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            logger.warning(f"Missing required environment variables: {missing_vars}")
            return jsonify({
                'ready': False,
                'missing_variables': missing_vars,
                'message': 'Missing required environment variables'
            }), 503
        else:
            logger.info("Service is ready")
            return jsonify({
                'ready': True,
                'message': 'Service is ready to handle requests'
            }), 200
            
    except Exception as e:
        logger.error(f"Readiness probe failed: {e}")
        return jsonify({
            'ready': False,
            'error': str(e)
        }), 500

def run_server():
    """Run the Flask server with enhanced error handling"""
    try:
        # Get port from environment
        port = int(os.getenv('PORT', 8000))
        debug = os.getenv('LOG_LEVEL', 'INFO').upper() == 'DEBUG'
        
        logger.info(f"Starting web server on port {port}")
        logger.info(f"Debug mode: {debug}")
        logger.info(f"Environment variables: PORT={port}, LOG_LEVEL={os.getenv('LOG_LEVEL')}")
        
        # Log all environment variables for debugging
        logger.info("Environment variables:")
        for key, value in os.environ.items():
            if 'PASSWORD' not in key.upper():  # Don't log passwords
                logger.info(f"  {key}: {value}")
        
        # Start the server
        app.run(
            host='0.0.0.0',  # Bind to all interfaces
            port=port,
            debug=debug,
            use_reloader=False  # Disable reloader for production
        )
        
    except Exception as e:
        logger.error(f"Failed to start web server: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == '__main__':
    logger.info("Web server starting...")
    run_server()
