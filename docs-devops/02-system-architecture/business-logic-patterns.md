# Business Logic Patterns

This document describes the patterns for implementing business logic in the Nano DevOps Platform services.

---

## Overview

Business logic patterns ensure consistent implementation of validation, business rules, error handling, and data persistence across services.

---

## Core Patterns

### 1. Input Validation Pattern

**When to use**: When accepting user input or external data

**Implementation**:

```python
# Define validation functions
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

# Use in endpoint
@app.route('/users/register', methods=['POST'])
def register_user():
    data = request.get_json()
    username = data.get('username')
    
    # Validate
    username_valid, username_error = validate_username(username)
    if not username_valid:
        validation_errors.labels(field='username', rule='format').inc()
        return jsonify({'error': username_error}), 400
```

**Best Practices**:
- Validate all required fields first
- Return clear, user-friendly error messages
- Track validation errors in metrics
- Use consistent validation functions across services

---

### 2. Business Rules Pattern

**When to use**: When enforcing business constraints

**Implementation**:

```python
# Define business rules as constants
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128
MIN_USERNAME_LENGTH = 3
MAX_USERNAME_LENGTH = 50
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

# Apply business rules
def validate_password(password):
    """Validate password against business rules"""
    if not password or not isinstance(password, str):
        return False, "Password is required"
    
    if len(password) < MIN_PASSWORD_LENGTH:
        return False, f"Password must be at least {MIN_PASSWORD_LENGTH} characters"
    
    if len(password) > MAX_PASSWORD_LENGTH:
        return False, f"Password must be at most {MAX_PASSWORD_LENGTH} characters"
    
    return True, None
```

**Best Practices**:
- Define business rules as constants at module level
- Make rules configurable via environment variables if needed
- Document business rules in service documentation
- Apply rules consistently across all endpoints

---

### 3. Uniqueness Validation Pattern

**When to use**: When enforcing unique constraints (username, email, etc.)

**Implementation**:

```python
# Check uniqueness before insert
conn = get_db_connection()
cur = conn.cursor()

# Check username uniqueness
cur.execute("SELECT id FROM users WHERE username = %s", (username,))
if cur.fetchone():
    cur.close()
    conn.close()
    validation_errors.labels(field='username', rule='unique').inc()
    return jsonify({'error': 'Username already exists'}), 409

# Check email uniqueness
cur.execute("SELECT id FROM users WHERE email = %s", (email,))
if cur.fetchone():
    cur.close()
    conn.close()
    validation_errors.labels(field='email', rule='unique').inc()
    return jsonify({'error': 'Email already exists'}), 409

# Proceed with insert
cur.execute("INSERT INTO users ...")
```

**Best Practices**:
- Check uniqueness before attempting insert
- Use database constraints as backup (UNIQUE constraints)
- Return 409 Conflict for duplicate violations
- Track uniqueness violations in metrics

---

### 4. Error Handling Pattern

**When to use**: When handling database operations and business logic errors

**Implementation**:

```python
try:
    # Business logic operation
    cur.execute("INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
                (username, email, password_hash))
    conn.commit()
    cur.close()
    conn.close()
    
    return jsonify({'message': 'User registered successfully'}), 201

except psycopg2.IntegrityError as e:
    # Handle business rule violations (e.g., duplicate)
    app.logger.error(f"Database integrity error: {e}")
    db_errors.labels(operation='register').inc()
    if conn:
        conn.close()
    return jsonify({'error': 'User already exists'}), 409

except Exception as e:
    # Handle unexpected errors
    app.logger.error(f"Register user error: {e}")
    db_errors.labels(operation='register').inc()
    if conn:
        conn.close()
    return jsonify({'error': 'Database error'}), 500
```

**Best Practices**:
- Handle specific exceptions (IntegrityError, etc.)
- Log errors with context
- Track errors in metrics
- Return appropriate HTTP status codes
- Always close database connections in finally blocks

---

### 5. Data Transformation Pattern

**When to use**: When transforming data before storage or response

**Implementation**:

