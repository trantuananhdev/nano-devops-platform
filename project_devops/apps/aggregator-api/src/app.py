#!/usr/bin/env python3
"""
Aggregator API Service
HTTP API that aggregates data from other services (health-api, data-api)
Demonstrates service-to-service communication patterns
"""

from flask import Flask, jsonify, request
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST, Counter, Histogram
import requests
import os
import time
import sys

app = Flask(__name__)

# Service endpoints configuration
HEALTH_API_URL = os.getenv('HEALTH_API_URL', 'http://health-api:8080')
DATA_API_URL = os.getenv('DATA_API_URL', 'http://data-api:8080')

# Request timeout for service calls
SERVICE_TIMEOUT = float(os.getenv('SERVICE_TIMEOUT', '5.0'))

# Prometheus metrics
request_count = Counter('aggregator_api_requests_total', 'Total number of requests', ['method', 'endpoint'])
request_duration = Histogram('aggregator_api_request_duration_seconds', 'Request duration in seconds', ['method', 'endpoint'])
service_call_count = Counter('aggregator_api_service_calls_total', 'Total service calls', ['target_service', 'status'])
service_call_duration = Histogram('aggregator_api_service_call_duration_seconds', 'Service call duration', ['target_service'])

def call_service(url, endpoint, timeout=SERVICE_TIMEOUT):
    """Call an external service endpoint"""
    try:
        start_time = time.time()
        response = requests.get(f"{url}{endpoint}", timeout=timeout)
        duration = time.time() - start_time
        
        service_call_duration.labels(target_service=url.split('://')[1].split(':')[0]).observe(duration)
        service_call_count.labels(target_service=url.split('://')[1].split(':')[0], status=str(response.status_code)).inc()
        
        if response.status_code == 200:
            return {'success': True, 'data': response.json(), 'status_code': response.status_code}
        else:
            return {'success': False, 'error': f'HTTP {response.status_code}', 'status_code': response.status_code}
    except requests.exceptions.Timeout:
        service_call_count.labels(target_service=url.split('://')[1].split(':')[0], status='timeout').inc()
        return {'success': False, 'error': 'Service call timeout'}
    except requests.exceptions.ConnectionError:
        service_call_count.labels(target_service=url.split('://')[1].split(':')[0], status='connection_error').inc()
        return {'success': False, 'error': 'Service connection error'}
    except Exception as e:
        service_call_count.labels(target_service=url.split('://')[1].split(':')[0], status='error').inc()
        app.logger.error(f"Service call error: {e}")
        return {'success': False, 'error': str(e)}

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint - checks downstream services"""
    health_status = {
        'status': 'healthy',
        'service': 'aggregator-api',
        'version': '1.0.0',
        'downstream_services': {}
    }
    
    # Check health-api
    health_api_result = call_service(HEALTH_API_URL, '/health', timeout=2.0)
    health_status['downstream_services']['health-api'] = {
        'available': health_api_result['success'],
        'status': health_api_result.get('status_code', 'unknown')
    }
    
    # Check data-api
    data_api_result = call_service(DATA_API_URL, '/health', timeout=2.0)
    health_status['downstream_services']['data-api'] = {
        'available': data_api_result['success'],
        'status': data_api_result.get('status_code', 'unknown')
    }
    
    # Determine overall health
    all_healthy = all(
        svc['available'] for svc in health_status['downstream_services'].values()
    )
    
    status_code = 200 if all_healthy else 503
    health_status['status'] = 'healthy' if all_healthy else 'degraded'
    
    return jsonify(health_status), status_code

@app.route('/metrics', methods=['GET'])
def metrics():
    """Prometheus metrics endpoint"""
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

@app.route('/', methods=['GET'])
def root():
    """Root endpoint"""
    return jsonify({
        'message': 'Aggregator API Service',
        'version': '1.0.0',
        'endpoints': ['/health', '/metrics', '/aggregate/status', '/aggregate/data/<key>']
    }), 200

@app.route('/aggregate/status', methods=['GET'])
def aggregate_status():
    """Aggregate status from all services"""
    result = {
        'timestamp': time.time(),
        'services': {}
    }
    
    # Get health-api status
    health_api_result = call_service(HEALTH_API_URL, '/health')
    result['services']['health-api'] = health_api_result
    
    # Get data-api status
    data_api_result = call_service(DATA_API_URL, '/health')
    result['services']['data-api'] = data_api_result
    
    # Determine overall status
    all_available = all(
        svc.get('success', False) for svc in result['services'].values()
    )
    
    result['overall_status'] = 'all_available' if all_available else 'degraded'
    
    return jsonify(result), 200

@app.route('/aggregate/data/<key>', methods=['GET'])
def aggregate_data(key):
    """Get data from data-api and include service status"""
    result = {
        'timestamp': time.time(),
        'data': None,
        'service_status': {}
    }
    
    # Get data from data-api
    data_result = call_service(DATA_API_URL, f'/data/{key}')
    result['data'] = data_result
    
    # Get health-api status for context
    health_result = call_service(HEALTH_API_URL, '/health')
    result['service_status']['health-api'] = health_result
    
    if data_result.get('success'):
        return jsonify(result), 200
    else:
        return jsonify(result), 404 if data_result.get('status_code') == 404 else 503

@app.before_request
def before_request():
    """Track request start time"""
    request.start_time = time.time()

@app.after_request
def after_request(response):
    """Track request metrics"""
    request_count.labels(method=request.method, endpoint=request.endpoint or 'unknown').inc()
    duration = time.time() - request.start_time
    request_duration.labels(method=request.method, endpoint=request.endpoint or 'unknown').observe(duration)
    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)
