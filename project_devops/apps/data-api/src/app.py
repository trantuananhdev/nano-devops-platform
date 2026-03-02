#!/usr/bin/env python3
"""
Data API Service
Simple HTTP API for storing and retrieving key-value data using PostgreSQL
Demonstrates infrastructure integration (PostgreSQL) and multi-service deployment
"""

from flask import Flask, jsonify, request
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST, Counter, Histogram
import psycopg2
import os
import time
import sys

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

def init_db():
    """Initialize database schema"""
    conn = get_db_connection()
    if conn is None:
        app.logger.error("Failed to initialize database - connection failed")
        return False
    
    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS data_store (
                key VARCHAR(255) PRIMARY KEY,
                value TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        cur.close()
        conn.close()
        app.logger.info("Database schema initialized successfully")
        return True
    except Exception as e:
        app.logger.error(f"Database initialization error: {e}")
        db_errors.labels(operation='init').inc()
        if conn:
            conn.close()
        return False

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

@app.route('/', methods=['GET'])
def root():
    """Root endpoint"""
    return jsonify({
        'message': 'Data API Service',
        'version': '1.0.0',
        'endpoints': ['/health', '/metrics', '/data', '/data/<key>']
    }), 200

@app.route('/data/<key>', methods=['GET'])
def get_data(key):
    """Get data by key"""
    conn = get_db_connection()
    if conn is None:
        return jsonify({'error': 'Database connection failed'}), 503
    
    try:
        cur = conn.cursor()
        cur.execute("SELECT key, value, created_at, updated_at FROM data_store WHERE key = %s", (key,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        
        if row:
            return jsonify({
                'key': row[0],
                'value': row[1],
                'created_at': row[2].isoformat() if row[2] else None,
                'updated_at': row[3].isoformat() if row[3] else None
            }), 200
        else:
            return jsonify({'error': 'Key not found'}), 404
    except Exception as e:
        app.logger.error(f"Get data error: {e}")
        db_errors.labels(operation='get').inc()
        if conn:
            conn.close()
        return jsonify({'error': 'Database error'}), 500

@app.route('/data', methods=['POST'])
def set_data():
    """Store or update data"""
    if not request.is_json:
        return jsonify({'error': 'Content-Type must be application/json'}), 400
    
    data = request.get_json()
    if 'key' not in data or 'value' not in data:
        return jsonify({'error': 'Missing required fields: key, value'}), 400
    
    key = data['key']
    value = data['value']
    
    conn = get_db_connection()
    if conn is None:
        return jsonify({'error': 'Database connection failed'}), 503
    
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO data_store (key, value, updated_at)
            VALUES (%s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (key) DO UPDATE
            SET value = EXCLUDED.value, updated_at = CURRENT_TIMESTAMP
        """, (key, value))
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({
            'message': 'Data stored successfully',
            'key': key
        }), 201
    except Exception as e:
        app.logger.error(f"Set data error: {e}")
        db_errors.labels(operation='set').inc()
        if conn:
            conn.close()
        return jsonify({'error': 'Database error'}), 500

@app.route('/data/<key>', methods=['DELETE'])
def delete_data(key):
    """Delete data by key"""
    conn = get_db_connection()
    if conn is None:
        return jsonify({'error': 'Database connection failed'}), 503
    
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM data_store WHERE key = %s", (key,))
        deleted = cur.rowcount
        conn.commit()
        cur.close()
        conn.close()
        
        if deleted > 0:
            return jsonify({'message': 'Data deleted successfully', 'key': key}), 200
        else:
            return jsonify({'error': 'Key not found'}), 404
    except Exception as e:
        app.logger.error(f"Delete data error: {e}")
        db_errors.labels(operation='delete').inc()
        if conn:
            conn.close()
        return jsonify({'error': 'Database error'}), 500

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
    # Initialize database on startup
    if not init_db():
        app.logger.error("Failed to initialize database - service may not function correctly")
        sys.exit(1)
    
    app.run(host='0.0.0.0', port=8080, debug=False)
