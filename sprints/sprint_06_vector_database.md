# Sprint 06: Vector Search & Embeddings Service

**Phase:** 2 - Memory System
**Focus:** Semantic search services, hybrid search, and embedding pipeline
**Dependencies:** Sprint 01 (Database Schema), Sprint 05 (Memory Storage)

---

## Testable Deliverable

**Human Test:**
1. Create several memories with different content
2. Verify embeddings are generated asynchronously (check embedding_status)
3. Search using natural language query
4. Verify semantically similar results are returned
5. Results ranked by relevance score
6. Verify cached results return faster on repeated queries

**Test Script:**
```bash
# Create test memories
curl -X POST http://localhost:8000/api/v1/memories \
  -H "Authorization: Bearer <token>" \
  -d '{"content": "Q4 budget meeting with finance team. Decided to increase marketing spend."}'

curl -X POST http://localhost:8000/api/v1/memories \
  -H "Authorization: Bearer <token>" \
  -d '{"content": "Engineering standup: Sprint planning for new authentication feature."}'

curl -X POST http://localhost:8000/api/v1/memories \
  -H "Authorization: Bearer <token>" \
  -d '{"content": "Lunch with investor. Discussed Series A funding timeline."}'

# Wait for embedding generation (check status)
curl "http://localhost:8000/api/v1/memories/{id}" \
  -H "Authorization: Bearer <token>"
# embedding_status should transition: pending -> processing -> completed

# Semantic search
curl "http://localhost:8000/api/v1/memories/search?q=financial%20discussions" \
  -H "Authorization: Bearer <token>"

# Should return: Q4 budget meeting AND investor lunch (both financially related)
# Should NOT return: Engineering standup (not financially related)

# Hybrid search (vector + full-text)
curl "http://localhost:8000/api/v1/memories/search?q=budget&mode=hybrid" \
  -H "Authorization: Bearer <token>"

# Verify caching (second request should be faster)
time curl "http://localhost:8000/api/v1/memories/search?q=financial%20discussions" \
  -H "Authorization: Bearer <token>"
```

---

## Schema Reference

> **Note:** The database schema for vector embeddings is defined in **Sprint 01 (Database Schema)**.
> This sprint focuses on the **service layer** implementation.

### ⚠️ Vector Dimension Limitation

> **IMPORTANT:** The database schema in Sprint 01 defines `embedding VECTOR(1536)` which is **hardcoded**.
> This dimension matches OpenAI's `text-embedding-3-small` model. If you need to use a different
> embedding model with a different dimension (e.g., 384 for local models, 3072 for text-embedding-3-large),
> you must create a database migration. See **Migration Strategy** section below.

### Relevant Schema from Sprint 01:

```sql
-- From Sprint 01: memories table with embedding fields
-- NOTE: VECTOR(1536) is fixed - see migration strategy for changing dimensions
embedding VECTOR(1536),
embedding_status VARCHAR(20) DEFAULT 'pending',  -- pending, processing, completed, failed
embedding_model VARCHAR(100),
embedding_updated_at TIMESTAMP,

-- From Sprint 01: HNSW index for fast similarity search
CREATE INDEX idx_memories_embedding ON memories
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- From Sprint 01: Full-text search index on messages (for hybrid search)
CREATE INDEX idx_messages_content_search ON messages
    USING GIN(to_tsvector('english', content));
```

---

## Requirements Included

### Parent Requirements
| ID | Description | Children |
|----|-------------|----------|
| REQ_169 | Vector database for memory storage and retrieval | 18 |
| REQ_018 | Searchable memory indexes for fast retrieval | 17 |
| REQ_182 | RAG for memory-enhanced responses | 18 |

### Implementation Requirements

**Group 008 - Semantic Search (3 requirements)**
- REQ_169.2.1: Set up vector database (pgvector) - **See Sprint 01**
- REQ_169.2.2: Implement embedding generation pipeline
- REQ_169.2.3: Create similarity search functions

**Search & Retrieval Requirements**
- REQ_001.2.3: Query functionality for relevant information
- REQ_018.2.1: Create searchable indexes - **See Sprint 01**
- REQ_018.2.2: Implement fast retrieval mechanisms

---

## Architecture

