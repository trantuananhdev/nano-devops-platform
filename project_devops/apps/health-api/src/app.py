#!/usr/bin/env python3
"""
Health API Service
Minimal HTTP API for health checks and metrics
"""

from flask import Flask, jsonify
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST, Counter, Histogram
import time

app = Flask(__name__)

# Prometheus metrics
request_count = Counter('health_api_requests_total', 'Total number of requests', ['method', 'endpoint'])
request_duration = Histogram('health_api_request_duration_seconds', 'Request duration in seconds', ['method', 'endpoint'])

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'health-api',
        'version': '1.0.0'
    }), 200

@app.route('/metrics', methods=['GET'])
def metrics():
    """Prometheus metrics endpoint"""
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

@app.route('/', methods=['GET'])
def root():
    """Root endpoint"""
    return jsonify({
        'message': 'Health API Service',
        'version': '1.0.0',
        'endpoints': ['/health', '/metrics']
    }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
