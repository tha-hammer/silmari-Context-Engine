# Sprint 05: Memory Storage Core

**Phase:** 2 - Memory System
**Focus:** OMNE memory storage backend with async embedding generation
**Dependencies:** Sprint 01 (Database), Sprint 02 (Auth), Sprint 03 (API + Redis + Celery)

---

## Testable Deliverable

**Human Test:**
1. Create a memory via API
2. Verify memory is stored in database with `embedding_status: "pending"`
3. Verify Celery task is triggered for embedding generation
4. Check Redis cache for frequently accessed memories
5. Retrieve memory by ID (check cache hit)
6. Update memory content (verify embedding regeneration triggered)
7. Delete memory
8. List all memories for user

**Test Script:**
```bash
# Create memory
curl -X POST http://localhost:8000/api/v1/memories \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Meeting with John about Q4 planning. Key decisions: increase marketing budget by 20%, hire 2 new engineers.",
    "memory_type": "meeting_note",
    "metadata": {
      "participants": ["John", "Sarah"],
      "date": "2024-01-15"
    }
  }'
# Response includes: "embedding_status": "pending"

# Check Celery task was queued
celery -A tasks.celery_app inspect active

# Verify in database (embedding_status should update)
psql -c "SELECT id, embedding_status, embedding_updated_at FROM memories WHERE user_id = '<user_id>';"

# Retrieve by ID (first call populates cache)
curl http://localhost:8000/api/v1/memories/<memory_id> \
  -H "Authorization: Bearer <token>"

# Verify Redis cache
redis-cli GET "memory:<memory_id>"

# List all
curl "http://localhost:8000/api/v1/memories?page=1&per_page=10" \
  -H "Authorization: Bearer <token>"

# Update memory (triggers embedding regeneration)
curl -X PATCH http://localhost:8000/api/v1/memories/<memory_id> \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"content": "Updated content"}'
# Response includes: "embedding_status": "pending"
```

---

## Requirements Included

### Parent Requirements
| ID | Description | Children |
|----|-------------|----------|
| REQ_001 | AI-powered messenger with persistent memory | 17 |
| REQ_006 | EverMemOS memory framework | 17 |
| REQ_002 | Capture, store, retrieve organizational knowledge | 17 |

### Implementation Requirements

**Memory Storage Requirements**
- REQ_001.2.1: Create OMNE memory storage system
- REQ_001.2.2: Ingest data from chat messages
- REQ_001.2.3: Query functionality for retrieving information
- REQ_001.2.4: Validation checks for data integrity
- REQ_001.2.5: Security measures for storage protection

**Group 016 - Memory (5 requirements)**
- REQ_006.2.1: Define core memory architecture
- REQ_006.2.2: Develop core OMNE framework
- REQ_006.2.3: Create data model for memories
- REQ_014.2.1: Extract memories from conversations
- REQ_014.2.2: Store extracted memories

---

## Database Schema

> **Note:** The complete `memories` table schema is defined in **Sprint 01: Database & Schema Foundation**.
> This sprint implements the service layer and API endpoints for that schema.

### Schema Reference (from Sprint 01)

```sql
-- See Sprint 01 for complete table definition
-- Key fields used by this sprint:
--   id, user_id, content, memory_type, source, source_id
--   title, tags, metadata
--   embedding, embedding_status, embedding_model, embedding_updated_at
--   created_at, updated_at, accessed_at, deleted_at
--   conversation_id
```

### Additional Indexes (if not in Sprint 01)

```sql
-- Composite index for efficient user + status queries
CREATE INDEX idx_memories_user_embedding_status
    ON memories(user_id, embedding_status)
    WHERE deleted_at IS NULL;

-- Index for pending embeddings (for batch processing)
CREATE INDEX idx_memories_pending_embeddings
    ON memories(created_at)
    WHERE embedding_status = 'pending' AND deleted_at IS NULL;
```

