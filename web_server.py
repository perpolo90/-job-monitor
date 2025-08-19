#!/usr/bin/env python3
"""
Simple web server with health check endpoint for Railway deployment
"""

import os
import logging
from flask import Flask, jsonify
from datetime import datetime
import pytz

# Configure logging for Railway
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Log to stdout for Railway
        logging.FileHandler('job_monitor.log')  # Also log to file
    ]
)

app = Flask(__name__)
logger = logging.getLogger(__name__)

@app.route('/health')
def health_check():
    """Health check endpoint for Railway"""
    try:
        # Get current time in Poland timezone
        timezone_str = os.getenv('TIMEZONE', 'Europe/Warsaw')
        tz = pytz.timezone(timezone_str)
        current_time = datetime.now(tz)
        
        return jsonify({
            'status': 'healthy',
            'timestamp': current_time.isoformat(),
            'timezone': timezone_str,
            'service': 'job-monitor',
            'version': '2.0.0'
        }), 200
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@app.route('/')
def home():
    """Home endpoint"""
    return jsonify({
        'service': 'Job Monitor',
        'version': '2.0.0',
        'description': 'Automated job monitoring system for fintech and AI companies',
        'endpoints': {
            'health': '/health',
            'home': '/'
        }
    }), 200

@app.route('/status')
def status():
    """Status endpoint showing current configuration"""
    try:
        return jsonify({
            'timezone': os.getenv('TIMEZONE', 'Europe/Warsaw'),
            'schedule_time': os.getenv('SCHEDULE_TIME', '09:00'),
            'log_level': os.getenv('LOG_LEVEL', 'INFO'),
            'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
            'sender_email': os.getenv('SENDER_EMAIL', 'not-set'),
            'recipient_email': os.getenv('RECIPIENT_EMAIL', 'not-set'),
            'database_url': os.getenv('DATABASE_URL', 'jobs.db')
        }), 200
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        return jsonify({'error': str(e)}), 500

def run_server():
    """Run the Flask server"""
    port = int(os.getenv('PORT', 8000))
    debug = os.getenv('LOG_LEVEL', 'INFO').upper() == 'DEBUG'
    
    logger.info(f"Starting web server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)

if __name__ == '__main__':
    run_server()
