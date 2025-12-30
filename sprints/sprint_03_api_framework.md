# Sprint 03: Core API Framework

**Phase:** 1 - Foundation
**Focus:** RESTful API foundation, Redis caching, and background task queue
**Dependencies:** Sprint 01 (Database), Sprint 02 (Auth)

---

## Testable Deliverable

**Human Test:**
1. API server starts without errors
2. Health check endpoint returns OK with all service statuses
3. API documentation (OpenAPI/Swagger) is accessible
4. Basic CRUD operations work on test entities
5. Error responses are consistent and helpful
6. Redis cache is connected and working
7. Background task queue processes jobs

**Test Endpoints:**
```bash
# Health check (comprehensive)
curl http://localhost:8000/health
# Returns: {"status": "healthy", "database": "connected", "redis": "connected", "version": "1.0.0"}

# API docs
open http://localhost:8000/docs  # Swagger UI

# Create a resource (authenticated)
curl -X POST http://localhost:8000/api/v1/memories \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"content": "Test memory", "memory_type": "note"}'

# Test background job
curl -X POST http://localhost:8000/api/v1/jobs/test \
  -H "Authorization: Bearer <token>"
# Returns: {"job_id": "uuid", "status": "queued"}

# Check job status
curl http://localhost:8000/api/v1/jobs/<job_id> \
  -H "Authorization: Bearer <token>"
```

---

## Requirements Included

### Parent Requirements
| ID | Description | Children |
|----|-------------|----------|
| REQ_007 | Web-based application interface | 17 |
| REQ_004 | Automated workflows and task management | 17 |

### Implementation Requirements

**Group 001 - Implementation (8 requirements)**
- REQ_001.2.1: OMNE storage service API
- REQ_001.2.2: Message ingestion service API
- REQ_001.2.3: Query service API
- REQ_001.2.4: Validation service API
- REQ_001.2.5: Security service API

**API Endpoints Domain (221 requirements)**
Core patterns to implement across all resource types.

---

## Architecture

```
                     [Load Balancer]
                           |
            +--------------+--------------+
            |              |              |
        [API-1]        [API-2]        [API-N]
            |              |              |
            +--------------+--------------+
                           |
          +----------------+----------------+
          |                |                |
      [PostgreSQL]     [Redis]        [Task Queue]
          |                |                |
     (Primary DB)     (Cache/Pub-Sub)  (Background Jobs)
```

---

## Infrastructure Components

### Redis Setup
```yaml
# docker-compose.yml additions
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes

volumes:
  redis_data:
```

### Task Queue (Celery with Redis)
```python
# celery_app.py
from celery import Celery

celery_app = Celery(
    "tanka",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/1"
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes
    worker_prefetch_multiplier=1,
)
```

---

## API Architecture

### Base URL Structure
```
/api/v1/
  /auth/        # Authentication (Sprint 02)
  /users/       # User management
  /memories/    # Memory CRUD
  /conversations/  # Chat management
  /messages/    # Message management
  /tasks/       # Task management
  /integrations/ # OAuth integrations
  /search/      # Unified search
  /jobs/        # Background job status
  /health       # Health check
```

### Standard Response Format
```json
{
  "success": true,
  "data": { ... },
  "meta": {
    "page": 1,
    "per_page": 20,
    "total": 100,
    "total_pages": 5
  }
}
```

### Error Response Format
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Email is required",
    "details": [
      {"field": "email", "message": "This field is required"}
    ],
    "request_id": "uuid"
  }
}
```

---

## Core Endpoints to Implement

### Health & Info
```yaml
GET /health
  Response:
    status: "healthy" | "degraded" | "unhealthy"
    services:
      database: "connected" | "disconnected"
      redis: "connected" | "disconnected"
      task_queue: "connected" | "disconnected"
    version: string
    uptime: integer (seconds)

GET /api/v1/info
  Response:
    api_version: "1.0.0"
    features_enabled: string[]
    environment: "development" | "staging" | "production"
```

### Users
```yaml
GET /api/v1/users/me
  Response: Current user profile with preferences

PATCH /api/v1/users/me
  Request: { display_name?, avatar_url?, first_name?, last_name? }
  Response: Updated user profile

GET /api/v1/users/me/preferences
  Response: User preferences

PATCH /api/v1/users/me/preferences
  Request: { theme?, language?, email_notifications?, push_notifications? }
  Response: Updated preferences