---

## Memory Data Model

```python
from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field

class MemoryType(str, Enum):
    NOTE = "note"
    MEETING = "meeting"
    TASK = "task"
    INSIGHT = "insight"
    DECISION = "decision"
    CONTACT = "contact"
    FILE = "file"
    CUSTOM = "custom"

class MemorySource(str, Enum):
    MANUAL = "manual"
    CHAT = "chat"
    FILE = "file"
    INTEGRATION = "integration"
    AI_EXTRACTED = "ai_extracted"

class EmbeddingStatus(str, Enum):
    """Status of the embedding generation for a memory."""
    PENDING = "pending"      # Queued for embedding generation
    PROCESSING = "processing"  # Currently being processed
    COMPLETED = "completed"   # Embedding successfully generated
    FAILED = "failed"        # Embedding generation failed

class Memory(BaseModel):
    id: UUID
    user_id: UUID
    content: str                    # Main content
    memory_type: MemoryType         # note, meeting, task, insight, etc.
    source: MemorySource            # manual, chat, file, integration
    source_id: Optional[str]        # Reference to source (message_id, file_id)

    # Metadata
    title: Optional[str]
    tags: List[str] = []
    metadata: Dict[str, Any] = {}

    # Embedding status
    embedding_status: EmbeddingStatus = EmbeddingStatus.PENDING
    embedding_model: Optional[str] = None
    embedding_updated_at: Optional[datetime] = None

    # Timestamps
    created_at: datetime
    updated_at: datetime
    accessed_at: datetime           # For relevance scoring

    # Relationships
    related_memories: List[UUID] = []
    conversation_id: Optional[UUID]

class MemoryCreate(BaseModel):
    content: str = Field(..., max_length=50000)
    memory_type: MemoryType = MemoryType.NOTE
    source: MemorySource = MemorySource.MANUAL
    source_id: Optional[str] = None
    title: Optional[str] = Field(None, max_length=500)
    tags: List[str] = []
    metadata: Dict[str, Any] = {}
    conversation_id: Optional[UUID] = None

class MemoryUpdate(BaseModel):
    content: Optional[str] = Field(None, max_length=50000)
    title: Optional[str] = Field(None, max_length=500)
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

class MemoryResponse(Memory):
    """Response model with embedding_status visible to client."""
    pass
```

---

## API Endpoints

```yaml
# Create Memory
POST /api/v1/memories
  Request:
    content: string (required, max 50000 chars)
    memory_type: string (default: "note")
    title: string (optional, max 500 chars)
    tags: string[] (optional)
    metadata: object (optional)
  Response:
    id: uuid
    content: string
    memory_type: string
    embedding_status: string  # "pending" on create
    created_at: timestamp
  Side Effects:
    - Triggers Celery task: generate_embedding(memory_id)
    - Invalidates user memory list cache

# List Memories
GET /api/v1/memories
  Query:
    page: int (default: 1)
    per_page: int (default: 20, max: 100)
    memory_type: string (filter)
    tags: string (comma-separated, filter)
    source: string (filter)
    embedding_status: string (filter: pending, processing, completed, failed)
    created_after: datetime (filter)
    created_before: datetime (filter)
    sort_by: string (created_at, updated_at, accessed_at)
    sort_order: string (asc, desc)
  Response:
    data: Memory[] (includes embedding_status)
    meta: { page, per_page, total, total_pages }

# Get Memory
GET /api/v1/memories/{id}
  Response: Memory (includes embedding_status)
  Caching:
    - Cache key: "memory:{id}"
    - TTL: 5 minutes
    - Updates accessed_at timestamp

# Update Memory
PATCH /api/v1/memories/{id}
  Request:
    content: string (optional)
    title: string (optional)
    tags: string[] (optional)
    metadata: object (optional)
  Response: Memory (embedding_status reset to "pending" if content changed)
  Side Effects:
    - If content changed: triggers generate_embedding task
    - Invalidates cache: "memory:{id}"

# Delete Memory
DELETE /api/v1/memories/{id}
  Response: 204 No Content
  Side Effects:
    - Invalidates cache: "memory:{id}"
    - Soft delete (sets deleted_at)

# Bulk Operations
POST /api/v1/memories/bulk
  Request:
    memories: MemoryCreate[] (max 100)
  Response:
    created: int
    failed: int
    errors: Error[]
  Side Effects:
    - Triggers generate_embedding for each created memory

# Retry Failed Embeddings
POST /api/v1/memories/{id}/retry-embedding
  Response:
    id: uuid
    embedding_status: "pending"
  Side Effects:
    - Queues new embedding generation task
```

