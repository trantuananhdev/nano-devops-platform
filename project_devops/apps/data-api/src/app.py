#!/usr/bin/env python3
"""
Data API Service
PostgreSQL integration for data operations
"""

from flask import Flask, jsonify, request
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST, Counter, Histogram
import psycopg2
import os
import time

app = Flask(__name__)

# Database connection configuration
def get_db_password():
    """Get database password from environment variable or Docker secret file"""
    password_file = os.getenv('POSTGRES_PASSWORD_FILE', '/run/secrets/postgres_password')
    if os.path.exists(password_file):
        with open(password_file, 'r') as f:
            return f.read().strip()
    return os.getenv('POSTGRES_PASSWORD', 'platform_password')

DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'platform-postgres'),
    'port': os.getenv('POSTGRES_PORT', '5432'),
    'database': os.getenv('POSTGRES_DB', 'platform_db'),
    'user': os.getenv('POSTGRES_USER', 'platform_user'),
    'password': get_db_password()
}

# Prometheus metrics
request_count = Counter('data_api_requests_total', 'Total number of requests', ['method', 'endpoint'])
request_duration = Histogram('data_api_request_duration_seconds', 'Request duration in seconds', ['method', 'endpoint'])
db_errors = Counter('data_api_db_errors_total', 'Total database errors', ['operation'])

def get_db_connection():
    """Get database connection"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        app.logger.error(f"Database connection error: {e}")
        db_errors.labels(operation='connect').inc()
        return None

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint - verifies database connectivity"""
    db_status = 'unknown'
    try:
        conn = get_db_connection()
        if conn:
            cur = conn.cursor()
            cur.execute("SELECT 1")
            cur.close()
            conn.close()
            db_status = 'connected'
        else:
            db_status = 'disconnected'
    except Exception as e:
        app.logger.error(f"Health check database error: {e}")
        db_status = 'error'
    
    status_code = 200 if db_status == 'connected' else 503
    return jsonify({
        'status': 'healthy' if db_status == 'connected' else 'unhealthy',
        'service': 'data-api',
        'version': '1.0.0',
        'database': db_status
    }), status_code

@app.route('/metrics', methods=['GET'])
def metrics():
    """Prometheus metrics endpoint"""
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

@app.route('/data/<key>', methods=['GET'])
def get_data(key):
    """Get data by key"""
    start_time = time.time()
    request_count.labels(method='GET', endpoint='/data').inc()
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'database connection failed'}), 500
    
    try:
        cur = conn.cursor()
        cur.execute("SELECT value FROM data_store WHERE key = %s", (key,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        
        if row:
            request_duration.labels(method='GET', endpoint='/data').observe(time.time() - start_time)
            return jsonify({'key': key, 'value': row[0]}), 200
        else:
            return jsonify({'error': 'key not found'}), 404
    except Exception as e:
        app.logger.error(f"Error fetching data: {e}")
        db_errors.labels(operation='select').inc()
        return jsonify({'error': 'internal database error'}), 500

@app.route('/data', methods=['POST'])
def store_data():
    """Store data"""
    start_time = time.time()
    request_count.labels(method='POST', endpoint='/data').inc()
    
    data = request.json
    if not data or 'key' not in data or 'value' not in data:
        return jsonify({'error': 'missing key or value'}), 400
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'database connection failed'}), 500
    
    try:
        cur = conn.cursor()
        cur.execute("INSERT INTO data_store (key, value) VALUES (%s, %s) ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value", 
                    (data['key'], data['value']))
        conn.commit()
        cur.close()
        conn.close()
        
        request_duration.labels(method='POST', endpoint='/data').observe(time.time() - start_time)
        return jsonify({'status': 'success'}), 201
    except Exception as e:
        app.logger.error(f"Error storing data: {e}")
        db_errors.labels(operation='insert').inc()
        return jsonify({'error': 'internal database error'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
