#!/usr/bin/env python3
"""
User API Service
HTTP API for user management with business logic (registration, validation, profile management)
Demonstrates real-world business logic patterns: input validation, business rules, error handling
"""

from flask import Flask, jsonify, request
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST, Counter, Histogram
import psycopg2
import os
import time
import sys
import re
import hashlib
from datetime import datetime

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

# Business rules constants
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128
MIN_USERNAME_LENGTH = 3
MAX_USERNAME_LENGTH = 50
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

# Prometheus metrics
request_count = Counter('user_api_requests_total', 'Total number of requests', ['method', 'endpoint'])
request_duration = Histogram('user_api_request_duration_seconds', 'Request duration in seconds', ['method', 'endpoint'])
db_errors = Counter('user_api_db_errors_total', 'Total database errors', ['operation'])
validation_errors = Counter('user_api_validation_errors_total', 'Total validation errors', ['field', 'rule'])

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
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                full_name VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE
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

def hash_password(password):
    """Hash password using SHA-256 (simple hashing for demo purposes)"""
    return hashlib.sha256(password.encode()).hexdigest()

def validate_email(email):
    """Validate email format"""
    if not email or not isinstance(email, str):
        return False
    return bool(EMAIL_REGEX.match(email.strip()))

def validate_password(password):
    """Validate password against business rules"""
    if not password or not isinstance(password, str):
        return False, "Password is required"
    
    if len(password) < MIN_PASSWORD_LENGTH:
        return False, f"Password must be at least {MIN_PASSWORD_LENGTH} characters"
    
    if len(password) > MAX_PASSWORD_LENGTH:
        return False, f"Password must be at most {MAX_PASSWORD_LENGTH} characters"
    
    return True, None

def validate_username(username):
    """Validate username against business rules"""
    if not username or not isinstance(username, str):
        return False, "Username is required"
    
    username = username.strip()
    
    if len(username) < MIN_USERNAME_LENGTH:
        return False, f"Username must be at least {MIN_USERNAME_LENGTH} characters"
    
    if len(username) > MAX_USERNAME_LENGTH:
        return False, f"Username must be at most {MAX_USERNAME_LENGTH} characters"
    
    if not username.isalnum() and '_' not in username and '-' not in username:
        return False, "Username can only contain letters, numbers, underscores, and hyphens"
    
    return True, None

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

@app.route('/', methods=['GET'])
def root():
    """Root endpoint"""
    return jsonify({
        'message': 'User API Service',
        'version': '1.0.0',
        'endpoints': ['/health', '/metrics', '/users', '/users/<id>', '/users/register']
    }), 200

