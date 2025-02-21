#!/bin/bash

# ProductWatch API Test Script
# This script tests all major endpoints of the ProductWatch API

# Configuration
BASE_URL="http://localhost:8000/api"
ADMIN_EMAIL="admin@example.com"
ADMIN_PASSWORD="adminpassword123"
REGULAR_EMAIL="user@example.com"
REGULAR_PASSWORD="userpassword123"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Variables to store tokens and IDs
ADMIN_ACCESS_TOKEN=""
ADMIN_REFRESH_TOKEN=""
USER_ACCESS_TOKEN=""
PRODUCT_ID=""
VISIT_ID=""

# Utility functions
print_header() {
    echo -e "\n${BLUE}======== $1 ========${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}$1${NC}"
}

check_status() {
    if [ $1 -ge 200 ] && [ $1 -lt 300 ]; then
        print_success "Status code: $1"
        return 0
    else
        print_error "Status code: $1"
        return 1
    fi
}

extract_json_value() {
    # $1: JSON string, $2: key name
    echo $1 | grep -o "\"$2\":[^,}]*" | cut -d: -f2- | tr -d '"' | tr -d ' '
}

#######################################
# TESTING BEGINS
#######################################

print_header "STARTING PRODUCTWATCH API TESTS"

# 1. Health Check
print_header "1. Health Check"
RESPONSE=$(curl -s $BASE_URL/)
echo $RESPONSE
if [[ $RESPONSE == *"status"*"ok"* ]]; then
    print_success "Health check passed"
else
    print_error "Health check failed"
fi

# 2. User Registration & Authentication
print_header "2. User Registration & Authentication"

# 2.1 Register admin user
print_info "Registering admin user..."
RESPONSE=$(curl -s -X POST $BASE_URL/auth/register \
    -H "Content-Type: application/json" \
    -d "{\"email\": \"$ADMIN_EMAIL\", \"password\": \"$ADMIN_PASSWORD\", \"is_admin\": true}")
echo $RESPONSE

# 2.2 Register regular user
print_info "Registering regular user..."
RESPONSE=$(curl -s -X POST $BASE_URL/auth/register \
    -H "Content-Type: application/json" \
    -d "{\"email\": \"$REGULAR_EMAIL\", \"password\": \"$REGULAR_PASSWORD\", \"is_admin\": false}")
echo $RESPONSE

# 2.3 Login as admin
print_info "Logging in as admin..."
RESPONSE=$(curl -s -X POST $BASE_URL/auth/login \
    -H "Content-Type: application/json" \
    -d "{\"email\": \"$ADMIN_EMAIL\", \"password\": \"$ADMIN_PASSWORD\"}")
echo $RESPONSE

