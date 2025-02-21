# API Documentation

The Product Watch API follows RESTful principles and uses JSON for request/response payloads. 

## Base URL

```
http://localhost:8000/api/
```

## Authentication

The API uses JWT tokens for authentication. Tokens should be included in the `Authorization` header of requests:

```
Authorization: Bearer <jwt_token>
```

## Error Responses

Errors are returned with an appropriate HTTP status code and a JSON body in the following format:

```json
{
  "detail": "Error message"
}
```

## Endpoints

### Health Check

- `GET /health`
- Check the health status of the API
- Response 200 OK:
  ```json
  {
    "status": "ok" 
  }
  ```

### User Registration

- `POST /auth/register`
- Register a new user
- Request Body:
  ```json
  {
    "email": "user@example.com",
    "password": "secretpass",
    "is_admin": false
  }
  ```
- Response 201 Created:
  ```json
  {
    "id": "a3141c38-cf71-4925-b895-d3b8337dbc96",  
    "email": "user@example.com",
    "is_admin": false,
    "created_at": "2023-05-30T10:30:00Z" 
  }
  ```

### User Login

- `POST /auth/login`
- Login and receive an access token
- Request Body: 
  ```json
  {
    "email": "user@example.com", 
    "password": "secretpass"
  }
  ```
- Response 200 OK:
  ```json
  {  
    "access_token": "eyJhb...<snip>",
    "refresh_token": "fV9pZ...<snip>",
    "token_type": "bearer"
  }
  ```

### Token Refresh

- `POST /auth/refresh` 
- Get a new access token using a refresh token
- Request Body:
  ```json
  {
    "refresh_token": "fV9pZ...<snip>" 
  }
  ```  
- Response 200 OK:
  ```json
  {
    "access_token": "Xc2dT...<snip>",
    "refresh_token": "aB7jK...<snip>", 
    "token_type": "bearer"
  }
  ```

### Logout

- `POST /auth/logout`
- Revoke current user's tokens
- Requires authentication
- Response 204 No Content

### Get Current User

- `GET /auth/me`
- Get details of currently authenticated user
- Requires authentication  
- Response 200 OK:
  ```json
  {
    "id": "a3141c38-cf71-4925-b895-d3b8337dbc96",
    "email": "user@example.com",
    "is_admin": false,
    "created_at": "2023-05-30T10:30:00Z",
    "last_login": "2023-05-31T08:15:00Z"
  }  
  ```

### Get All Products

- `GET /products`
- Retrieve a paginated list of products
- Query Parameters:
  - `skip`: Number of products to skip (default 0)
  - `limit`: Max number of products to return (default 100) 
  - `name`: Filter by product name (optional)
- Response 200 OK:
  ```json
  {
    "items": [
      {
        "id": "0df94f39-d709-4cd9-a7fd-8b732fa5fc14",
        "name": "Product 1",
        "description": "Example product", 
        "price": 9.99,
        "stock": 100,
        "created_at": "2023-05-30T10:00:00Z",
        "updated_at": "2023-05-30T10:00:00Z" 
      },
      ...
    ],
    "total": 50
  }
  ```

### Get Popular Products

- `GET /products/popular?limit=5`  
- Retrieve most visited products
- Query Parameters:
  - `limit`: Max number of products to return (default 5)
- Response 200 OK:
  ```json
  [
    {
      "id": "0df94f39-d709-4cd9-a7fd-8b732fa5fc14",  
      "name": "Product 1",
      "description": "Popular product",
      "price": 9.99,
      "stock": 100,  
      "created_at": "2023-05-30T10:00:00Z",
      "updated_at": "2023-05-30T10:00:00Z"
    },
    ...  
  ]
  ```

### Get Product by ID

- `GET /products/{product_id}`
- Retrieve a single product by ID
- Path Parameters:  
  - `product_id`: UUID of the product
- Response 200 OK:
  ```json
  {
    "id": "0df94f39-d709-4cd9-a7fd-8b732fa5fc14",
    "name": "Product 1", 
    "description": "Example product",
    "price": 9.99,
    "stock": 100,
    "created_at": "2023-05-30T10:00:00Z",
    "updated_at": "2023-05-30T10:00:00Z"  
  }
  ```

