# Architecture Overview

The Product Watch system follows a layered architecture pattern with clear separation of concerns.

## High-Level Architecture Diagram

```mermaid
%%{init: {'theme': 'default', 'themeVariables': { 'fontSize': '16px'}}}%%
graph TB
    title["Product Architecture"]
    subgraph "Client Layer"
        ADMIN[Admin Client]
        ANON[Anonymous Client]
    end
    subgraph "API Gateway Layer"
        NGINX[Nginx]
        subgraph "Authentication"
            JWT[JWT Handler]
            RATES[Rate Limiter]
        end
    end
    subgraph "Application Layer"
        subgraph "Web Framework"
            DJANGO[Django]
            NINJA[Django Ninja]
        end
        subgraph "Core Services"
            PROD[Product Service]
            AUTH[Auth Service]
            VISIT[Visit Tracking Service]
            NOTIF[Notification Service]
        end
        subgraph "Background Workers"
            CELERY[Celery Workers]
            BEAT[Celery Beat]
        end
    end
    subgraph "Data Layer"
        PG[(PostgreSQL)]
        REDIS[(Redis)]
    end
    subgraph "External Services"
        SENDGRID[SendGrid API]
    end

classDef client fill:#e1bee7,stroke:#6a1b9a,stroke-width:2px;
classDef gateway fill:#bbdefb,stroke:#1976d2,stroke-width:2px;
classDef app fill:#c8e6c9,stroke:#388e3c,stroke-width:2px;
classDef data fill:#ffe0b2,stroke:#f57c00,stroke-width:2px;
classDef external fill:#ffcdd2,stroke:#d32f2f,stroke-width:2px;

class ADMIN,ANON client;
class NGINX,JWT,RATES gateway;
class DJANGO,NINJA,PROD,AUTH,VISIT,NOTIF,CELERY,BEAT app;
class PG,REDIS data;
class SENDGRID external;
```

## Key Components

### Client Layer
- **Admin Client**: Interface for authenticated admin users to manage products and view analytics
- **Anonymous Client**: Public interface for unauthenticated users to view products

### API Gateway Layer
- **Nginx**: Front-facing reverse proxy for request routing and SSL termination
- **JWT Handler**: Manages JSON Web Token based authentication
- **Rate Limiter**: Throttles requests to prevent abuse

### Application Layer
- **Django**: Python web framework serving as the foundation
- **Django Ninja**: Library for building API endpoints
- **Product Service**: Handles CRUD operations for products
- **Auth Service**: Manages user registration, login, and token handling
- **Visit Tracking Service**: Tracks anonymous user visits to products
- **Notification Service**: Sends email notifications for product updates
- **Celery**: Distributed task queue for asynchronous processing
- **Celery Beat**: Schedules periodic tasks like daily analytics reports

### Data Layer
- **PostgreSQL**: Primary relational database for storing application data
- **Redis**: In-memory data store for caching, rate limiting, and async task brokering

### External Services
- **SendGrid API**: Third-party service for sending transactional emails

## Request Flow

1. Client sends request to Nginx
2. Nginx routes request to Django Ninja API
3. JWT Handler middleware authenticates request
4. Rate Limiter middleware checks against throttling rules
5. Request reaches appropriate API endpoint
6. Endpoint invokes methods on Services to fulfill request
   - Services interact with Postgres and Redis to query and persist data
7. For async tasks (e.g. email notifications), Service dispatches tasks to Celery queue
   - Celery workers process tasks asynchronously
   - Celery Beat schedules periodic tasks
8. API forms response and sends back to client