```
[User Query]
    |
    v
[Redis Cache Check] --> [Cache Hit] --> [Return Cached Results]
    |
    [Cache Miss]
    |
    v
[Embedding Model] -> [Query Vector]
    |
    v
[Hybrid Search Engine]
    |
    +---> [pgvector Similarity Search]
    |
    +---> [PostgreSQL Full-Text Search]
    |
    v
[Score Fusion & Ranking]
    |
    v
[Cache Results in Redis]
    |
    v
[Return Ranked Results]
```

### Components

1. **Embedding Service**: Converts text to vectors using OpenAI/local model
2. **Embedding Worker (Celery)**: Background processing for batch embeddings
3. **Search Service**: Similarity search with filtering and hybrid mode
4. **Cache Layer (Redis)**: TTL-based caching for search results
5. **Score Fusion**: Combines vector similarity with full-text relevance

---

## Embedding Configuration

```python
from pydantic_settings import BaseSettings
from typing import Literal

class EmbeddingConfig(BaseSettings):
    """Embedding service configuration."""

    # Model settings
    provider: Literal["openai", "local", "cohere"] = "openai"
    model_name: str = "text-embedding-3-small"  # 1536 dimensions
    embedding_dimension: int = 1536

    # For local: sentence-transformers/all-MiniLM-L6-v2 (384 dims)
    local_model_name: str = "all-MiniLM-L6-v2"
    local_embedding_dimension: int = 384

    # Processing settings
    batch_size: int = 100
    max_tokens: int = 8191  # OpenAI model limit
    max_retries: int = 3
    retry_delay: float = 1.0

    # Celery worker settings
    worker_concurrency: int = 4
    processing_interval: int = 5  # seconds

    class Config:
        env_prefix = "EMBEDDING_"


class SearchConfig(BaseSettings):
    """Search service configuration."""

    # Similarity thresholds
    default_threshold: float = 0.7
    strict_threshold: float = 0.85
    relaxed_threshold: float = 0.5

    # Result limits
    default_limit: int = 10
    max_limit: int = 50

    # Hybrid search weights
    vector_weight: float = 0.7
    fulltext_weight: float = 0.3

    # Cache settings (Redis)
    cache_enabled: bool = True
    cache_ttl: int = 300  # 5 minutes
    cache_prefix: str = "search:"

    class Config:
        env_prefix = "SEARCH_"
```

---

## Vector Dimension Migration Strategy

> **When to use this:** If you need to change from OpenAI (1536 dims) to another provider
> (e.g., local models with 384 dims, or text-embedding-3-large with 3072 dims).

### Migration Steps

```python
# migrations/versions/xxx_change_embedding_dimension.py
"""
Change embedding vector dimension.

Revision ID: xxx
Revises: previous_revision
Create Date: YYYY-MM-DD

IMPORTANT: This migration will:
1. Drop existing embeddings (data loss!)
2. Alter the column dimension
3. Require re-embedding all memories

Run during maintenance window with embedding workers stopped.
"""

from alembic import op
import sqlalchemy as sa

# Target dimension (change this based on your embedding provider)
NEW_DIMENSION = 384  # e.g., for all-MiniLM-L6-v2

def upgrade():
    # 1. Drop the HNSW index (required before altering)
    op.drop_index('idx_memories_embedding', table_name='memories')

    # 2. Clear existing embeddings (they're incompatible with new dimension)
    op.execute("""
        UPDATE memories
        SET embedding = NULL,
            embedding_status = 'pending',
            embedding_model = NULL,
            embedding_updated_at = NULL
    """)

    # 3. Alter the column dimension
    op.execute(f"""
        ALTER TABLE memories
        ALTER COLUMN embedding TYPE vector({NEW_DIMENSION})
    """)

    # 4. Recreate the HNSW index
    op.execute(f"""
        CREATE INDEX idx_memories_embedding ON memories
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
    """)


def downgrade():
    # Reverse the process for 1536 dimensions
    op.drop_index('idx_memories_embedding', table_name='memories')
    op.execute("UPDATE memories SET embedding = NULL, embedding_status = 'pending'")
    op.execute("ALTER TABLE memories ALTER COLUMN embedding TYPE vector(1536)")
    op.execute("""
        CREATE INDEX idx_memories_embedding ON memories
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
    """)
```

### Post-Migration Re-Embedding

