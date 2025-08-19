#!/usr/bin/env python3
"""
Minimal web server for Railway health checks
"""

import os
import sys
from flask import Flask, jsonify

# Create Flask app
app = Flask(__name__)

@app.route('/')
def home():
    """Simple home endpoint"""
    return jsonify({
        'status': 'running',
        'service': 'job-monitor',
        'message': 'Service is running'
    })

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'job-monitor'
    })

@app.route('/ping')
def ping():
    """Simple ping endpoint"""
    return jsonify({'pong': True})

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8000))
    print(f"Starting simple web server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
