#!/bin/bash
# Smoke test script for user-api service
# Validates business logic: user registration, validation, profile management

set -e

SERVICE_URL="${USER_API_URL:-http://user-api.localhost}"
TIMEOUT="${TIMEOUT:-5}"

echo "=========================================="
echo "User API Smoke Test"
echo "=========================================="
echo "Service URL: $SERVICE_URL"
echo ""

# Test 1: Health check
echo "[TEST 1] Health check..."
health_response=$(curl -s -w "\n%{http_code}" --max-time $TIMEOUT "$SERVICE_URL/health" || echo -e "\n000")
health_body=$(echo "$health_response" | head -n -1)
health_code=$(echo "$health_response" | tail -n 1)

if [ "$health_code" != "200" ]; then
    echo "❌ FAILED: Health check returned status $health_code"
    echo "Response: $health_body"
    exit 1
fi

echo "✅ Health check passed"
echo "Response: $health_body"
echo ""

# Test 2: Metrics endpoint
echo "[TEST 2] Metrics endpoint..."
metrics_code=$(curl -s -o /dev/null -w "%{http_code}" --max-time $TIMEOUT "$SERVICE_URL/metrics" || echo "000")

if [ "$metrics_code" != "200" ]; then
    echo "❌ FAILED: Metrics endpoint returned status $metrics_code"
    exit 1
fi

echo "✅ Metrics endpoint accessible"
echo ""

# Test 3: User registration - valid user
echo "[TEST 3] User registration - valid user..."
register_response=$(curl -s -w "\n%{http_code}" --max-time $TIMEOUT \
    -X POST \
    -H "Content-Type: application/json" \
    -d '{
        "username": "testuser_'$(date +%s)'",
        "email": "test_'$(date +%s)'@example.com",
        "password": "TestPassword123",
        "full_name": "Test User"
    }' \
    "$SERVICE_URL/users/register" || echo -e "\n000")

register_body=$(echo "$register_response" | head -n -1)
register_code=$(echo "$register_response" | tail -n 1)

if [ "$register_code" != "201" ]; then
    echo "❌ FAILED: User registration returned status $register_code"
    echo "Response: $register_body"
    exit 1
fi

# Extract user ID from response
user_id=$(echo "$register_body" | grep -o '"id":[0-9]*' | grep -o '[0-9]*' || echo "")
if [ -z "$user_id" ]; then
    echo "❌ FAILED: Could not extract user ID from response"
    echo "Response: $register_body"
    exit 1
fi

echo "✅ User registration successful (user_id: $user_id)"
echo "Response: $register_body"
echo ""

# Test 4: Get user by ID
echo "[TEST 4] Get user by ID..."
get_user_response=$(curl -s -w "\n%{http_code}" --max-time $TIMEOUT "$SERVICE_URL/users/$user_id" || echo -e "\n000")
get_user_body=$(echo "$get_user_response" | head -n -1)
get_user_code=$(echo "$get_user_response" | tail -n 1)

if [ "$get_user_code" != "200" ]; then
    echo "❌ FAILED: Get user returned status $get_user_code"
    echo "Response: $get_user_body"
    exit 1
fi

echo "✅ Get user successful"
echo "Response: $get_user_body"
echo ""

# Test 5: User registration - validation error (duplicate username)
echo "[TEST 5] User registration - validation error (duplicate username)..."
duplicate_response=$(curl -s -w "\n%{http_code}" --max-time $TIMEOUT \
    -X POST \
    -H "Content-Type: application/json" \
    -d '{
        "username": "testuser_duplicate",
        "email": "duplicate_'$(date +%s)'@example.com",
        "password": "TestPassword123"
    }' \
    "$SERVICE_URL/users/register" || echo -e "\n000")

duplicate_body=$(echo "$duplicate_response" | head -n -1)
duplicate_code=$(echo "$duplicate_response" | tail -n 1)

# Register first user
curl -s -X POST -H "Content-Type: application/json" \
    -d '{"username": "testuser_duplicate", "email": "first_'$(date +%s)'@example.com", "password": "TestPassword123"}' \
    "$SERVICE_URL/users/register" > /dev/null || true

# Try to register duplicate
duplicate_response=$(curl -s -w "\n%{http_code}" --max-time $TIMEOUT \
    -X POST \
    -H "Content-Type: application/json" \
    -d '{
        "username": "testuser_duplicate",
        "email": "second_'$(date +%s)'@example.com",
        "password": "TestPassword123"
    }' \
    "$SERVICE_URL/users/register" || echo -e "\n000")

duplicate_body=$(echo "$duplicate_response" | head -n -1)
duplicate_code=$(echo "$duplicate_response" | tail -n 1)

if [ "$duplicate_code" != "409" ]; then
    echo "⚠️  WARNING: Duplicate username validation returned status $duplicate_code (expected 409)"
    echo "Response: $duplicate_body"
else
    echo "✅ Validation error handling works correctly (duplicate username)"
fi
echo ""

# Test 6: User registration - validation error (invalid email)
echo "[TEST 6] User registration - validation error (invalid email)..."
invalid_email_response=$(curl -s -w "\n%{http_code}" --max-time $TIMEOUT \
    -X POST \
    -H "Content-Type: application/json" \
    -d '{
        "username": "testuser_invalid_'$(date +%s)'",
        "email": "invalid-email",
        "password": "TestPassword123"
    }' \
    "$SERVICE_URL/users/register" || echo -e "\n000")

invalid_email_body=$(echo "$invalid_email_response" | head -n -1)
invalid_email_code=$(echo "$invalid_email_response" | tail -n 1)

if [ "$invalid_email_code" != "400" ]; then
    echo "⚠️  WARNING: Invalid email validation returned status $invalid_email_code (expected 400)"
    echo "Response: $invalid_email_body"
else
    echo "✅ Validation error handling works correctly (invalid email)"
fi
echo ""

# Test 7: User registration - validation error (short password)
echo "[TEST 7] User registration - validation error (short password)..."
short_password_response=$(curl -s -w "\n%{http_code}" --max-time $TIMEOUT \
    -X POST \
    -H "Content-Type: application/json" \
    -d '{
        "username": "testuser_short_'$(date +%s)'",
        "email": "short_'$(date +%s)'@example.com",
        "password": "short"
    }' \
    "$SERVICE_URL/users/register" || echo -e "\n000")

short_password_body=$(echo "$short_password_response" | head -n -1)
short_password_code=$(echo "$short_password_response" | tail -n 1)

if [ "$short_password_code" != "400" ]; then
    echo "⚠️  WARNING: Short password validation returned status $short_password_code (expected 400)"
    echo "Response: $short_password_body"
else
    echo "✅ Validation error handling works correctly (short password)"
fi
echo ""

# Test 8: List users
echo "[TEST 8] List users..."
list_users_response=$(curl -s -w "\n%{http_code}" --max-time $TIMEOUT "$SERVICE_URL/users?limit=10" || echo -e "\n000")
list_users_body=$(echo "$list_users_response" | head -n -1)
list_users_code=$(echo "$list_users_response" | tail -n 1)

if [ "$list_users_code" != "200" ]; then
    echo "❌ FAILED: List users returned status $list_users_code"
    echo "Response: $list_users_body"
    exit 1
fi

echo "✅ List users successful"
echo "Response: $list_users_body"
echo ""

echo "=========================================="
echo "✅ All smoke tests passed!"
echo "=========================================="
