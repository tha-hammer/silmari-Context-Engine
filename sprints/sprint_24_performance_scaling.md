# Sprint 24: Performance & Scaling

**Phase:** 7 - Mobile & Scale
**Focus:** Production readiness and scalability
**Dependencies:** All previous sprints

---

## Testable Deliverable

**Human Test:**
1. Run load test (100 concurrent users)
2. All requests complete < 2 seconds
3. No errors under load
4. View monitoring dashboard
5. Alerts fire on threshold breach
6. Database performs under load

---

## Requirements Included

### Parent Requirements
| ID | Description | Children |
|----|-------------|----------|
| REQ_293 | 10x user growth without refactoring | 19 |
| REQ_288 | Performance and scalability optimization | 20 |
| REQ_243 | Page load < 2 seconds | 18 |

### Implementation Requirements
- REQ_293.2.1: Horizontal scaling
- REQ_288.2.1: Performance optimization
- REQ_243.2.1: Frontend optimization
- REQ_243.2.2: API optimization

---

## Performance Targets

| Metric | Target | Current |
|--------|--------|---------|
| API response p50 | < 100ms | TBD |
| API response p99 | < 500ms | TBD |
| Page load | < 2s | TBD |
| Time to interactive | < 3s | TBD |
| Concurrent users | 1000 | TBD |
| Memory search | < 200ms | TBD |
| Database queries | < 50ms | TBD |

---

## Architecture

```
                    [CDN]
                      |
                [Load Balancer]
                      |
        +-------------+-------------+
        |             |             |
    [API-1]       [API-2]       [API-N]
        |             |             |
        +-------------+-------------+
                      |
              [Redis Cache]
                      |
        +-------------+-------------+
        |             |             |
    [DB Primary]  [DB Read-1]  [DB Read-N]
```

---

## Tasks

### Backend - Performance
- [ ] Add Redis caching layer
- [ ] Implement query optimization
- [ ] Add database read replicas
- [ ] Connection pooling tuning
- [ ] Async job processing

### Backend - Scaling
- [ ] Stateless API design
- [ ] Session externalization
- [ ] Database connection management
- [ ] Rate limiting per user

### Frontend - Performance
- [ ] Code splitting
- [ ] Image optimization
- [ ] Bundle size reduction
- [ ] Service worker caching

### Infrastructure
- [ ] CDN setup
- [ ] Load balancer configuration
- [ ] Auto-scaling policies
- [ ] Health check endpoints

### Monitoring
- [ ] APM integration (DataDog/NewRelic)
- [ ] Custom metrics
- [ ] Alert configuration
- [ ] Dashboard creation

### Load Testing
- [ ] Create load test scripts
- [ ] Run baseline tests
- [ ] Identify bottlenecks
- [ ] Optimize and retest

---

## Acceptance Criteria

1. 100 concurrent users supported
2. p99 latency < 500ms
3. No memory leaks
4. Database handles load
5. Caching reduces DB hits
6. Monitoring dashboards live
7. Alerts configured

---

## Caching Strategy

```python
from redis import Redis
from functools import wraps
import json

redis = Redis(host='localhost', port=6379, db=0)

def cache(ttl: int = 300, key_prefix: str = ""):
    """Redis cache decorator."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}:{func.__name__}:{hash(str(args) + str(kwargs))}"

            # Check cache
            cached = redis.get(cache_key)
            if cached:
                return json.loads(cached)

            # Call function
            result = await func(*args, **kwargs)

            # Store in cache
            redis.setex(cache_key, ttl, json.dumps(result, default=str))

            return result
        return wrapper
    return decorator

# Usage
@cache(ttl=60, key_prefix="memories")
async def get_user_memories(user_id: UUID):
    return await memory_repository.list(user_id)

# Cache invalidation
def invalidate_user_cache(user_id: UUID):
    pattern = f"memories:*:{user_id}*"
    keys = redis.keys(pattern)
    if keys:
        redis.delete(*keys)
```

---

## Database Optimization