# Extract tokens
ADMIN_ACCESS_TOKEN=$(echo $RESPONSE | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
ADMIN_REFRESH_TOKEN=$(echo $RESPONSE | grep -o '"refresh_token":"[^"]*' | cut -d'"' -f4)

if [ -z "$ADMIN_ACCESS_TOKEN" ]; then
    print_error "Failed to get admin access token"
    exit 1
else
    print_success "Admin authentication successful"
    print_info "Admin access token: ${ADMIN_ACCESS_TOKEN:0:15}..."
fi

# 2.4 Login as regular user
print_info "Logging in as regular user..."
RESPONSE=$(curl -s -X POST $BASE_URL/auth/login \
    -H "Content-Type: application/json" \
    -d "{\"email\": \"$REGULAR_EMAIL\", \"password\": \"$REGULAR_PASSWORD\"}")
echo $RESPONSE

# Extract token
USER_ACCESS_TOKEN=$(echo $RESPONSE | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [ -z "$USER_ACCESS_TOKEN" ]; then
    print_error "Failed to get user access token"
else
    print_success "User authentication successful"
    print_info "User access token: ${USER_ACCESS_TOKEN:0:15}..."
fi

# 2.5 Get current admin profile
print_info "Getting admin profile..."
RESPONSE=$(curl -s $BASE_URL/auth/me \
    -H "Authorization: Bearer $ADMIN_ACCESS_TOKEN")
echo $RESPONSE

if [[ $RESPONSE == *"is_admin\":true"* ]]; then
    print_success "Admin profile verification passed"
else
    print_error "Admin profile verification failed"
fi

# 3. Product Management
print_header "3. Product Management"

# 3.1 Create product (admin only)
print_info "Creating a new product..."
RESPONSE=$(curl -s -X POST $BASE_URL/products/ \
    -H "Authorization: Bearer $ADMIN_ACCESS_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "name": "Test Product",
        "description": "This is a test product with a detailed description",
        "price": 29.99,
        "stock": 100
    }')
echo $RESPONSE

# Extract product ID
PRODUCT_ID=$(echo $RESPONSE | grep -o '"id":"[^"]*' | cut -d'"' -f4)

if [ -z "$PRODUCT_ID" ]; then
    print_error "Failed to create product"
else
    print_success "Product created successfully with ID: $PRODUCT_ID"
fi

# 3.2 List all products
print_info "Listing all products..."
RESPONSE=$(curl -s $BASE_URL/products/)
echo $RESPONSE

if [[ $RESPONSE == *"items"* ]]; then
    print_success "Product listing successful"
else
    print_error "Product listing failed"
fi

# 3.3 Get specific product
print_info "Getting specific product details..."
RESPONSE=$(curl -s $BASE_URL/products/$PRODUCT_ID)
echo $RESPONSE

if [[ $RESPONSE == *"$PRODUCT_ID"* ]]; then
    print_success "Product detail retrieval successful"
else
    print_error "Product detail retrieval failed"
fi

# 3.4 Update product (admin only)
print_info "Updating product..."
RESPONSE=$(curl -s -X PUT $BASE_URL/products/$PRODUCT_ID \
    -H "Authorization: Bearer $ADMIN_ACCESS_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "name": "Updated Test Product",
        "price": 39.99
    }')
echo $RESPONSE

if [[ $RESPONSE == *"Updated Test Product"* ]]; then
    print_success "Product update successful"
else
    print_error "Product update failed"
fi

# 3.5 Create a second product
print_info "Creating a second product for testing..."
RESPONSE=$(curl -s -X POST $BASE_URL/products/ \
    -H "Authorization: Bearer $ADMIN_ACCESS_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "name": "Second Test Product",
        "description": "This is another test product",
        "price": 19.99,
        "stock": 50
    }')
echo $RESPONSE

# Extract product ID
SECOND_PRODUCT_ID=$(echo $RESPONSE | grep -o '"id":"[^"]*' | cut -d'"' -f4)

if [ -z "$SECOND_PRODUCT_ID" ]; then
    print_error "Failed to create second product"
else
    print_success "Second product created successfully with ID: $SECOND_PRODUCT_ID"
fi

# 3.6 List popular products
print_info "Listing popular products..."
RESPONSE=$(curl -s $BASE_URL/products/popular?limit=5)
echo $RESPONSE

# 3.7 Access control test (regular user can't update)
print_info "Testing access control (user trying to update product)..."
RESPONSE=$(curl -s -X PUT $BASE_URL/products/$PRODUCT_ID \
    -H "Authorization: Bearer $USER_ACCESS_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "name": "Should Fail Update",
        "price": 0.99
    }')
echo $RESPONSE

if [[ $RESPONSE == *"Unauthorized"* ]]; then
    print_success "Access control working properly"
else
    print_error "Access control failed"
fi

# 4. Visit Tracking
print_header "4. Visit Tracking"

# 4.1 Generate visits by accessing products multiple times
print_info "Generating visits by accessing products..."
for i in {1..5}; do
    curl -s $BASE_URL/products/$PRODUCT_ID > /dev/null
    curl -s $BASE_URL/products/$SECOND_PRODUCT_ID > /dev/null
    sleep 1
done
print_success "Generated multiple visits to products"

# 4.2 Get visit analytics for a product (admin only)
print_info "Getting visit analytics..."
RESPONSE=$(curl -s $BASE_URL/visits/analytics/product/$PRODUCT_ID \
    -H "Authorization: Bearer $ADMIN_ACCESS_TOKEN")
echo $RESPONSE

if [[ $RESPONSE == *"total_visits"* ]]; then
    print_success "Visit analytics retrieved successfully"
else
    print_error "Failed to retrieve visit analytics"
fi

# 4.3 Get visit list for a product (admin only)
print_info "Getting visit list..."
RESPONSE=$(curl -s $BASE_URL/visits/product/$PRODUCT_ID \
    -H "Authorization: Bearer $ADMIN_ACCESS_TOKEN")
echo $RESPONSE

# 4.4 Get popular products based on visits (admin only)
print_info "Getting popular products based on visits..."
RESPONSE=$(curl -s $BASE_URL/visits/popular \
    -H "Authorization: Bearer $ADMIN_ACCESS_TOKEN")
echo $RESPONSE

# 5. JWT Token Management
print_header "5. JWT Token Management"

# 5.1 Refresh token
print_info "Testing token refresh..."
RESPONSE=$(curl -s -X POST $BASE_URL/auth/refresh \
    -H "Content-Type: application/json" \
    -d "{\"refresh_token\": \"$ADMIN_REFRESH_TOKEN\"}")
echo $RESPONSE

NEW_ACCESS_TOKEN=$(echo $RESPONSE | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [ -z "$NEW_ACCESS_TOKEN" ]; then
    print_error "Token refresh failed"
else
    print_success "Token refresh successful"
    print_info "New access token: ${NEW_ACCESS_TOKEN:0:15}..."
    # Update token for subsequent requests
    ADMIN_ACCESS_TOKEN=$NEW_ACCESS_TOKEN
fi

# 5.2 Verify the new token works
print_info "Verifying new token works..."
RESPONSE=$(curl -s $BASE_URL/auth/me \
    -H "Authorization: Bearer $ADMIN_ACCESS_TOKEN")
echo $RESPONSE

if [[ $RESPONSE == *"is_admin\":true"* ]]; then
    print_success "New token verification passed"
else
    print_error "New token verification failed"
fi

# 5.3 Logout
print_info "Testing logout..."
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST $BASE_URL/auth/logout \
    -H "Authorization: Bearer $ADMIN_ACCESS_TOKEN")
check_status $STATUS

# 6. Cleanup
print_header "6. Cleanup"

# 6.1 Delete products
print_info "Deleting test products..."
# We need to log in again since we logged out
RESPONSE=$(curl -s -X POST $BASE_URL/auth/login \
    -H "Content-Type: application/json" \
    -d "{\"email\": \"$ADMIN_EMAIL\", \"password\": \"$ADMIN_PASSWORD\"}")
ADMIN_ACCESS_TOKEN=$(echo $RESPONSE | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X DELETE $BASE_URL/products/$PRODUCT_ID \
    -H "Authorization: Bearer $ADMIN_ACCESS_TOKEN")
check_status $STATUS

STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X DELETE $BASE_URL/products/$SECOND_PRODUCT_ID \
    -H "Authorization: Bearer $ADMIN_ACCESS_TOKEN")
check_status $STATUS

print_header "TEST SUMMARY"
echo "All critical endpoints have been tested:"
echo "✓ Health check"
echo "✓ User registration and authentication"
echo "✓ Product management (CRUD operations)"
echo "✓ Visit tracking and analytics"
echo "✓ JWT token management (refresh, logout)"
echo "✓ Access control"

print_header "TESTS COMPLETED"