---

## Background Tasks

### Embedding Generation Task

```python
# tasks/workers/embedding.py
from celery import shared_task
from tasks.base import BaseTask
from tasks.celery_app import celery_app
from database.connection import get_db_session
from cache.redis_client import redis_client
import logging

logger = logging.getLogger(__name__)

@celery_app.task(
    base=BaseTask,
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    queue="high_priority"
)
def generate_embedding(self, memory_id: str):
    """
    Generate embedding for a memory.

    Process:
    1. Update status to 'processing'
    2. Fetch memory content
    3. Call embedding API (OpenAI, Anthropic, etc.)
    4. Store embedding vector in database
    5. Update status to 'completed'
    6. Invalidate cache
    """
    try:
        with get_db_session() as db:
            # Update status to processing
            memory = db.query(Memory).filter(Memory.id == memory_id).first()
            if not memory:
                logger.warning(f"Memory {memory_id} not found")
                return

            memory.embedding_status = "processing"
            db.commit()

            # Generate embedding using configured provider (see EmbeddingProvider below)
            embedding_provider = get_embedding_provider()
            embedding_vector = embedding_provider.generate(memory.content)

            # Update memory with embedding
            memory.embedding = embedding_vector
            memory.embedding_status = "completed"
            memory.embedding_model = "text-embedding-3-small"  # or configured model
            memory.embedding_updated_at = datetime.utcnow()
            db.commit()

            # Invalidate cache (synchronous Redis call - Celery tasks are not async)
            redis_client.delete(f"memory:{memory_id}")

            logger.info(f"Embedding generated for memory {memory_id}")

    except Exception as exc:
        # Update status to failed
        with get_db_session() as db:
            memory = db.query(Memory).filter(Memory.id == memory_id).first()
            if memory:
                memory.embedding_status = "failed"
                db.commit()

        logger.error(f"Embedding generation failed for {memory_id}: {exc}")
        raise self.retry(exc=exc)


@celery_app.task(base=BaseTask, queue="low_priority")
def process_pending_embeddings(batch_size: int = 50):
    """
    Batch process memories with pending embeddings.
    Scheduled task to catch any missed embeddings.
    """
    with get_db_session() as db:
        pending = db.query(Memory)\
            .filter(Memory.embedding_status == "pending")\
            .filter(Memory.deleted_at.is_(None))\
            .order_by(Memory.created_at)\
            .limit(batch_size)\
            .all()

        for memory in pending:
            generate_embedding.delay(str(memory.id))

        logger.info(f"Queued {len(pending)} pending embeddings")


@celery_app.task(base=BaseTask, queue="low_priority")
def retry_failed_embeddings(max_age_hours: int = 24):
    """
    Retry failed embedding generations that are within max_age.
    """
    cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)

    with get_db_session() as db:
        failed = db.query(Memory)\
            .filter(Memory.embedding_status == "failed")\
            .filter(Memory.updated_at >= cutoff)\
            .filter(Memory.deleted_at.is_(None))\
            .all()

        for memory in failed:
            memory.embedding_status = "pending"
            db.commit()
            generate_embedding.delay(str(memory.id))

        logger.info(f"Retrying {len(failed)} failed embeddings")
```