```python
# Query optimization examples

# BAD: N+1 query
async def get_conversations_bad(user_id: UUID):
    conversations = await db.fetch_all(
        "SELECT * FROM conversations WHERE user_id = :id", {"id": user_id}
    )
    for conv in conversations:
        conv.last_message = await db.fetch_one(
            "SELECT * FROM messages WHERE conversation_id = :id ORDER BY created_at DESC LIMIT 1",
            {"id": conv.id}
        )
    return conversations

# GOOD: Single query with JOIN
async def get_conversations_good(user_id: UUID):
    return await db.fetch_all("""
        SELECT c.*,
            m.content as last_message_content,
            m.created_at as last_message_at
        FROM conversations c
        LEFT JOIN LATERAL (
            SELECT content, created_at
            FROM messages
            WHERE conversation_id = c.id
            ORDER BY created_at DESC
            LIMIT 1
        ) m ON true
        WHERE c.user_id = :id
        ORDER BY COALESCE(m.created_at, c.created_at) DESC
    """, {"id": user_id})

# Add indexes for common queries
"""
CREATE INDEX CONCURRENTLY idx_messages_conv_created
ON messages(conversation_id, created_at DESC);

CREATE INDEX CONCURRENTLY idx_memories_user_type
ON memories(user_id, memory_type, created_at DESC);

-- Partial index for active conversations
CREATE INDEX CONCURRENTLY idx_conv_active
ON conversations(user_id, last_message_at DESC)
WHERE deleted_at IS NULL;
"""
```

---

## Load Testing

```python
# locustfile.py
from locust import HttpUser, task, between

class TankaUser(HttpUser):
    wait_time = between(1, 3)
    token = None

    def on_start(self):
        # Login
        response = self.client.post("/api/v1/auth/login", json={
            "email": f"loadtest_{self.user_id}@example.com",
            "password": "testpassword"
        })
        self.token = response.json()["access_token"]

    def auth_headers(self):
        return {"Authorization": f"Bearer {self.token}"}

    @task(3)
    def list_conversations(self):
        self.client.get("/api/v1/conversations", headers=self.auth_headers())

    @task(2)
    def list_memories(self):
        self.client.get("/api/v1/memories", headers=self.auth_headers())

    @task(1)
    def search_memories(self):
        self.client.get(
            "/api/v1/memories/search?q=project",
            headers=self.auth_headers()
        )

    @task(2)
    def send_message(self):
        self.client.post(
            f"/api/v1/conversations/{self.conv_id}/messages",
            json={"content": "Test message"},
            headers=self.auth_headers()
        )

# Run: locust -f locustfile.py --host=http://localhost:8000
```

---

## Monitoring Setup

```python
# Prometheus metrics
from prometheus_client import Counter, Histogram, generate_latest

REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint']
)

# Middleware
class MetricsMiddleware:
    async def __call__(self, request: Request, call_next):
        start = time.time()
        response = await call_next(request)
        duration = time.time() - start

        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code
        ).inc()

        REQUEST_LATENCY.labels(
            method=request.method,
            endpoint=request.url.path
        ).observe(duration)

        return response

# Metrics endpoint
@router.get("/metrics")
async def metrics():
    return Response(
        generate_latest(),
        media_type="text/plain"
    )
```

---

## Alert Configuration

```yaml
# alerts.yaml
groups:
  - name: tanka-alerts
    rules:
      - alert: HighLatency
        expr: histogram_quantile(0.99, http_request_duration_seconds) > 0.5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High API latency"

      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.01
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate"

      - alert: DatabaseConnectionsHigh
        expr: pg_stat_activity_count > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Database connections nearing limit"
```

---

## Files to Create

```
src/
  monitoring/
    __init__.py
    metrics.py
    middleware.py
    health.py

  cache/
    __init__.py
    redis_client.py
    decorators.py

infra/
  docker/
    docker-compose.prod.yml
  k8s/
    deployment.yaml
    service.yaml
    ingress.yaml
    hpa.yaml  # Horizontal Pod Autoscaler

tests/
  load/
    locustfile.py
    scenarios/
```

---

## Related Requirement Groups

- REQ_293: Scalability
- REQ_288: Performance
- REQ_243: Load time
- Monitoring domain

---

## Database Read/Write Split

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager

class DatabaseManager:
    """Manage read/write database connections with replica routing."""

    def __init__(self):
        # Primary for writes
        self.write_engine = create_engine(
            os.getenv('DATABASE_URL_PRIMARY'),
            pool_size=20,
            max_overflow=10,
            pool_pre_ping=True,
            pool_recycle=3600,
        )

        # Read replicas (can have multiple)
        replica_urls = os.getenv('DATABASE_URL_REPLICAS', '').split(',')
        self.read_engines = [
            create_engine(
                url.strip(),
                pool_size=20,
                max_overflow=10,
                pool_pre_ping=True,
                pool_recycle=3600,
            )
            for url in replica_urls if url.strip()
        ]

        # Fall back to primary if no replicas configured
        if not self.read_engines:
            self.read_engines = [self.write_engine]

        self._read_index = 0

    def get_write_session(self) -> Session:
        """Get session for write operations."""
        SessionLocal = sessionmaker(bind=self.write_engine)
        return SessionLocal()

    def get_read_session(self) -> Session:
        """Get session for read operations (round-robin across replicas)."""
        engine = self.read_engines[self._read_index % len(self.read_engines)]
        self._read_index += 1
        SessionLocal = sessionmaker(bind=engine)
        return SessionLocal()

    @contextmanager
    def read_session(self):
        """Context manager for read operations."""
        session = self.get_read_session()
        try:
            yield session
        finally:
            session.close()

    @contextmanager
    def write_session(self):
        """Context manager for write operations."""
        session = self.get_write_session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


# Usage in services
db = DatabaseManager()

async def get_conversations(user_id: UUID):
    """Read operation - uses replica."""
    with db.read_session() as session:
        return session.query(Conversation).filter_by(user_id=user_id).all()

async def create_message(data: dict):
    """Write operation - uses primary."""
    with db.write_session() as session:
        message = Message(**data)
        session.add(message)
        return message
```

---

## WebSocket Scaling with Redis Pub/Sub

```python
import aioredis
from typing import Dict, Set

class ScalableWebSocketManager:
    """WebSocket manager that scales across multiple server instances."""

    def __init__(self):
        self.local_connections: Dict[str, Set[WebSocket]] = {}
        self.redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        self.pubsub = None

    async def connect(self):
        """Initialize Redis pub/sub connection."""
        self.redis = await aioredis.from_url(self.redis_url)
        self.pubsub = self.redis.pubsub()
        await self.pubsub.subscribe('websocket_broadcast')

        # Start listening for messages from other instances
        asyncio.create_task(self._listen_for_broadcasts())

    async def _listen_for_broadcasts(self):
        """Listen for messages from other server instances."""
        async for message in self.pubsub.listen():
            if message['type'] == 'message':
                data = json.loads(message['data'])
                user_id = data['user_id']

                # Only send to locally connected users
                if user_id in self.local_connections:
                    for ws in self.local_connections[user_id]:
                        await ws.send_json(data['payload'])

    async def add_connection(self, user_id: str, websocket: WebSocket):
        """Register a WebSocket connection."""
        if user_id not in self.local_connections:
            self.local_connections[user_id] = set()
        self.local_connections[user_id].add(websocket)

    async def remove_connection(self, user_id: str, websocket: WebSocket):
        """Unregister a WebSocket connection."""
        if user_id in self.local_connections:
            self.local_connections[user_id].discard(websocket)
            if not self.local_connections[user_id]:
                del self.local_connections[user_id]

    async def send_to_user(self, user_id: str, message: dict):
        """Send message to user across all server instances."""
        # Publish to Redis so all instances receive it
        await self.redis.publish('websocket_broadcast', json.dumps({
            'user_id': user_id,
            'payload': message,
        }))
```

---

## Connection Pool Configuration

```python
# Environment variables for pool configuration
DATABASE_POOL_SIZE = int(os.getenv('DATABASE_POOL_SIZE', '20'))
DATABASE_POOL_OVERFLOW = int(os.getenv('DATABASE_POOL_OVERFLOW', '10'))
DATABASE_POOL_TIMEOUT = int(os.getenv('DATABASE_POOL_TIMEOUT', '30'))

REDIS_POOL_SIZE = int(os.getenv('REDIS_POOL_SIZE', '50'))

# SQLAlchemy engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    pool_size=DATABASE_POOL_SIZE,        # Connections to keep open
    max_overflow=DATABASE_POOL_OVERFLOW,  # Extra connections allowed
    pool_timeout=DATABASE_POOL_TIMEOUT,   # Seconds to wait for connection
    pool_pre_ping=True,                   # Verify connections before use
    pool_recycle=3600,                    # Recycle connections after 1 hour
)