@app.route('/users/register', methods=['POST'])
def register_user():
    """Register a new user with business logic validation"""
    if not request.is_json:
        return jsonify({'error': 'Content-Type must be application/json'}), 400
    
    data = request.get_json()
    
    # Extract fields
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    full_name = data.get('full_name', '')
    
    # Validate required fields
    if not username:
        validation_errors.labels(field='username', rule='required').inc()
        return jsonify({'error': 'Username is required'}), 400
    
    if not email:
        validation_errors.labels(field='email', rule='required').inc()
        return jsonify({'error': 'Email is required'}), 400
    
    if not password:
        validation_errors.labels(field='password', rule='required').inc()
        return jsonify({'error': 'Password is required'}), 400
    
    # Validate username
    username_valid, username_error = validate_username(username)
    if not username_valid:
        validation_errors.labels(field='username', rule='format').inc()
        return jsonify({'error': username_error}), 400
    
    # Validate email
    if not validate_email(email):
        validation_errors.labels(field='email', rule='format').inc()
        return jsonify({'error': 'Invalid email format'}), 400
    
    # Validate password
    password_valid, password_error = validate_password(password)
    if not password_valid:
        validation_errors.labels(field='password', rule='length').inc()
        return jsonify({'error': password_error}), 400
    
    # Check if username or email already exists
    conn = get_db_connection()
    if conn is None:
        return jsonify({'error': 'Database connection failed'}), 503
    
    try:
        cur = conn.cursor()
        
        # Check username
        cur.execute("SELECT id FROM users WHERE username = %s", (username,))
        if cur.fetchone():
            cur.close()
            conn.close()
            validation_errors.labels(field='username', rule='unique').inc()
            return jsonify({'error': 'Username already exists'}), 409
        
        # Check email
        cur.execute("SELECT id FROM users WHERE email = %s", (email,))
        if cur.fetchone():
            cur.close()
            conn.close()
            validation_errors.labels(field='email', rule='unique').inc()
            return jsonify({'error': 'Email already exists'}), 409
        
        # Create user
        password_hash = hash_password(password)
        cur.execute("""
            INSERT INTO users (username, email, password_hash, full_name)
            VALUES (%s, %s, %s, %s)
            RETURNING id, username, email, full_name, created_at, is_active
        """, (username, email.lower(), password_hash, full_name))
        
        user = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({
            'message': 'User registered successfully',
            'user': {
                'id': user[0],
                'username': user[1],
                'email': user[2],
                'full_name': user[3],
                'created_at': user[4].isoformat() if user[4] else None,
                'is_active': user[5]
            }
        }), 201
    
    except psycopg2.IntegrityError as e:
        app.logger.error(f"Database integrity error: {e}")
        db_errors.labels(operation='register').inc()
        if conn:
            conn.close()
        return jsonify({'error': 'User already exists'}), 409
    except Exception as e:
        app.logger.error(f"Register user error: {e}")
        db_errors.labels(operation='register').inc()
        if conn:
            conn.close()
        return jsonify({'error': 'Database error'}), 500

@app.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """Get user by ID"""
    conn = get_db_connection()
    if conn is None:
        return jsonify({'error': 'Database connection failed'}), 503
    
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, username, email, full_name, created_at, updated_at, is_active
            FROM users WHERE id = %s
        """, (user_id,))
        user = cur.fetchone()
        cur.close()
        conn.close()
        
        if user:
            return jsonify({
                'id': user[0],
                'username': user[1],
                'email': user[2],
                'full_name': user[3],
                'created_at': user[4].isoformat() if user[4] else None,
                'updated_at': user[5].isoformat() if user[5] else None,
                'is_active': user[6]
            }), 200
        else:
            return jsonify({'error': 'User not found'}), 404
    except Exception as e:
        app.logger.error(f"Get user error: {e}")
        db_errors.labels(operation='get').inc()
        if conn:
            conn.close()
        return jsonify({'error': 'Database error'}), 500

@app.route('/users', methods=['GET'])
def list_users():
    """List users with pagination"""
    limit = min(int(request.args.get('limit', 10)), 100)  # Max 100 per page
    offset = int(request.args.get('offset', 0))
    
    conn = get_db_connection()
    if conn is None:
        return jsonify({'error': 'Database connection failed'}), 503
    
    try:
        cur = conn.cursor()
        
        # Get total count
        cur.execute("SELECT COUNT(*) FROM users WHERE is_active = TRUE")
        total = cur.fetchone()[0]
        
        # Get users
        cur.execute("""
            SELECT id, username, email, full_name, created_at, updated_at, is_active
            FROM users
            WHERE is_active = TRUE
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """, (limit, offset))
        
        users = []
        for row in cur.fetchall():
            users.append({
                'id': row[0],
                'username': row[1],
                'email': row[2],
                'full_name': row[3],
                'created_at': row[4].isoformat() if row[4] else None,
                'updated_at': row[5].isoformat() if row[5] else None,
                'is_active': row[6]
            })
        
        cur.close()
        conn.close()
        
        return jsonify({
            'users': users,
            'total': total,
            'limit': limit,
            'offset': offset
        }), 200
    except Exception as e:
        app.logger.error(f"List users error: {e}")
        db_errors.labels(operation='list').inc()
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