GET /api/v1/users/search
  Query: ?q=john&limit=10
  Response: User[] (for starting conversations)
```

### Background Jobs
```yaml
GET /api/v1/jobs/{job_id}
  Response:
    id: uuid
    status: "pending" | "running" | "completed" | "failed"
    result: any (if completed)
    error: string (if failed)
    created_at: timestamp
    started_at: timestamp
    completed_at: timestamp

GET /api/v1/jobs
  Query: ?status=pending&limit=20
  Response: Job[]
```

---

## Tasks

### Framework Setup
- [ ] Configure FastAPI with proper middleware
- [ ] Set up CORS for web client
- [ ] Configure request/response logging
- [ ] Set up exception handlers
- [ ] Add request ID middleware for tracing

### Redis Setup
- [ ] Install and configure Redis
- [ ] Create Redis connection pool
- [ ] Implement caching decorators
- [ ] Set up pub/sub for real-time features
- [ ] Cache invalidation utilities

### Task Queue Setup
- [ ] Install and configure Celery
- [ ] Create worker startup script
- [ ] Define base task classes
- [ ] Job status tracking endpoints
- [ ] Retry and error handling

### API Structure
- [ ] Create router organization
- [ ] Implement dependency injection pattern
- [ ] Set up Pydantic schemas for validation
- [ ] Configure OpenAPI documentation
- [ ] Add API versioning

### Core Endpoints
- [ ] Health check endpoint (comprehensive)
- [ ] User profile endpoints (get, update)
- [ ] User preferences endpoints
- [ ] User search endpoint
- [ ] Job status endpoints

### Middleware
- [ ] Request ID middleware (for tracing)
- [ ] Response time logging
- [ ] Error handling middleware
- [ ] Rate limiting (global and per-endpoint)
- [ ] CORS middleware

### Testing
- [ ] Set up pytest with fixtures
- [ ] Write tests for all endpoints
- [ ] Test error scenarios
- [ ] Test authentication integration
- [ ] Test caching behavior

---

## Acceptance Criteria

1. Server starts and responds to health check
2. Swagger documentation accessible at /docs
3. All CRUD operations work
4. Authentication middleware protects endpoints
5. Pagination works correctly
6. Error responses follow standard format
7. Request logging captures all API calls
8. Redis cache connected and functional
9. Background task queue processes jobs
10. Request IDs tracked for debugging

---

## Files to Create

```
src/
  api/
    __init__.py
    main.py            # FastAPI app initialization
    dependencies.py    # Dependency injection
    middleware.py      # Custom middleware
    exceptions.py      # Exception handlers

    v1/
      __init__.py
      router.py        # Main v1 router

      endpoints/
        __init__.py
        health.py
        users.py
        jobs.py

      schemas/
        __init__.py
        common.py      # Pagination, response wrappers
        users.py
        jobs.py

  cache/
    __init__.py
    redis_client.py    # Redis connection
    decorators.py      # Caching decorators

  tasks/
    __init__.py
    celery_app.py      # Celery configuration
    base.py            # Base task classes
    workers/
      __init__.py
      # Task implementations go here

  core/
    __init__.py
    config.py          # Application configuration
    logging.py         # Logging configuration
```

---

## Redis Implementation

### Connection Pool
```python
# cache/redis_client.py
import redis.asyncio as redis
from functools import lru_cache

class RedisClient:
    def __init__(self, url: str = "redis://localhost:6379"):
        self.url = url
        self.pool = None

    async def connect(self):
        self.pool = redis.ConnectionPool.from_url(
            self.url,
            max_connections=50,
            decode_responses=True
        )
        self.client = redis.Redis(connection_pool=self.pool)

    async def disconnect(self):
        if self.pool:
            await self.pool.disconnect()

    async def get(self, key: str) -> str | None:
        return await self.client.get(key)

    async def set(self, key: str, value: str, ttl: int = 300):
        await self.client.setex(key, ttl, value)

    async def delete(self, key: str):
        await self.client.delete(key)

    async def delete_pattern(self, pattern: str):
        keys = await self.client.keys(pattern)
        if keys:
            await self.client.delete(*keys)

redis_client = RedisClient()
```

### Caching Decorator
```python
# cache/decorators.py
from functools import wraps
import json
import hashlib