# Redis connection pool
redis_pool = redis.ConnectionPool.from_url(
    REDIS_URL,
    max_connections=REDIS_POOL_SIZE,
)
redis_client = redis.Redis(connection_pool=redis_pool)
```

---

## Graceful Shutdown

```python
import signal
import asyncio
from contextlib import asynccontextmanager

shutdown_event = asyncio.Event()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for graceful shutdown."""

    # Startup
    print("Starting up...")
    await websocket_manager.connect()

    yield  # Application runs

    # Shutdown
    print("Shutting down gracefully...")

    # 1. Stop accepting new requests (handled by load balancer health check)

    # 2. Close WebSocket connections gracefully
    for user_id, connections in websocket_manager.local_connections.items():
        for ws in connections:
            await ws.close(code=1001, reason="Server shutting down")

    # 3. Wait for in-flight requests to complete (max 30 seconds)
    await asyncio.sleep(5)

    # 4. Close database connections
    engine.dispose()

    # 5. Close Redis connections
    await redis_client.close()

    print("Shutdown complete")


app = FastAPI(lifespan=lifespan)


# Health check endpoint for load balancer
@app.get("/health")
async def health_check():
    if shutdown_event.is_set():
        # Return unhealthy during shutdown to drain traffic
        return JSONResponse(
            status_code=503,
            content={"status": "shutting_down"}
        )
    return {"status": "healthy"}


# Signal handlers
def handle_shutdown(signum, frame):
    """Handle SIGTERM/SIGINT for graceful shutdown."""
    shutdown_event.set()

signal.signal(signal.SIGTERM, handle_shutdown)
signal.signal(signal.SIGINT, handle_shutdown)
```

---

## Vector Database (pgvector) Scaling

```python
# pgvector-specific configuration for performance

# 1. Set work_mem for vector operations
"""
-- Run in PostgreSQL
SET work_mem = '256MB';  -- Increase for large vector operations

-- Or per-session in application
await connection.execute("SET work_mem = '256MB'")
"""

# 2. Use IVFFlat index for approximate nearest neighbor (faster than exact)
"""
-- Create IVFFlat index (lists = sqrt(num_vectors), good default)
CREATE INDEX idx_memories_embedding ON memories
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- For exact search, use HNSW (slower to build, faster to query)
CREATE INDEX idx_memories_embedding_hnsw ON memories
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
"""

# 3. Query with probes parameter for IVFFlat
async def search_memories_vectordb(embedding: List[float], limit: int = 10):
    """Search with optimized vector query."""
    return await db.fetch_all("""
        SET ivfflat.probes = 10;  -- More probes = more accurate, slower
        SELECT id, content, 1 - (embedding <=> :query_embedding) as similarity
        FROM memories
        WHERE user_id = :user_id
        ORDER BY embedding <=> :query_embedding
        LIMIT :limit
    """, {
        "query_embedding": embedding,
        "user_id": user_id,
        "limit": limit,
    })
```

---

## Validation Notes (2025-12-30)

**Status:** ✅ Validated + Fixed

**Fixes Applied:**
1. Added `DatabaseManager` with read/write split and replica round-robin
2. Added `ScalableWebSocketManager` using Redis pub/sub for multi-instance support
3. Added explicit connection pool configuration with environment variables
4. Added graceful shutdown with signal handlers and connection draining
5. Added pgvector-specific optimization guidance (IVFFlat, HNSW indexes, probes)
6. Added health check endpoint that returns 503 during shutdown

**Cross-Sprint Dependencies:**
- Sprint 06: Vector database indexes for semantic search
- Sprint 09: WebSocket infrastructure (now scaled with Redis)
- Sprint 03: Redis setup for caching and pub/sub

**Infrastructure Requirements:**
- PostgreSQL read replicas (optional but recommended)
- Redis for caching, session storage, and WebSocket pub/sub
- Load balancer that respects health check for graceful shutdown
- Kubernetes HPA or similar for auto-scaling

**Environment Variables:**
```
DATABASE_URL_PRIMARY=postgresql://...
DATABASE_URL_REPLICAS=postgresql://replica1/...,postgresql://replica2/...
DATABASE_POOL_SIZE=20
DATABASE_POOL_OVERFLOW=10
REDIS_URL=redis://...
REDIS_POOL_SIZE=50
```
