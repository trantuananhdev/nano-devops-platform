#!/usr/bin/env python3
"""
User API Service
Business logic, user registration, validation, profile management
"""

from flask import Flask, jsonify, request
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST, Counter, Histogram
import psycopg2
import os
import time
import hashlib
import re

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
request_count = Counter('user_api_requests_total', 'Total number of requests', ['method', 'endpoint'])
request_duration = Histogram('user_api_request_duration_seconds', 'Request duration in seconds', ['method', 'endpoint'])
db_errors = Counter('user_api_db_errors_total', 'Total database errors', ['operation'])
user_registrations = Counter('user_api_registrations_total', 'Total user registrations', ['status'])

def get_db_connection():
    """Get database connection"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        app.logger.error(f"Database connection error: {e}")
        db_errors.labels(operation='connect').inc()
        return None

def validate_email(email):
    """Simple email validation"""
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

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
        'service': 'user-api',
        'version': '1.0.0',
        'database': db_status
    }), status_code

@app.route('/metrics', methods=['GET'])
def metrics():
    """Prometheus metrics endpoint"""
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

@app.route('/users/register', methods=['POST'])
def register():
    """Register a new user"""
    start_time = time.time()
    request_count.labels(method='POST', endpoint='/users/register').inc()
    
    data = request.json
    if not data or not all(k in data for k in ('username', 'email', 'password')):
        user_registrations.labels(status='validation_error').inc()
        return jsonify({'error': 'missing required fields'}), 400
    
    if not validate_email(data['email']):
        user_registrations.labels(status='invalid_email').inc()
        return jsonify({'error': 'invalid email format'}), 400
    
    if len(data['password']) < 8:
        user_registrations.labels(status='weak_password').inc()
        return jsonify({'error': 'password too short'}), 400
    
    # Simple hashing (use better library in real prod)
    password_hash = hashlib.sha256(data['password'].encode()).hexdigest()
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'database connection failed'}), 500
    
    try:
        cur = conn.cursor()
        # Check if username/email already exists
        cur.execute("SELECT 1 FROM users WHERE username = %s OR email = %s", (data['username'], data['email']))
        if cur.fetchone():
            cur.close()
            conn.close()
            user_registrations.labels(status='duplicate_user').inc()
            return jsonify({'error': 'username or email already exists'}), 409
        
        # Insert user
        cur.execute("INSERT INTO users (username, email, password_hash, full_name) VALUES (%s, %s, %s, %s) RETURNING id",
                    (data['username'], data['email'], password_hash, data.get('full_name')))
        user_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        
        user_registrations.labels(status='success').inc()
        request_duration.labels(method='POST', endpoint='/users/register').observe(time.time() - start_time)
        return jsonify({'id': user_id, 'username': data['username'], 'status': 'registered'}), 201
    except Exception as e:
        app.logger.error(f"Error registering user: {e}")
        db_errors.labels(operation='insert').inc()
        return jsonify({'error': 'internal database error'}), 500

@app.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """Get user profile by ID"""
    start_time = time.time()
    request_count.labels(method='GET', endpoint='/users/id').inc()
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'database connection failed'}), 500
    
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, username, email, full_name, created_at, is_active FROM users WHERE id = %s", (user_id,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        
        if row:
            request_duration.labels(method='GET', endpoint='/users/id').observe(time.time() - start_time)
            return jsonify({
                'id': row[0],
                'username': row[1],
                'email': row[2],
                'full_name': row[3],
                'created_at': row[4].isoformat(),
                'is_active': row[5]
            }), 200
        else:
            return jsonify({'error': 'user not found'}), 404
    except Exception as e:
        app.logger.error(f"Error fetching user: {e}")
        db_errors.labels(operation='select').inc()
        return jsonify({'error': 'internal database error'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
