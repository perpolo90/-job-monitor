#!/usr/bin/env python3
"""
Basic HTTP server for Railway health checks using Python's built-in server
"""

import os
import json
from http.server import HTTPServer, BaseHTTPRequestHandler

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {
                'status': 'healthy',
                'service': 'job-monitor',
                'message': 'Service is running'
            }
            self.wfile.write(json.dumps(response).encode())
        elif self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {
                'status': 'running',
                'service': 'job-monitor',
                'message': 'Service is running'
            }
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {'error': 'Not found'}
            self.wfile.write(json.dumps(response).encode())
    
    def log_message(self, format, *args):
        """Override to use print instead of stderr"""
        print(f"[{self.log_date_time_string()}] {format % args}")

def run_server():
    """Run the HTTP server"""
    port = int(os.getenv('PORT', 8000))
    server_address = ('', port)
    httpd = HTTPServer(server_address, HealthCheckHandler)
    print(f"Starting basic HTTP server on port {port}")
    print(f"Health check available at: http://localhost:{port}/health")
    httpd.serve_forever()

if __name__ == '__main__':
    run_server()