```bash
# After migration, re-embed all memories:
celery -A tasks.celery_app call tasks.workers.embedding.process_pending_embeddings \
  --kwargs='{"batch_size": 100}'

# Monitor progress:
SELECT embedding_status, COUNT(*) FROM memories GROUP BY embedding_status;
```

### Supported Embedding Dimensions

| Provider | Model | Dimensions | Notes |
|----------|-------|------------|-------|
| OpenAI | text-embedding-3-small | 1536 | **Default** (Sprint 01 schema) |
| OpenAI | text-embedding-3-large | 3072 | Higher quality, more storage |
| OpenAI | text-embedding-ada-002 | 1536 | Legacy model |
| Local | all-MiniLM-L6-v2 | 384 | Fast, good quality, no API cost |
| Local | all-mpnet-base-v2 | 768 | Higher quality local model |
| Cohere | embed-english-v3.0 | 1024 | Good multilingual support |

---

## Embedding Generation Service

### Celery Worker for Batch Embedding Generation

```python
# src/embeddings/worker.py
from celery import Celery
from sqlalchemy import select, update
from datetime import datetime
from typing import List
import asyncio

from src.database.connection import get_async_session
from src.database.models.memory import Memory
from src.embeddings.service import EmbeddingService, get_embedding_service
from src.core.config import settings

celery_app = Celery(
    "embedding_worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    task_track_started=True,
    task_time_limit=300,  # 5 minutes max per task
)


@celery_app.task(bind=True, max_retries=3)
def process_pending_embeddings(self, batch_size: int = 100):
    """
    Celery task to process memories with pending embeddings.
    Runs on schedule or triggered after memory creation.
    """
    return asyncio.run(_process_pending_embeddings_async(batch_size))


async def _process_pending_embeddings_async(batch_size: int) -> dict:
    """Process pending embeddings asynchronously."""
    embedding_service = get_embedding_service()

    async with get_async_session() as session:
        # Fetch pending memories
        stmt = (
            select(Memory)
            .where(Memory.embedding_status == "pending")
            .where(Memory.deleted_at.is_(None))
            .limit(batch_size)
        )
        result = await session.execute(stmt)
        memories = result.scalars().all()

        if not memories:
            return {"processed": 0, "status": "no_pending"}

        # Mark as processing
        memory_ids = [m.id for m in memories]
        await session.execute(
            update(Memory)
            .where(Memory.id.in_(memory_ids))
            .values(embedding_status="processing")
        )
        await session.commit()

        # Generate embeddings in batch
        texts = [m.content for m in memories]
        try:
            embeddings = await embedding_service.embed_batch(texts)

            # Update memories with embeddings
            for memory, embedding in zip(memories, embeddings):
                memory.embedding = embedding
                memory.embedding_status = "completed"
                memory.embedding_model = embedding_service.model_name
                memory.embedding_updated_at = datetime.utcnow()

            await session.commit()

            return {
                "processed": len(memories),
                "status": "success",
                "memory_ids": [str(m.id) for m in memories]
            }

        except Exception as e:
            # Mark as failed
            await session.execute(
                update(Memory)
                .where(Memory.id.in_(memory_ids))
                .values(embedding_status="failed")
            )
            await session.commit()
            raise


@celery_app.task
def embed_single_memory(memory_id: str):
    """Process a single memory's embedding (triggered on creation)."""
    return asyncio.run(_embed_single_memory_async(memory_id))


async def _embed_single_memory_async(memory_id: str) -> dict:
    """Embed a single memory asynchronously."""
    embedding_service = get_embedding_service()

    async with get_async_session() as session:
        stmt = select(Memory).where(Memory.id == memory_id)
        result = await session.execute(stmt)
        memory = result.scalar_one_or_none()

        if not memory:
            return {"status": "not_found", "memory_id": memory_id}

        if memory.embedding_status == "completed":
            return {"status": "already_completed", "memory_id": memory_id}

        memory.embedding_status = "processing"
        await session.commit()

        try:
            embedding = await embedding_service.embed(memory.content)
            memory.embedding = embedding
            memory.embedding_status = "completed"
            memory.embedding_model = embedding_service.model_name
            memory.embedding_updated_at = datetime.utcnow()
            await session.commit()

            return {"status": "success", "memory_id": memory_id}

        except Exception as e:
            memory.embedding_status = "failed"
            await session.commit()
            return {"status": "failed", "memory_id": memory_id, "error": str(e)}


# Celery Beat schedule for periodic processing
celery_app.conf.beat_schedule = {
    "process-pending-embeddings": {
        "task": "src.embeddings.worker.process_pending_embeddings",
        "schedule": 30.0,  # Every 30 seconds
        "args": (100,),    # batch_size
    },
}
```