### Create Product

- `POST /products`
- Create a new product  
- Requires admin authentication
- Request Body:
  ```json
  {
    "name": "New Product",
    "description": "Shiny new product", 
    "price": 19.99,
    "stock": 50  
  }
  ```
- Response 201 Created:
  ```json  
  {
    "id": "7c5c1b4e-2b4b-4b7d-93c8-3f1f3bbbd8b8",
    "name": "New Product",
    "description": "Shiny new product",
    "price": 19.99,
    "stock": 50,
    "created_at": "2023-06-01T12:00:00Z",  
    "updated_at": "2023-06-01T12:00:00Z"
  }
  ```

### Update Product

- `PUT /products/{product_id}`
- Update an existing product
- Requires admin authentication
- Path Parameters:
  - `product_id`: UUID of the product  
- Request Body:
  ```json
  {
    "name": "Updated Name",
    "price": 24.99  
  }
  ```
- Response 200 OK:
  ```json
  {
    "id": "0df94f39-d709-4cd9-a7fd-8b732fa5fc14",
    "name": "Updated Name",
    "description": "Example product", 
    "price": 24.99,
    "stock": 100,
    "created_at": "2023-05-30T10:00:00Z",
    "updated_at": "2023-06-01T13:00:00Z"
  }  
  ```

### Delete Product

- `DELETE /products/{product_id}`  
- Remove a product
- Requires admin authentication
- Path Parameters:
  - `product_id`: UUID of the product
- Response 204 No Content  

### Update Visit Duration

- `POST /visits/track/{visit_id}`
- Update the duration of a visit
- Path Parameters:  
  - `visit_id`: UUID of the visit
- Request Body:
  ```json
  {
    "duration": 120
  }
  ```
- Response 200 OK:  
  ```json
  {
    "detail": "Visit duration updated"
  }
  ```

### Get Product Visits  

- `GET /visits/product/{product_id}`
- Retrieve visits for a product
- Requires admin authentication  
- Path Parameters:
  - `product_id`: UUID of the product
- Query Parameters:  
  - `start_date`: Minimum visit timestamp (ISO format)
  - `end_date`: Maximum visit timestamp (ISO format) 
  - `limit`: Max number of visits to return (default 100)
- Response 200 OK:
  ```json
  [
    {
      "id": "b8bea5e3-8d33-4132-b5d8-c1fcedba4657", 
      "product_id": "0df94f39-d709-4cd9-a7fd-8b732fa5fc14",
      "ip_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", 
      "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:93.0) Gecko/20100101 Firefox/93.0",
      "timestamp": "2023-05-31T12:34:56Z",
      "duration": 75  
    },
    ...
  ]
  ```

### Get Product Analytics

- `GET /visits/analytics/product/{product_id}`
- Retrieve analytics data for a product 
- Requires admin authentication
- Path Parameters:
  - `product_id`: UUID of the product
- Response 200 OK:
  ```json  
  {
    "product_id": "0df94f39-d709-4cd9-a7fd-8b732fa5fc14",
    "total_visits": 1000,
    "unique_visitors": 800, 
    "avg_duration": 90,
    "last_updated": "2023-06-01T08:00:00Z",
    "daily_stats": [
      {
        "date": "2023-05-30",
        "count": 100,
        "unique_visitors": 80  
      },
      ...
    ] 
  }
  ```

### Get Popular Products (Admin)

- `GET /visits/popular?limit=5`
- Retrieve most visited products with additional stats
- Requires admin authentication
- Query Parameters:
  - `limit`: Max number of products to return (default 5)  
- Response 200 OK:
  ```json
  [
    {
      "product_id": "0df94f39-d709-4cd9-a7fd-8b732fa5fc14",
      "name": "Product 1",
      "total_visits": 1000,
      "unique_visitors": 800,
      "percentage_change": 15.0
    },
    ...
  ]
  ```