### Celery Beat Schedule (Periodic Tasks)

```python
# tasks/celery_app.py (additions)
from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    "process-pending-embeddings": {
        "task": "tasks.workers.embedding.process_pending_embeddings",
        "schedule": crontab(minute="*/5"),  # Every 5 minutes
        "kwargs": {"batch_size": 50},
    },
    "retry-failed-embeddings": {
        "task": "tasks.workers.embedding.retry_failed_embeddings",
        "schedule": crontab(hour="*/6"),  # Every 6 hours
        "kwargs": {"max_age_hours": 24},
    },
}
```

---

## Embedding Provider Abstraction

> **Note:** This provides the embedding generation interface. Sprint 06 extends this with vector search capabilities.

```python
# services/embedding/provider.py
from abc import ABC, abstractmethod
from typing import List
import os
import openai
from pydantic_settings import BaseSettings

class EmbeddingSettings(BaseSettings):
    """Embedding provider configuration."""
    provider: str = "openai"  # openai, local, cohere
    openai_api_key: str = ""
    model_name: str = "text-embedding-3-small"
    dimension: int = 1536  # Must match database VECTOR dimension

    class Config:
        env_prefix = "EMBEDDING_"


class EmbeddingProvider(ABC):
    """Abstract base class for embedding providers."""

    @abstractmethod
    def generate(self, text: str) -> List[float]:
        """Generate embedding vector for text."""
        pass

    @abstractmethod
    def generate_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Return the embedding dimension."""
        pass


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """OpenAI embedding provider (text-embedding-3-small = 1536 dims)."""

    def __init__(self, settings: EmbeddingSettings):
        self.settings = settings
        self.client = openai.OpenAI(api_key=settings.openai_api_key)
        self._dimension = settings.dimension

    def generate(self, text: str) -> List[float]:
        response = self.client.embeddings.create(
            model=self.settings.model_name,
            input=text
        )
        return response.data[0].embedding

    def generate_batch(self, texts: List[str]) -> List[List[float]]:
        response = self.client.embeddings.create(
            model=self.settings.model_name,
            input=texts
        )
        return [item.embedding for item in response.data]

    @property
    def dimension(self) -> int:
        return self._dimension


# Factory function
_provider_instance = None

def get_embedding_provider() -> EmbeddingProvider:
    """Get singleton embedding provider instance."""
    global _provider_instance
    if _provider_instance is None:
        settings = EmbeddingSettings()
        if settings.provider == "openai":
            _provider_instance = OpenAIEmbeddingProvider(settings)
        else:
            raise ValueError(f"Unsupported provider: {settings.provider}")
    return _provider_instance
```

### Dimension Validation

```python
# services/embedding/validation.py
def validate_embedding_dimension(embedding: List[float], expected: int = 1536) -> bool:
    """
    Validate embedding dimension matches database schema.

    IMPORTANT: The database VECTOR column is defined as VECTOR(1536) in Sprint 01.
    If using a different embedding model, you must:
    1. Create a migration to alter the column dimension
    2. Re-embed all existing memories
    3. Update this validation
    """
    if len(embedding) != expected:
        raise ValueError(
            f"Embedding dimension mismatch: got {len(embedding)}, expected {expected}. "
            f"Ensure EMBEDDING_DIMENSION matches database schema."
        )
    return True
```

---

## Redis Caching Strategy

### Cache Keys

| Key Pattern | Purpose | TTL |
|-------------|---------|-----|
| `memory:{id}` | Single memory cache | 5 minutes |
| `memories:user:{user_id}:list:{hash}` | List query cache | 2 minutes |
| `memories:user:{user_id}:count` | Total memory count | 2 minutes |
| `memories:user:{user_id}:recent` | Recent memories (top 10) | 1 minute |

### Caching Implementation