---

## Search Caching Strategy

### Redis TTL for Vector Search Results

```python
# src/search/cache.py
import hashlib
import json
from typing import Optional, List, Any
from datetime import timedelta
import redis.asyncio as redis

from src.core.config import settings
from src.search.schemas import SearchResult


class SearchCache:
    """Redis-based caching for vector search results."""

    def __init__(
        self,
        redis_url: str = None,
        ttl: int = 300,  # 5 minutes default
        prefix: str = "search:"
    ):
        self.redis_url = redis_url or settings.REDIS_URL
        self.ttl = ttl
        self.prefix = prefix
        self._client: Optional[redis.Redis] = None

    async def get_client(self) -> redis.Redis:
        """Get or create Redis client."""
        if self._client is None:
            self._client = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
        return self._client

    def _generate_cache_key(
        self,
        user_id: str,
        query: str,
        filters: dict,
        mode: str = "vector"
    ) -> str:
        """Generate deterministic cache key from search parameters."""
        key_data = {
            "user_id": user_id,
            "query": query.lower().strip(),
            "filters": json.dumps(filters, sort_keys=True),
            "mode": mode
        }
        key_hash = hashlib.sha256(
            json.dumps(key_data, sort_keys=True).encode()
        ).hexdigest()[:16]

        return f"{self.prefix}{user_id}:{key_hash}"

    async def get(
        self,
        user_id: str,
        query: str,
        filters: dict = None,
        mode: str = "vector"
    ) -> Optional[List[dict]]:
        """Retrieve cached search results."""
        client = await self.get_client()
        key = self._generate_cache_key(user_id, query, filters or {}, mode)

        cached = await client.get(key)
        if cached:
            return json.loads(cached)
        return None

    async def set(
        self,
        user_id: str,
        query: str,
        results: List[dict],
        filters: dict = None,
        mode: str = "vector",
        ttl: int = None
    ) -> None:
        """Cache search results with TTL."""
        client = await self.get_client()
        key = self._generate_cache_key(user_id, query, filters or {}, mode)

        await client.setex(
            key,
            ttl or self.ttl,
            json.dumps(results)
        )

    async def invalidate_user_cache(self, user_id: str) -> int:
        """Invalidate all cached searches for a user (on memory update/delete)."""
        client = await self.get_client()
        pattern = f"{self.prefix}{user_id}:*"

        keys = []
        async for key in client.scan_iter(match=pattern):
            keys.append(key)

        if keys:
            return await client.delete(*keys)
        return 0

    async def invalidate_all(self) -> int:
        """Invalidate all search cache (admin operation)."""
        client = await self.get_client()
        pattern = f"{self.prefix}*"

        keys = []
        async for key in client.scan_iter(match=pattern):
            keys.append(key)

        if keys:
            return await client.delete(*keys)
        return 0

    async def get_stats(self) -> dict:
        """Get cache statistics."""
        client = await self.get_client()
        pattern = f"{self.prefix}*"

        count = 0
        async for _ in client.scan_iter(match=pattern):
            count += 1

        info = await client.info("memory")

        return {
            "cached_queries": count,
            "redis_memory_used": info.get("used_memory_human", "unknown"),
            "ttl_seconds": self.ttl
        }


# Singleton instance
_search_cache: Optional[SearchCache] = None


def get_search_cache() -> SearchCache:
    """Get or create search cache singleton."""
    global _search_cache
    if _search_cache is None:
        _search_cache = SearchCache(
            ttl=settings.SEARCH_CACHE_TTL,
            prefix=settings.SEARCH_CACHE_PREFIX
        )
    return _search_cache
```

---

## Hybrid Search

### Combining Vector Similarity with PostgreSQL Full-Text Search