```python
# Hash passwords before storage
def hash_password(password):
    """Hash password using SHA-256 (simple hashing for demo purposes)"""
    return hashlib.sha256(password.encode()).hexdigest()

# Normalize email (lowercase)
email = email.lower()

# Transform data for response
return jsonify({
    'id': user[0],
    'username': user[1],
    'email': user[2],
    'created_at': user[4].isoformat() if user[4] else None,
    'is_active': user[6]
}), 200
```

**Best Practices**:
- Never store sensitive data in plaintext
- Normalize data consistently (e.g., lowercase emails)
- Transform timestamps to ISO format for API responses
- Document data transformations

---

### 6. Metrics Tracking Pattern

**When to use**: When tracking business logic operations

**Implementation**:

```python
# Define metrics
validation_errors = Counter('user_api_validation_errors_total', 'Total validation errors', ['field', 'rule'])
db_errors = Counter('user_api_db_errors_total', 'Total database errors', ['operation'])

# Track validation errors
if not username_valid:
    validation_errors.labels(field='username', rule='format').inc()
    return jsonify({'error': username_error}), 400

# Track database errors
except Exception as e:
    db_errors.labels(operation='register').inc()
    return jsonify({'error': 'Database error'}), 500
```

**Best Practices**:
- Track all validation errors with field and rule labels
- Track database errors with operation labels
- Use consistent metric naming across services
- Include metrics in Grafana dashboards

---

## HTTP Status Codes

Use appropriate HTTP status codes for business logic responses:

- **200 OK**: Successful GET, PUT, PATCH operations
- **201 Created**: Successful POST operations (resource created)
- **400 Bad Request**: Validation errors, invalid input format
- **404 Not Found**: Resource not found
- **409 Conflict**: Business rule violations (duplicates, conflicts)
- **500 Internal Server Error**: Unexpected server errors
- **503 Service Unavailable**: Database connection failures

---

## Example: Complete User Registration Flow

```python
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
    
    # Validate required fields
    if not username:
        validation_errors.labels(field='username', rule='required').inc()
        return jsonify({'error': 'Username is required'}), 400
    
    # Validate format
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
    
    # Check uniqueness
    conn = get_db_connection()
    if conn is None:
        return jsonify({'error': 'Database connection failed'}), 503
    
    try:
        cur = conn.cursor()
        
        # Check username uniqueness
        cur.execute("SELECT id FROM users WHERE username = %s", (username,))
        if cur.fetchone():
            validation_errors.labels(field='username', rule='unique').inc()
            return jsonify({'error': 'Username already exists'}), 409
        
        # Check email uniqueness
        cur.execute("SELECT id FROM users WHERE email = %s", (email,))
        if cur.fetchone():
            validation_errors.labels(field='email', rule='unique').inc()
            return jsonify({'error': 'Email already exists'}), 409
        
        # Create user
        password_hash = hash_password(password)
        cur.execute("""
            INSERT INTO users (username, email, password_hash)
            VALUES (%s, %s, %s)
            RETURNING id, username, email, created_at, is_active
        """, (username, email.lower(), password_hash))
        
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
                'created_at': user[3].isoformat() if user[3] else None,
                'is_active': user[4]
            }
        }), 201
    
    except psycopg2.IntegrityError:
        db_errors.labels(operation='register').inc()
        return jsonify({'error': 'User already exists'}), 409
    except Exception as e:
        app.logger.error(f"Register user error: {e}")
        db_errors.labels(operation='register').inc()
        return jsonify({'error': 'Database error'}), 500
```

---

## Anti-Patterns to Avoid

❌ **No validation** - Always validate input  
❌ **Storing sensitive data in plaintext** - Always hash passwords  
❌ **Generic error messages** - Provide specific, actionable error messages  
❌ **No metrics tracking** - Track validation errors and business logic failures  
❌ **Ignoring database constraints** - Use database constraints as backup  
❌ **Not handling edge cases** - Handle all validation scenarios  

---

## Future Enhancements

- **Input sanitization** - Sanitize input to prevent injection attacks
- **Rate limiting** - Implement rate limiting for registration endpoints
- **Password strength validation** - Add password complexity requirements
- **Email verification** - Add email verification workflow
- **Audit logging** - Log all business logic operations for audit

---

**Pattern Established By**: user-api service (Phase 2 Task 3)  
**Last Updated**: 2026-03-01