def cache(ttl: int = 300, key_prefix: str = ""):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            key_data = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            key_hash = hashlib.md5(key_data.encode()).hexdigest()
            cache_key = f"{key_prefix}:{key_hash}" if key_prefix else key_hash

            # Check cache
            cached = await redis_client.get(cache_key)
            if cached:
                return json.loads(cached)

            # Execute function
            result = await func(*args, **kwargs)

            # Store in cache
            await redis_client.set(cache_key, json.dumps(result, default=str), ttl)

            return result
        return wrapper
    return decorator

def invalidate_cache(pattern: str):
    """Invalidate cache keys matching pattern."""
    async def _invalidate():
        await redis_client.delete_pattern(pattern)
    return _invalidate
```

---

## Celery Tasks

### Base Task
```python
# tasks/base.py
from celery import Task
from datetime import datetime

class BaseTask(Task):
    abstract = True

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failure."""
        # Log to database or monitoring
        pass

    def on_success(self, retval, task_id, args, kwargs):
        """Handle task success."""
        pass

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Handle task retry."""
        pass
```

### Example Tasks
```python
# tasks/workers/embedding.py
from tasks.celery_app import celery_app
from tasks.base import BaseTask

@celery_app.task(base=BaseTask, bind=True, max_retries=3)
def generate_embedding(self, memory_id: str):
    """Generate embedding for a memory."""
    try:
        # Implementation here
        pass
    except Exception as exc:
        self.retry(exc=exc, countdown=60)

@celery_app.task(base=BaseTask)
def sync_integration(integration_id: str, provider: str):
    """Sync data from external integration."""
    # Implementation here
    pass

@celery_app.task(base=BaseTask)
def send_push_notification(user_id: str, title: str, body: str, data: dict):
    """Send push notification to user's devices."""
    # Implementation here
    pass
```

---

## Middleware Implementation

### Request ID Middleware
```python
# api/middleware.py
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id

        return response
```

### Response Time Middleware
```python
import time
import logging

logger = logging.getLogger(__name__)

class ResponseTimeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        response = await call_next(request)

        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)

        logger.info(
            f"{request.method} {request.url.path} "
            f"status={response.status_code} "
            f"duration={process_time:.3f}s"
        )

        return response
```

---

## Health Check Implementation

```python
# api/v1/endpoints/health.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from cache.redis_client import redis_client
from tasks.celery_app import celery_app
import time

router = APIRouter()

start_time = time.time()

@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    status = "healthy"
    services = {}

    # Check database
    try:
        await db.execute("SELECT 1")
        services["database"] = "connected"
    except Exception:
        services["database"] = "disconnected"
        status = "degraded"

    # Check Redis
    try:
        await redis_client.client.ping()
        services["redis"] = "connected"
    except Exception:
        services["redis"] = "disconnected"
        status = "degraded"

    # Check Celery
    try:
        celery_app.control.ping(timeout=1)
        services["task_queue"] = "connected"
    except Exception:
        services["task_queue"] = "disconnected"
        # Task queue down is degraded, not unhealthy

    return {
        "status": status,
        "services": services,
        "version": "1.0.0",
        "uptime": int(time.time() - start_time)
    }
```

---

## Configuration

```python
# core/config.py
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # API
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "Tanka AI"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # Database
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # CORS
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000"]

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    # Pagination
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    # JWT (from Sprint 02)
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings() -> Settings:
    return Settings()
```

---

## Application Startup

```python
# api/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from core.config import get_settings
from cache.redis_client import redis_client
from database.connection import engine
from api.middleware import RequestIDMiddleware, ResponseTimeMiddleware
from api.v1.router import api_router

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await redis_client.connect()
    yield
    # Shutdown
    await redis_client.disconnect()
    await engine.dispose()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    lifespan=lifespan
)

# Middleware (order matters - last added = first executed)
app.add_middleware(ResponseTimeMiddleware)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(api_router, prefix=settings.API_V1_PREFIX)
```

---

## Worker Startup Script

```bash
#!/bin/bash
# scripts/start_worker.sh

celery -A tasks.celery_app worker \
  --loglevel=info \
  --concurrency=4 \
  --queues=default,high_priority,low_priority
```

---

## Related Requirement Groups

- Group 001: Implementation (backend, frontend, middleware, shared_objects)
- Group 002: Dependencies (frontend, backend, shared_objects)
- API Endpoints domain (221 requirements)