```python
# src/search/hybrid.py
from typing import List, Optional, Tuple
from dataclasses import dataclass
from sqlalchemy import text, select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
import numpy as np

from src.database.models.memory import Memory
from src.embeddings.service import EmbeddingService
from src.search.schemas import SearchResult, SearchMode


@dataclass
class HybridSearchConfig:
    """Configuration for hybrid search scoring."""
    vector_weight: float = 0.7
    fulltext_weight: float = 0.3
    vector_threshold: float = 0.5
    fulltext_threshold: float = 0.1

    def normalize_weights(self):
        """Ensure weights sum to 1.0."""
        total = self.vector_weight + self.fulltext_weight
        self.vector_weight /= total
        self.fulltext_weight /= total


class HybridSearchService:
    """
    Hybrid search combining vector similarity and full-text search.

    Implements Reciprocal Rank Fusion (RRF) for score combination.
    """

    def __init__(
        self,
        embedding_service: EmbeddingService,
        config: HybridSearchConfig = None
    ):
        self.embedding_service = embedding_service
        self.config = config or HybridSearchConfig()
        self.config.normalize_weights()

    async def search(
        self,
        session: AsyncSession,
        user_id: str,
        query: str,
        mode: SearchMode = SearchMode.HYBRID,
        limit: int = 10,
        threshold: float = None,
        memory_type: str = None,
        tags: List[str] = None
    ) -> List[SearchResult]:
        """
        Perform hybrid search on memories.

        Args:
            session: Database session
            user_id: User ID for filtering
            query: Natural language search query
            mode: Search mode (vector, fulltext, hybrid)
            limit: Maximum results to return
            threshold: Minimum similarity score
            memory_type: Filter by memory type
            tags: Filter by tags

        Returns:
            List of SearchResult with combined scores
        """
        threshold = threshold or self.config.vector_threshold

        if mode == SearchMode.VECTOR:
            return await self._vector_search(
                session, user_id, query, limit, threshold, memory_type, tags
            )
        elif mode == SearchMode.FULLTEXT:
            return await self._fulltext_search(
                session, user_id, query, limit, memory_type, tags
            )
        else:  # HYBRID
            return await self._hybrid_search(
                session, user_id, query, limit, threshold, memory_type, tags
            )

    async def _vector_search(
        self,
        session: AsyncSession,
        user_id: str,
        query: str,
        limit: int,
        threshold: float,
        memory_type: str = None,
        tags: List[str] = None
    ) -> List[SearchResult]:
        """Pure vector similarity search."""
        # Generate query embedding
        query_embedding = await self.embedding_service.embed(query)

        # Build vector search query
        sql = text("""
            SELECT
                m.id,
                m.content,
                m.title,
                m.memory_type,
                m.tags,
                m.metadata,
                m.created_at,
                1 - (m.embedding <=> :query_embedding::vector) AS similarity_score
            FROM memories m
            WHERE
                m.user_id = :user_id
                AND m.deleted_at IS NULL
                AND m.embedding IS NOT NULL
                AND m.embedding_status = 'completed'
                AND (:memory_type IS NULL OR m.memory_type = :memory_type)
                AND 1 - (m.embedding <=> :query_embedding::vector) >= :threshold
            ORDER BY m.embedding <=> :query_embedding::vector
            LIMIT :limit
        """)

        result = await session.execute(
            sql,
            {
                "query_embedding": str(query_embedding),
                "user_id": user_id,
                "memory_type": memory_type,
                "threshold": threshold,
                "limit": limit
            }
        )

        rows = result.fetchall()
        return [
            SearchResult(
                memory_id=str(row.id),
                content=row.content,
                title=row.title,
                memory_type=row.memory_type,
                tags=row.tags or [],
                score=float(row.similarity_score),
                score_breakdown={"vector": float(row.similarity_score)},
                created_at=row.created_at
            )
            for row in rows
        ]

    async def _fulltext_search(
        self,
        session: AsyncSession,
        user_id: str,
        query: str,
        limit: int,
        memory_type: str = None,
        tags: List[str] = None
    ) -> List[SearchResult]:
        """Pure PostgreSQL full-text search."""
        # Convert query to tsquery format
        sql = text("""
            SELECT
                m.id,
                m.content,
                m.title,
                m.memory_type,
                m.tags,
                m.metadata,
                m.created_at,
                ts_rank_cd(
                    to_tsvector('english', m.content),
                    plainto_tsquery('english', :query)
                ) AS fulltext_score
            FROM memories m
            WHERE
                m.user_id = :user_id
                AND m.deleted_at IS NULL
                AND (:memory_type IS NULL OR m.memory_type = :memory_type)
                AND to_tsvector('english', m.content) @@ plainto_tsquery('english', :query)
            ORDER BY fulltext_score DESC
            LIMIT :limit
        """)

        result = await session.execute(
            sql,
            {
                "query": query,
                "user_id": user_id,
                "memory_type": memory_type,
                "limit": limit
            }
        )

        rows = result.fetchall()

        # Normalize fulltext scores (0-1 range)
        if rows:
            max_score = max(row.fulltext_score for row in rows) or 1.0
            return [
                SearchResult(
                    memory_id=str(row.id),
                    content=row.content,
                    title=row.title,
                    memory_type=row.memory_type,
                    tags=row.tags or [],
                    score=float(row.fulltext_score / max_score),
                    score_breakdown={"fulltext": float(row.fulltext_score / max_score)},
                    created_at=row.created_at
                )
                for row in rows
            ]
        return []

    async def _hybrid_search(
        self,
        session: AsyncSession,
        user_id: str,
        query: str,
        limit: int,
        threshold: float,
        memory_type: str = None,
        tags: List[str] = None
    ) -> List[SearchResult]:
        """
        Hybrid search using Reciprocal Rank Fusion (RRF).

        Combines vector similarity and full-text search results.
        """
        # Get results from both search methods (fetch more for fusion)
        fetch_limit = limit * 3

        vector_results = await self._vector_search(
            session, user_id, query, fetch_limit, threshold * 0.8, memory_type, tags
        )
        fulltext_results = await self._fulltext_search(
            session, user_id, query, fetch_limit, memory_type, tags
        )

        # Apply Reciprocal Rank Fusion
        rrf_scores = self._reciprocal_rank_fusion(
            vector_results,
            fulltext_results,
            k=60  # RRF constant
        )

        # Sort by fused score and limit
        sorted_results = sorted(
            rrf_scores.items(),
            key=lambda x: x[1]["score"],
            reverse=True
        )[:limit]

        # Build final results
        results = []
        for memory_id, score_data in sorted_results:
            # Get memory data from whichever result set has it
            memory_data = score_data.get("memory_data")
            if memory_data:
                results.append(SearchResult(
                    memory_id=memory_id,
                    content=memory_data.content,
                    title=memory_data.title,
                    memory_type=memory_data.memory_type,
                    tags=memory_data.tags,
                    score=score_data["score"],
                    score_breakdown={
                        "vector": score_data.get("vector_score", 0),
                        "fulltext": score_data.get("fulltext_score", 0),
                        "rrf": score_data["score"]
                    },
                    created_at=memory_data.created_at
                ))

        return results

    def _reciprocal_rank_fusion(
        self,
        vector_results: List[SearchResult],
        fulltext_results: List[SearchResult],
        k: int = 60
    ) -> dict:
        """
        Reciprocal Rank Fusion algorithm.

        RRF(d) = sum(1 / (k + rank_i(d))) for each ranking i
        """
        scores = {}

        # Process vector results
        for rank, result in enumerate(vector_results, 1):
            if result.memory_id not in scores:
                scores[result.memory_id] = {
                    "score": 0,
                    "vector_score": result.score,
                    "memory_data": result
                }
            scores[result.memory_id]["score"] += self.config.vector_weight / (k + rank)
            scores[result.memory_id]["vector_score"] = result.score

        # Process fulltext results
        for rank, result in enumerate(fulltext_results, 1):
            if result.memory_id not in scores:
                scores[result.memory_id] = {
                    "score": 0,
                    "fulltext_score": result.score,
                    "memory_data": result
                }
            scores[result.memory_id]["score"] += self.config.fulltext_weight / (k + rank)
            scores[result.memory_id]["fulltext_score"] = result.score

        return scores
```

