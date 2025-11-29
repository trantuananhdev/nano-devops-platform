#!/usr/bin/env python3
"""
Aggregator API Service
Service-to-service communication, calls health-api and data-api
"""

from flask import Flask, jsonify
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST, Counter, Histogram
import requests
import os
import time

app = Flask(__name__)

# Service URLs from environment variables
HEALTH_API_URL = os.getenv('HEALTH_API_URL', 'http://health-api:8080')
DATA_API_URL = os.getenv('DATA_API_URL', 'http://data-api:8080')

# Prometheus metrics
request_count = Counter('aggregator_api_requests_total', 'Total number of requests', ['method', 'endpoint'])
request_duration = Histogram('aggregator_api_request_duration_seconds', 'Request duration in seconds', ['method', 'endpoint'])
service_calls = Counter('aggregator_api_service_calls_total', 'Total service-to-service calls', ['service', 'status'])

def call_service(url, endpoint, method='GET', timeout=5):
    """Helper to call downstream services"""
    try:
        response = requests.request(method, f"{url}{endpoint}", timeout=timeout)
        service_calls.labels(service=url.split('://')[1].split(':')[0], status=response.status_code).inc()
        return {
            'success': response.status_code < 400,
            'status_code': response.status_code,
            'data': response.json() if response.status_code < 400 else None
        }
    except Exception as e:
        app.logger.error(f"Error calling {url}{endpoint}: {e}")
        service_calls.labels(service=url.split('://')[1].split(':')[0], status='error').inc()
        return {'success': False, 'status_code': 500, 'error': str(e)}

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint - verifies downstream services"""
    health_api_result = call_service(HEALTH_API_URL, '/health')
    data_api_result = call_service(DATA_API_URL, '/health')
    
    all_healthy = health_api_result['success'] and data_api_result['success']
    
    return jsonify({
        'status': 'healthy' if all_healthy else 'degraded',
        'service': 'aggregator-api',
        'version': '1.0.0',
        'downstream_services': {
            'health-api': {'available': health_api_result['success']},
            'data-api': {'available': data_api_result['success']}
        }
    }), 200 if all_healthy else 200 # We return 200 even if degraded for now

@app.route('/metrics', methods=['GET'])
def metrics():
    """Prometheus metrics endpoint"""
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

@app.route('/aggregate/status', methods=['GET'])
def aggregate_status():
    """Aggregate status from all services"""
    start_time = time.time()
    request_count.labels(method='GET', endpoint='/aggregate/status').inc()
    
    health_api_result = call_service(HEALTH_API_URL, '/health')
    data_api_result = call_service(DATA_API_URL, '/health')
    
    request_duration.labels(method='GET', endpoint='/aggregate/status').observe(time.time() - start_time)
    
    return jsonify({
        'overall_status': 'healthy' if (health_api_result['success'] and data_api_result['success']) else 'degraded',
        'services': {
            'health-api': health_api_result['data'] if health_api_result['success'] else {'status': 'unavailable'},
            'data-api': data_api_result['data'] if data_api_result['success'] else {'status': 'unavailable'}
        }
    }), 200

@app.route('/aggregate/data/<key>', methods=['GET'])
def aggregate_data(key):
    """Aggregate data from data-api"""
    start_time = time.time()
    request_count.labels(method='GET', endpoint='/aggregate/data').inc()
    
    data_api_result = call_service(DATA_API_URL, f'/data/{key}')
    
    request_duration.labels(method='GET', endpoint='/aggregate/data').observe(time.time() - start_time)
    
    if data_api_result['success']:
        return jsonify({
            'data': data_api_result['data'],
            'service_status': 'ok'
        }), 200
    else:
        return jsonify({
            'error': 'could not fetch data',
            'service_status': 'unavailable',
            'status_code': data_api_result['status_code']
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