```python
# memories/cache.py
from cache.decorators import cache, invalidate_cache
from cache.redis_client import redis_client
import json
from typing import Optional
from uuid import UUID

class MemoryCache:
    """Redis caching layer for memories."""

    MEMORY_TTL = 300  # 5 minutes
    LIST_TTL = 120    # 2 minutes
    COUNT_TTL = 120   # 2 minutes

    @staticmethod
    def memory_key(memory_id: UUID) -> str:
        return f"memory:{memory_id}"

    @staticmethod
    def list_key(user_id: UUID, query_hash: str) -> str:
        return f"memories:user:{user_id}:list:{query_hash}"

    @staticmethod
    def count_key(user_id: UUID) -> str:
        return f"memories:user:{user_id}:count"

    @staticmethod
    def recent_key(user_id: UUID) -> str:
        return f"memories:user:{user_id}:recent"

    async def get_memory(self, memory_id: UUID) -> Optional[dict]:
        """Get memory from cache."""
        key = self.memory_key(memory_id)
        data = await redis_client.get(key)
        return json.loads(data) if data else None

    async def set_memory(self, memory_id: UUID, memory_data: dict):
        """Cache a memory."""
        key = self.memory_key(memory_id)
        await redis_client.set(key, json.dumps(memory_data, default=str), self.MEMORY_TTL)

    async def invalidate_memory(self, memory_id: UUID):
        """Invalidate single memory cache."""
        await redis_client.delete(self.memory_key(memory_id))

    async def invalidate_user_lists(self, user_id: UUID):
        """Invalidate all list caches for a user."""
        pattern = f"memories:user:{user_id}:*"
        await redis_client.delete_pattern(pattern)

    async def invalidate_all_for_user(self, user_id: UUID, memory_id: UUID):
        """Invalidate both specific memory and user list caches."""
        await self.invalidate_memory(memory_id)
        await self.invalidate_user_lists(user_id)


memory_cache = MemoryCache()
```

### Service Layer with Caching

```python
# memories/service.py
from memories.cache import memory_cache
from memories.repository import MemoryRepository
from tasks.workers.embedding import generate_embedding
from datetime import datetime

class MemoryService:
    def __init__(self, repository: MemoryRepository):
        self.repository = repository

    async def create_memory(self, user_id: UUID, data: MemoryCreate) -> Memory:
        """Create memory and trigger embedding generation."""
        memory = await self.repository.create(
            user_id=user_id,
            **data.dict(),
            embedding_status="pending"
        )

        # Invalidate user list cache
        await memory_cache.invalidate_user_lists(user_id)

        # Trigger async embedding generation
        generate_embedding.delay(str(memory.id))

        return memory

    async def get_memory(self, memory_id: UUID, user_id: UUID) -> Optional[Memory]:
        """Get memory with caching."""
        # Try cache first
        cached = await memory_cache.get_memory(memory_id)
        if cached and cached.get("user_id") == str(user_id):
            return Memory(**cached)

        # Fetch from database
        memory = await self.repository.get_by_id(memory_id, user_id)
        if memory:
            # Update accessed_at
            await self.repository.update_accessed_at(memory_id)
            # Cache the result
            await memory_cache.set_memory(memory_id, memory.dict())

        return memory

    async def update_memory(
        self,
        memory_id: UUID,
        user_id: UUID,
        data: MemoryUpdate
    ) -> Optional[Memory]:
        """Update memory, regenerate embedding if content changed."""
        existing = await self.repository.get_by_id(memory_id, user_id)
        if not existing:
            return None

        update_data = data.dict(exclude_unset=True)

        # If content changed, reset embedding status
        if "content" in update_data and update_data["content"] != existing.content:
            update_data["embedding_status"] = "pending"
            update_data["embedding"] = None
            update_data["embedding_updated_at"] = None

        memory = await self.repository.update(memory_id, **update_data)

        # Invalidate caches
        await memory_cache.invalidate_all_for_user(user_id, memory_id)

        # Trigger embedding regeneration if content changed
        if update_data.get("embedding_status") == "pending":
            generate_embedding.delay(str(memory_id))

        return memory

    async def delete_memory(self, memory_id: UUID, user_id: UUID) -> bool:
        """Soft delete memory and invalidate cache."""
        result = await self.repository.soft_delete(memory_id, user_id)

        if result:
            await memory_cache.invalidate_all_for_user(user_id, memory_id)

        return result

    async def retry_embedding(self, memory_id: UUID, user_id: UUID) -> Optional[Memory]:
        """Retry failed embedding generation."""
        memory = await self.repository.get_by_id(memory_id, user_id)
        if not memory or memory.embedding_status not in ["failed", "pending"]:
            return None

        await self.repository.update(memory_id, embedding_status="pending")
        generate_embedding.delay(str(memory_id))

        await memory_cache.invalidate_memory(memory_id)

        return await self.repository.get_by_id(memory_id, user_id)
```