---

## API Endpoints

```yaml
# Semantic Search
GET /api/v1/memories/search
  Query:
    q: string (required) - Natural language query
    limit: int (default: 10, max: 50)
    threshold: float (default: 0.7) - Minimum similarity
    mode: string (default: "hybrid") - vector, fulltext, hybrid
    memory_type: string (filter)
    tags: string[] (filter)
    include_score: bool (default: true)
    bypass_cache: bool (default: false)
  Response:
    results: [
      {
        memory: Memory,
        score: float,  # 0.0 - 1.0 similarity
        score_breakdown: {
          vector: float,
          fulltext: float,
          rrf: float  # hybrid only
        },
        highlights: string[]  # Matching snippets
      }
    ]
    cached: bool
    search_time_ms: int

# Find Similar Memories
GET /api/v1/memories/{id}/similar
  Query:
    limit: int (default: 5)
    threshold: float (default: 0.7)
  Response:
    results: Memory[] with scores

# Reindex Memory (admin/manual)
POST /api/v1/memories/{id}/reindex
  Response: { status: "queued", embedding_status: string }

# Check Embedding Status
GET /api/v1/memories/{id}/embedding-status
  Response: {
    status: "pending" | "processing" | "completed" | "failed",
    model: string,
    updated_at: timestamp
  }

# Bulk Search (for AI context building)
POST /api/v1/memories/search/bulk
  Request:
    queries: string[] (max 10)
    limit_per_query: int
    mode: string (default: "hybrid")
  Response:
    results: { query: string, memories: Memory[] }[]

# Cache Management (admin)
DELETE /api/v1/admin/search-cache
  Response: { invalidated: int }

GET /api/v1/admin/search-cache/stats
  Response: { cached_queries: int, memory_used: string, ttl: int }
```

