# User API Service

HTTP API service for user management with business logic (registration, validation, profile management). Demonstrates real-world business logic patterns: input validation, business rules, error handling, and PostgreSQL integration.

## Purpose

This is the fourth application service added to the platform to:
- Demonstrate real-world business logic patterns
- Implement input validation and business rules
- Show error handling and validation patterns
- Provide a user management service example
- Validate PostgreSQL integration with business logic

## Features

- **Health Endpoint**: `/health` - Returns service health and database connectivity status
- **Metrics Endpoint**: `/metrics` - Prometheus metrics for observability
- **User Registration**: `POST /users/register` - Register new users with validation
- **Get User**: `GET /users/<id>` - Get user by ID
- **List Users**: `GET /users` - List users with pagination
- **Root Endpoint**: `/` - Service information

## Business Logic

### User Registration

The service implements comprehensive business logic for user registration:

#### Validation Rules

1. **Username Validation**:
   - Required field
   - Length: 3-50 characters
   - Allowed characters: letters, numbers, underscores, hyphens
   - Must be unique

2. **Email Validation**:
   - Required field
   - Must match valid email format (RFC 5322 compliant regex)
   - Must be unique
   - Stored in lowercase

3. **Password Validation**:
   - Required field
   - Length: 8-128 characters
   - Stored as SHA-256 hash (simple hashing for demo purposes)

4. **Full Name**:
   - Optional field
   - Maximum 255 characters

#### Business Rules

- Username uniqueness enforced at database level
- Email uniqueness enforced at database level
- Passwords are hashed before storage (never stored in plaintext)
- Users are created as active by default
- Timestamps (created_at, updated_at) are automatically managed

### Error Handling

The service implements proper error handling:

- **400 Bad Request**: Validation errors (invalid format, missing fields, length violations)
- **409 Conflict**: Duplicate username or email
- **404 Not Found**: User not found
- **500 Internal Server Error**: Database errors
- **503 Service Unavailable**: Database connection failures

## Resource Usage

- **Memory**: <100MB RAM (within 6GB constraint)
- **CPU**: Minimal (lightweight Flask application)
- **Storage**: Minimal (Alpine-based Python image)
- **Database**: Uses PostgreSQL for data persistence

## Environment Variables

- `POSTGRES_HOST`: PostgreSQL host (default: `platform-postgres`)
- `POSTGRES_PORT`: PostgreSQL port (default: `5432`)
- `POSTGRES_DB`: Database name (default: `platform_db`)
- `POSTGRES_USER`: Database user (default: `platform_user`)
- `POSTGRES_PASSWORD_FILE`: Path to password file (default: `/run/secrets/postgres_password`)

## Database Schema

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);
```

## Observability

- Exposes Prometheus metrics on `/metrics` endpoint
- Tracks request metrics:
  - `user_api_requests_total` - Request count by method and endpoint
  - `user_api_request_duration_seconds` - Request latency
- Tracks validation errors:
  - `user_api_validation_errors_total` - Validation error count by field and rule
- Tracks database errors:
  - `user_api_db_errors_total` - Database error count by operation
- Integrated with Prometheus scrape configuration
- Health checks configured in docker-compose.yml
- Logs collected by Loki (via Docker logging driver)

## Deployment

The service is deployed via:
1. CI pipeline builds and pushes image to ghcr.io
2. Deployment script (`deploy.sh`) pulls image and deploys
3. Traefik routes traffic to service via `user-api.localhost`

## Monitoring

- **Prometheus Scrape**:
  - Job: `user-api`
  - Target: `user-api:8080`
  - Metrics endpoint: `/metrics`

- **Grafana Dashboard**:
  - Dashboard: `User API` (service-specific)
  - Key panels:
    - Service status (`up{job="user-api"}`)
    - Request rate (`user_api_requests_total`)
    - Request latency (`user_api_request_duration_seconds`)
    - Validation errors (`user_api_validation_errors_total`)
    - Database errors (`user_api_db_errors_total`)

- **Prometheus Alerts**:
  - `UserApiDown`: Service is down
  - `UserApiHighLatency`: High latency detected
  - `UserApiHighValidationErrors`: High validation error rate
  - `UserApiDatabaseErrors`: Database errors detected

## Usage Examples

### Register a new user

```bash
curl -X POST http://user-api.localhost/users/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "johndoe",
    "email": "john@example.com",
    "password": "SecurePassword123",
    "full_name": "John Doe"
  }'
```

### Get user by ID

```bash
curl http://user-api.localhost/users/1
```

### List users

```bash
curl http://user-api.localhost/users?limit=10&offset=0
```

### Health check

```bash
curl http://user-api.localhost/health
```

## Business Logic Patterns

### Input Validation Pattern

```python
# Validate required fields
if not username:
    return jsonify({'error': 'Username is required'}), 400

# Validate format
username_valid, username_error = validate_username(username)
if not username_valid:
    return jsonify({'error': username_error}), 400

# Validate uniqueness
cur.execute("SELECT id FROM users WHERE username = %s", (username,))
if cur.fetchone():
    return jsonify({'error': 'Username already exists'}), 409
```

### Business Rules Pattern

```python
# Define business rules as constants
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

# Apply business rules
if len(password) < MIN_PASSWORD_LENGTH:
    return jsonify({'error': f'Password must be at least {MIN_PASSWORD_LENGTH} characters'}), 400
```

### Error Handling Pattern

```python
try:
    # Business logic operation
    cur.execute("INSERT INTO users ...")
    conn.commit()
    return jsonify({'message': 'Success'}), 201
except psycopg2.IntegrityError:
    # Handle business rule violations (e.g., duplicate)
    return jsonify({'error': 'User already exists'}), 409
except Exception as e:
    # Handle unexpected errors
    app.logger.error(f"Error: {e}")
    return jsonify({'error': 'Database error'}), 500
```

## Development

### Local Development

```bash
# Set environment variables
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_DB=platform_db
export POSTGRES_USER=platform_user
export POSTGRES_PASSWORD=your_password

# Run service
python src/app.py
```

### Docker Build

```bash
docker build -t user-api:latest .
```

### Docker Run

```bash
docker run -p 8080:8080 \
  -e POSTGRES_HOST=platform-postgres \
  -e POSTGRES_DB=platform_db \
  -e POSTGRES_USER=platform_user \
  -e POSTGRES_PASSWORD=your_password \
  user-api:latest
```

## Smoke Tests

Run smoke tests after deployment:

```bash
./project_devops/scripts/smoke-test-user-api.sh
```

The smoke test validates:
- Health endpoint
- Metrics endpoint
- User registration (valid user)
- Get user by ID
- Validation error handling (duplicate username, invalid email, short password)
- List users

## Business Logic Patterns Documentation

See `docs-devops/02-system-architecture/business-logic-patterns.md` for comprehensive documentation on business logic patterns used in this service.