---

## Tasks

### Data Model
- [ ] Create Memory SQLAlchemy model (reference Sprint 01 schema)
- [ ] Create Pydantic schemas for API (MemoryCreate, MemoryUpdate, MemoryResponse)
- [ ] Add EmbeddingStatus enum
- [ ] Implement memory type and source enums

### CRUD Operations
- [ ] Implement create memory service (with Celery task trigger)
- [ ] Implement list memories with filtering (including embedding_status filter)
- [ ] Implement get single memory (with caching)
- [ ] Implement update memory (with embedding regeneration)
- [ ] Implement soft delete memory
- [ ] Add bulk create endpoint

### Background Tasks (Celery)
- [ ] Implement generate_embedding task
- [ ] Add embedding status update flow (pending -> processing -> completed/failed)
- [ ] Configure retry logic for failed embeddings
- [ ] Add periodic task for processing pending embeddings
- [ ] Add periodic task for retrying failed embeddings

### Caching (Redis)
- [ ] Implement MemoryCache class
- [ ] Add cache-aside pattern for get_memory
- [ ] Implement cache invalidation on create/update/delete
- [ ] Add user list cache invalidation
- [ ] Configure appropriate TTLs

### Validation & Security
- [ ] Validate memory content (max length, sanitization)
- [ ] Ensure user can only access own memories
- [ ] Add rate limiting for memory creation
- [ ] Implement soft delete option

### Performance
- [ ] Add additional indexes for embedding_status queries
- [ ] Implement cursor-based pagination option
- [ ] Optimize cache key generation

---

## Acceptance Criteria

1. Can create memory with content and type
2. Memory creation triggers async embedding generation
3. Embedding status tracks: pending -> processing -> completed/failed
4. Memories are isolated per user (can't see others' memories)
5. List endpoint supports pagination and filtering (including embedding_status)
6. Frequently accessed memories are cached in Redis
7. Update only modifies provided fields
8. Content update triggers embedding regeneration
9. Delete removes memory (soft delete) and invalidates cache
10. Bulk create handles partial failures gracefully
11. Memory creation rate limited to 100/minute
12. Content validation prevents XSS/injection
13. Failed embeddings can be retried via API
14. Periodic tasks process any missed/failed embeddings

---

## Files to Create

```
src/
  memories/
    __init__.py
    models.py          # SQLAlchemy models (extends Sprint 01)
    schemas.py         # Pydantic schemas (with EmbeddingStatus)
    service.py         # Business logic (with caching + task triggers)
    router.py          # API endpoints
    repository.py      # Database operations
    cache.py           # Redis caching layer

  tasks/
    workers/
      embedding.py     # Embedding generation tasks
```

---

## Related Requirement Groups

- Group 008: Semantic: Semantic Search
- Group 012: Semantic: Machine Learning
- Group 015: Semantic: Data Storage
- Group 016: Semantic: Memory