---

## Tasks

### Embedding Service Implementation
- [ ] Create embedding service interface (abstract base)
- [ ] Implement OpenAI embedding provider
- [ ] Implement local model fallback (sentence-transformers)
- [ ] Handle rate limiting and retries
- [ ] Add batch embedding support

### Celery Worker Setup
- [ ] Configure Celery with Redis broker
- [ ] Create `process_pending_embeddings` task
- [ ] Create `embed_single_memory` task
- [ ] Configure Celery Beat schedule for periodic processing
- [ ] Add task monitoring and error handling
- [ ] Implement retry logic with exponential backoff

### Search Service Implementation
- [ ] Implement pure vector similarity search
- [ ] Implement pure full-text search (PostgreSQL FTS)
- [ ] Implement hybrid search with RRF score fusion
- [ ] Add configurable similarity thresholds
- [ ] Add filtering (by type, date, tags)
- [ ] Implement "find similar" feature

### Redis Caching Layer
- [ ] Implement SearchCache class
- [ ] Add cache key generation with query hashing
- [ ] Implement TTL-based expiration
- [ ] Add cache invalidation on memory updates
- [ ] Add cache bypass option for fresh results
- [ ] Implement cache statistics endpoint

### API Integration
- [ ] Create search router with endpoints
- [ ] Add request/response schemas
- [ ] Integrate caching in search endpoints
- [ ] Add embedding status endpoints
- [ ] Implement bulk search endpoint

### Performance Optimization
- [ ] Tune HNSW index parameters (ef_search)
- [ ] Optimize batch sizes for embedding
- [ ] Benchmark search latency (target < 100ms)
- [ ] Monitor Redis memory usage
- [ ] Add query explain for debugging

---

## Acceptance Criteria

1. New memories trigger async embedding via Celery
2. embedding_status transitions: pending -> processing -> completed
3. Vector search returns semantically relevant results
4. Full-text search works for exact keyword matching
5. Hybrid search combines both for best results
6. Search latency < 100ms for 10k memories (cached)
7. Search latency < 500ms for 10k memories (uncached)
8. Cache hit rate > 60% for repeated queries
9. Failed embeddings are retried automatically
10. Cache is invalidated when user modifies memories

---

## Embedding Service Interface

```python
# src/embeddings/service.py
from abc import ABC, abstractmethod
from typing import List, Optional
from openai import AsyncOpenAI
from sentence_transformers import SentenceTransformer
import numpy as np

from src.core.config import EmbeddingConfig


class EmbeddingService(ABC):
    """Abstract base class for embedding services."""

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return the model identifier."""
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Return the embedding dimension."""
        pass

    @abstractmethod
    async def embed(self, text: str) -> List[float]:
        """Generate embedding for single text."""
        pass

    @abstractmethod
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        pass


class OpenAIEmbeddingService(EmbeddingService):
    """OpenAI embedding service implementation."""

    def __init__(
        self,
        api_key: str,
        model: str = "text-embedding-3-small"
    ):
        self.client = AsyncOpenAI(api_key=api_key)
        self._model = model
        self._dimension = 1536  # text-embedding-3-small

    @property
    def model_name(self) -> str:
        return self._model

    @property
    def dimension(self) -> int:
        return self._dimension

    async def embed(self, text: str) -> List[float]:
        response = await self.client.embeddings.create(
            model=self._model,
            input=text
        )
        return response.data[0].embedding

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        response = await self.client.embeddings.create(
            model=self._model,
            input=texts
        )
        return [item.embedding for item in response.data]


class LocalEmbeddingService(EmbeddingService):
    """Local sentence-transformers embedding service."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self._model_name = model_name
        self._model = SentenceTransformer(model_name)
        self._dimension = self._model.get_sentence_embedding_dimension()

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def dimension(self) -> int:
        return self._dimension

    async def embed(self, text: str) -> List[float]:
        embedding = self._model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        embeddings = self._model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()


def get_embedding_service(config: EmbeddingConfig = None) -> EmbeddingService:
    """Factory function to get configured embedding service."""
    config = config or EmbeddingConfig()

    if config.provider == "openai":
        from src.core.config import settings
        return OpenAIEmbeddingService(
            api_key=settings.OPENAI_API_KEY,
            model=config.model_name
        )
    elif config.provider == "local":
        return LocalEmbeddingService(
            model_name=config.local_model_name
        )
    else:
        raise ValueError(f"Unknown embedding provider: {config.provider}")
```

---

## Search Schemas

```python
# src/search/schemas.py
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime
from enum import Enum


class SearchMode(str, Enum):
    VECTOR = "vector"
    FULLTEXT = "fulltext"
    HYBRID = "hybrid"


class SearchRequest(BaseModel):
    """Search request schema."""
    q: str = Field(..., min_length=1, max_length=500)
    limit: int = Field(default=10, ge=1, le=50)
    threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    mode: SearchMode = Field(default=SearchMode.HYBRID)
    memory_type: Optional[str] = None
    tags: Optional[List[str]] = None
    include_score: bool = True
    bypass_cache: bool = False


class SearchResult(BaseModel):
    """Individual search result."""
    memory_id: str
    content: str
    title: Optional[str] = None
    memory_type: str
    tags: List[str] = []
    score: float
    score_breakdown: Dict[str, float] = {}
    created_at: datetime


class SearchResponse(BaseModel):
    """Search response schema."""
    results: List[SearchResult]
    total: int
    cached: bool = False
    search_time_ms: int


class BulkSearchRequest(BaseModel):
    """Bulk search request schema."""
    queries: List[str] = Field(..., min_items=1, max_items=10)
    limit_per_query: int = Field(default=5, ge=1, le=20)
    mode: SearchMode = Field(default=SearchMode.HYBRID)


class BulkSearchResult(BaseModel):
    """Bulk search result for single query."""
    query: str
    results: List[SearchResult]


class BulkSearchResponse(BaseModel):
    """Bulk search response schema."""
    results: List[BulkSearchResult]
    search_time_ms: int


class EmbeddingStatus(BaseModel):
    """Embedding status response."""
    status: str  # pending, processing, completed, failed
    model: Optional[str] = None
    updated_at: Optional[datetime] = None
```

---

## Files to Create

```
src/
  embeddings/
    __init__.py
    service.py           # Embedding service interface & implementations
    worker.py            # Celery tasks for async embedding
    config.py            # Embedding configuration

  search/
    __init__.py
    service.py           # Main search service
    hybrid.py            # Hybrid search implementation
    cache.py             # Redis caching layer
    router.py            # Search API endpoints
    schemas.py           # Search request/response schemas
```

---

## Related Sprints

- **Sprint 01: Database Schema** - Defines memories table with embedding fields
- **Sprint 05: Memory Storage** - Memory CRUD operations
- **Sprint 07: RAG Implementation** - Consumes search results for AI context

---

## Related Requirement Groups

- Group 008: Semantic: Semantic Search
- Group 010: Semantic: Query Processing
- Group 012: Semantic: Machine Learning
